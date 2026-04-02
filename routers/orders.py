from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import select, desc
from sqlmodel.ext.asyncio.session import AsyncSession
from pydantic import BaseModel

from database import get_session
from models.order import Order, OrderStatus
from models.workflow import Workflow
from models.product import Product
from loguru import logger

router = APIRouter(prefix="/api/orders", tags=["订单管理"])


class OrderCreate(BaseModel):
    """创建订单请求模型"""
    company_name: str
    video_count: int
    unit_price: float
    income: Optional[float] = None
    profit: Optional[float] = None
    status: str = OrderStatus.pending.value
    workflow_id: Optional[int] = None


class OrderUpdate(BaseModel):
    """更新订单请求模型"""
    company_name: Optional[str] = None
    progress: Optional[int] = None
    video_count: Optional[int] = None
    unit_price: Optional[float] = None
    income: Optional[float] = None
    profit: Optional[float] = None
    status: Optional[str] = None


class OrderResponse(BaseModel):
    """订单响应模型"""
    id: int
    company_name: str
    progress: int
    video_count: int
    unit_price: float
    income: float
    profit: float
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """订单列表响应模型"""
    items: List[OrderResponse]
    total: int
    page: int
    page_size: int


@router.get("", response_model=OrderListResponse, summary="获取订单列表")
async def get_orders(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    session: AsyncSession = Depends(get_session)
):
    """
    获取订单列表，支持分页，按创建时间倒序排列
    """
    try:
        offset = (page - 1) * page_size
        
        statement = select(Order).order_by(desc(Order.created_at))
        total_statement = select(Order)
        
        orders = (await session.exec(statement.offset(offset).limit(page_size))).all()
        total = len((await session.exec(total_statement)).all())
        
        return OrderListResponse(
            items=[OrderResponse.model_validate(order) for order in orders],
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        logger.error(f"获取订单列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取订单列表失败")


@router.get("/recent", response_model=List[OrderResponse], summary="获取最近订单")
async def get_recent_orders(session: AsyncSession = Depends(get_session)):
    """
    获取最近3条订单，按创建时间倒序排列
    """
    try:
        statement = select(Order).order_by(desc(Order.created_at)).limit(3)
        orders = (await session.exec(statement)).all()
        return [OrderResponse.model_validate(order) for order in orders]
    except Exception as e:
        logger.error(f"获取最近订单失败: {e}")
        raise HTTPException(status_code=500, detail="获取最近订单失败")


@router.post("", response_model=OrderResponse, summary="创建订单")
async def create_order(order_data: OrderCreate, session: AsyncSession = Depends(get_session)):
    """
    创建新订单
    - income 和 profit 如果未提供，会自动计算
    - income = video_count * unit_price
    - 如果提供 workflow_id，会复制工作流模板并关联到订单
    """
    try:
        income = order_data.income
        if income is None:
            income = order_data.video_count * order_data.unit_price
        
        profit = order_data.profit
        if profit is None:
            profit = income * 0.7
        
        order = Order(
            company_name=order_data.company_name,
            video_count=order_data.video_count,
            unit_price=order_data.unit_price,
            income=income,
            profit=profit,
            status=order_data.status
        )
        
        session.add(order)
        await session.commit()
        await session.refresh(order)
        
        if order_data.workflow_id:
            workflow_template = await session.get(Workflow, order_data.workflow_id)
            if workflow_template:
                original_steps = workflow_template.steps if workflow_template.steps else []
                enhanced_steps = ["准备中"] + original_steps + ["已完成"]
                new_workflow = Workflow(
                    name=f"{workflow_template.name} - {order.company_name}",
                    description=workflow_template.description,
                    order_id=order.id,
                    steps=enhanced_steps
                )
                session.add(new_workflow)
                await session.commit()
                logger.info(f"为订单 {order.id} 创建工作流: {new_workflow.name}")
        
        logger.info(f"创建订单成功: {order.id} - {order.company_name}")
        return OrderResponse.model_validate(order)
    except Exception as e:
        await session.rollback()
        logger.error(f"创建订单失败: {e}")
        raise HTTPException(status_code=500, detail="创建订单失败")


@router.put("/{order_id}", response_model=OrderResponse, summary="更新订单")
async def update_order(order_id: int, order_data: OrderUpdate, session: AsyncSession = Depends(get_session)):
    """
    更新订单信息
    - 自动更新 updated_at 字段
    """
    try:
        order = await session.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
        
        update_data = order_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(order, key, value)
        
        order.updated_at = datetime.utcnow()
        
        session.add(order)
        await session.commit()
        await session.refresh(order)
        
        logger.info(f"更新订单成功: {order.id}")
        return OrderResponse.model_validate(order)
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"更新订单失败: {e}")
        raise HTTPException(status_code=500, detail="更新订单失败")


@router.delete("/{order_id}", summary="删除订单")
async def delete_order(order_id: int, session: AsyncSession = Depends(get_session)):
    """
    删除指定订单及其关联的工作流和产品
    """
    try:
        order = await session.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
        
        product_statement = select(Product).where(Product.order_id == order_id)
        products = (await session.exec(product_statement)).all()
        for product in products:
            await session.delete(product)
            logger.info(f"删除订单 {order_id} 关联的产品: {product.id} - {product.name}")
        
        workflow_statement = select(Workflow).where(Workflow.order_id == order_id)
        workflows = (await session.exec(workflow_statement)).all()
        for workflow in workflows:
            await session.delete(workflow)
            logger.info(f"删除订单 {order_id} 关联的工作流: {workflow.id} - {workflow.name}")
        
        await session.delete(order)
        await session.commit()
        
        logger.info(f"删除订单成功: {order_id}")
        return {"message": "删除成功", "id": order_id}
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"删除订单失败: {e}")
        raise HTTPException(status_code=500, detail="删除订单失败")

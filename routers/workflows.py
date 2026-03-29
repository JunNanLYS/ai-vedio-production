from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel

from database import get_session
from models import Workflow, Order, Product
from loguru import logger

router = APIRouter(prefix="/api", tags=["workflows"])


class WorkflowCreate(BaseModel):
    """创建工作流的请求数据"""
    name: str
    description: str = ""
    steps: List[str]


class WorkflowUpdate(BaseModel):
    """更新工作流的请求数据"""
    name: Optional[str] = None
    description: Optional[str] = None
    steps: Optional[List[str]] = None


class ProductCreate(BaseModel):
    """创建产品的请求数据"""
    name: str


class ProductMove(BaseModel):
    """移动产品的请求数据"""
    direction: str  # "next" 或 "prev"


class StepProducts(BaseModel):
    """步骤及其产品"""
    step_name: str
    step_index: int
    products: List[Product]


class OrderWorkflowResponse(BaseModel):
    """订单工作流响应数据"""
    workflow: Workflow
    steps_with_products: List[StepProducts]


@router.get("/workflows")
def get_workflows(session: Session = Depends(get_session)) -> List[Workflow]:
    """获取全局工作流列表（order_id 为 null 的工作流）"""
    statement = select(Workflow).where(Workflow.order_id == None)
    workflows = session.exec(statement).all()
    logger.info(f"获取全局工作流列表，共 {len(workflows)} 条")
    return workflows


@router.post("/workflows")
def create_workflow(
    workflow_data: WorkflowCreate,
    session: Session = Depends(get_session)
) -> Workflow:
    """创建新的工作流"""
    workflow = Workflow(
        name=workflow_data.name,
        description=workflow_data.description,
        steps=workflow_data.steps,
        order_id=None
    )
    session.add(workflow)
    session.commit()
    session.refresh(workflow)
    logger.info(f"创建工作流成功: {workflow.name}, ID: {workflow.id}")
    return workflow


@router.delete("/workflows/{workflow_id}")
def delete_workflow(
    workflow_id: int,
    session: Session = Depends(get_session)
) -> dict:
    """删除工作流"""
    workflow = session.get(Workflow, workflow_id)
    if not workflow:
        logger.warning(f"工作流不存在: {workflow_id}")
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    session.delete(workflow)
    session.commit()
    logger.info(f"删除工作流成功: {workflow_id}")
    return {"message": "删除成功"}


@router.get("/orders/{order_id}/workflow")
def get_order_workflow(
    order_id: int,
    session: Session = Depends(get_session)
) -> OrderWorkflowResponse:
    """获取订单的工作流，包含每个步骤下的产品列表"""
    order = session.get(Order, order_id)
    if not order:
        logger.warning(f"订单不存在: {order_id}")
        raise HTTPException(status_code=404, detail="订单不存在")
    
    statement = select(Workflow).where(Workflow.order_id == order_id)
    workflow = session.exec(statement).first()
    
    if not workflow:
        logger.warning(f"订单 {order_id} 没有关联的工作流")
        raise HTTPException(status_code=404, detail="该订单没有关联的工作流")
    
    products_statement = select(Product).where(Product.order_id == order_id)
    all_products = session.exec(products_statement).all()
    
    steps_with_products = []
    steps = workflow.steps if workflow.steps else []
    
    for index, step_name in enumerate(steps):
        step_products = [
            product for product in all_products 
            if product.current_step == index
        ]
        steps_with_products.append(StepProducts(
            step_name=step_name,
            step_index=index,
            products=step_products
        ))
    
    logger.info(f"获取订单 {order_id} 的工作流，共 {len(steps_with_products)} 个步骤")
    return OrderWorkflowResponse(
        workflow=workflow,
        steps_with_products=steps_with_products
    )


@router.post("/orders/{order_id}/products")
def add_product_to_order(
    order_id: int,
    product_data: ProductCreate,
    session: Session = Depends(get_session)
) -> Product:
    """添加产品到订单"""
    order = session.get(Order, order_id)
    if not order:
        logger.warning(f"订单不存在: {order_id}")
        raise HTTPException(status_code=404, detail="订单不存在")
    
    product = Product(
        order_id=order_id,
        name=product_data.name
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    logger.info(f"添加产品到订单 {order_id}: {product.name}, ID: {product.id}")
    return product


@router.put("/workflows/{workflow_id}")
def update_workflow(
    workflow_id: int,
    workflow_data: WorkflowUpdate,
    session: Session = Depends(get_session)
) -> Workflow:
    """更新工作流"""
    workflow = session.get(Workflow, workflow_id)
    if not workflow:
        logger.warning(f"工作流不存在: {workflow_id}")
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    if workflow_data.name is not None:
        workflow.name = workflow_data.name
    if workflow_data.description is not None:
        workflow.description = workflow_data.description
    if workflow_data.steps is not None:
        workflow.steps = workflow_data.steps
    
    session.add(workflow)
    session.commit()
    session.refresh(workflow)
    logger.info(f"更新工作流成功: {workflow.name}, ID: {workflow.id}")
    return workflow


@router.post("/products/{product_id}/move")
def move_product(
    product_id: int,
    move_data: ProductMove,
    session: Session = Depends(get_session)
) -> Product:
    """移动产品到上一步或下一步"""
    product = session.get(Product, product_id)
    if not product:
        logger.warning(f"产品不存在: {product_id}")
        raise HTTPException(status_code=404, detail="产品不存在")
    
    workflow_statement = select(Workflow).where(Workflow.order_id == product.order_id)
    workflow = session.exec(workflow_statement).first()
    
    if not workflow:
        logger.warning(f"产品 {product_id} 所在订单没有工作流")
        raise HTTPException(status_code=400, detail="该产品所在订单没有工作流")
    
    steps = workflow.steps if workflow.steps else []
    max_step = len(steps) - 1
    
    if move_data.direction == "next":
        if product.current_step >= max_step:
            logger.warning(f"产品 {product_id} 已在最后一步，无法前进")
            raise HTTPException(status_code=400, detail="产品已在最后一步")
        product.current_step += 1
        if product.current_step == max_step:
            product.status = "completed"
        else:
            product.status = "in_progress"
    elif move_data.direction == "prev":
        if product.current_step <= 0:
            logger.warning(f"产品 {product_id} 已在第一步，无法后退")
            raise HTTPException(status_code=400, detail="产品已在第一步")
        product.current_step -= 1
        product.status = "in_progress"
    else:
        logger.warning(f"无效的移动方向: {move_data.direction}")
        raise HTTPException(status_code=400, detail="无效的移动方向，必须是 'next' 或 'prev'")
    
    session.add(product)
    session.commit()
    session.refresh(product)
    logger.info(f"移动产品 {product_id} 到步骤 {product.current_step}")
    return product


@router.post("/orders/{order_id}/apply-workflow/{workflow_id}")
def apply_workflow_to_order(
    order_id: int,
    workflow_id: int,
    session: Session = Depends(get_session)
) -> Workflow:
    """将工作流模板应用到订单"""
    order = session.get(Order, order_id)
    if not order:
        logger.warning(f"订单不存在: {order_id}")
        raise HTTPException(status_code=404, detail="订单不存在")
    
    template = session.get(Workflow, workflow_id)
    if not template:
        logger.warning(f"工作流模板不存在: {workflow_id}")
        raise HTTPException(status_code=404, detail="工作流模板不存在")
    
    existing_statement = select(Workflow).where(Workflow.order_id == order_id)
    existing = session.exec(existing_statement).first()
    if existing:
        logger.warning(f"订单 {order_id} 已有工作流")
        raise HTTPException(status_code=400, detail="该订单已有工作流")
    
    original_steps = template.steps.copy() if template.steps else []
    enhanced_steps = ["准备中"] + original_steps + ["已完成"]
    
    new_workflow = Workflow(
        name=template.name,
        description=template.description,
        steps=enhanced_steps,
        order_id=order_id
    )
    session.add(new_workflow)
    session.commit()
    session.refresh(new_workflow)
    logger.info(f"应用工作流模板 {workflow_id} 到订单 {order_id}")
    return new_workflow

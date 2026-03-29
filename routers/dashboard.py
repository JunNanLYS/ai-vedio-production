from datetime import datetime
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func
from pydantic import BaseModel

from database import get_session
from models.order import Order, OrderStatus
from loguru import logger

router = APIRouter(prefix="/api/dashboard", tags=["仪表盘"])


class DashboardStats(BaseModel):
    """仪表盘统计数据响应模型"""
    monthly_income: float
    monthly_profit: float
    total_orders: int
    completed_orders: int


@router.get("/stats", response_model=DashboardStats, summary="获取统计数据")
def get_dashboard_stats(session: Session = Depends(get_session)):
    """
    获取仪表盘统计数据
    - monthly_income: 本月所有订单的收入总和
    - monthly_profit: 本月所有订单的利润总和
    - total_orders: 本月订单总数
    - completed_orders: 本月已完成订单数
    """
    try:
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)
        
        statement = select(Order).where(Order.created_at >= month_start)
        orders = session.exec(statement).all()
        
        monthly_income = sum(order.income for order in orders)
        monthly_profit = sum(order.profit for order in orders)
        total_orders = len(orders)
        completed_orders = sum(1 for order in orders if order.status == OrderStatus.completed.value)
        
        return DashboardStats(
            monthly_income=monthly_income,
            monthly_profit=monthly_profit,
            total_orders=total_orders,
            completed_orders=completed_orders
        )
    except Exception as e:
        logger.error(f"获取仪表盘统计数据失败: {e}")
        raise HTTPException(status_code=500, detail="获取统计数据失败")

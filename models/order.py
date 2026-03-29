from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel
from enum import Enum


class OrderStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    company_name: str = Field(description="公司名")
    progress: int = Field(default=0, ge=0, le=100, description="完成进度，0-100")
    video_count: int = Field(default=0, ge=0, description="视频数量")
    unit_price: float = Field(default=0.0, ge=0, description="单价")
    income: float = Field(default=0.0, ge=0, description="收入")
    profit: float = Field(default=0.0, description="利润")
    status: str = Field(default=OrderStatus.pending.value, description="状态")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")

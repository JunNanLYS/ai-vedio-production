from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="order.id", description="关联订单ID")
    name: str = Field(description="产品名称")
    current_step: int = Field(default=0, ge=0, description="当前所处工作流步骤索引")
    status: str = Field(default="pending", description="状态")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")

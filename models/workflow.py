from datetime import datetime
from typing import Optional, Any
from sqlmodel import Field, SQLModel, Column, JSON


class Workflow(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(description="工作流名称")
    description: str = Field(default="", description="描述")
    order_id: Optional[int] = Field(default=None, foreign_key="order.id", description="关联订单ID，可为空表示全局工作流")
    steps: Any = Field(default=[], sa_column=Column(JSON), description="工作流步骤列表")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")

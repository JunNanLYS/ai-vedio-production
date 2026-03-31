from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class ApiConfig(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    config_key: str = Field(unique=True, description="配置键名")
    config_value: str = Field(description="配置值")
    description: Optional[str] = Field(default=None, description="配置描述")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")

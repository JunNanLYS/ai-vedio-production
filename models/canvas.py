from datetime import datetime
from typing import Optional, Any
from sqlmodel import Field, SQLModel, Column, JSON


class CanvasAsset(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(description="画布名称")
    nodes: Any = Field(default=[], sa_column=Column(JSON), description="节点数据")
    connections: Any = Field(default=[], sa_column=Column(JSON), description="连接数据")
    viewport: Any = Field(default={"x": 0, "y": 0, "scale": 1}, sa_column=Column(JSON), description="视口状态")
    project_id: Optional[int] = Field(default=None, foreign_key="project.id", description="所属项目ID")
    asset_id: Optional[int] = Field(default=None, foreign_key="asset.id", description="关联资产ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")

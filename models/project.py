from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class Project(SQLModel, table=True):
    """资产项目"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(description="项目名称")
    path: str = Field(description="项目路径")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")


class SubCategory(SQLModel, table=True):
    """资产子分类"""
    id: Optional[int] = Field(default=None, primary_key=True)
    category: str = Field(description="所属大类: prompt/image/audio/video")
    name: str = Field(description="子分类名称")
    project_id: Optional[int] = Field(default=None, description="所属项目ID，None表示全局")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")

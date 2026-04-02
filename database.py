from sqlmodel import SQLModel, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from typing import AsyncGenerator
from loguru import logger
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./ai_video_production.db")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def migrate_database():
    """执行数据库迁移"""
    async with async_session_factory() as session:
        try:
            result = await session.exec(text("PRAGMA table_info(asset)"))
            columns = [row[1] for row in result.fetchall()]
            
            if "project_id" not in columns:
                logger.info("正在添加 asset.project_id 列...")
                await session.exec(text("ALTER TABLE asset ADD COLUMN project_id INTEGER"))
                await session.commit()
                logger.info("asset.project_id 列添加成功")
        except Exception as e:
            logger.warning(f"迁移检查失败: {e}")
        
        try:
            result = await session.exec(text("SELECT name FROM sqlite_master WHERE type='table' AND name='project'"))
            if not result.fetchone():
                logger.info("正在创建 project 表...")
                await session.exec(text("""
                    CREATE TABLE project (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        path TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                await session.commit()
                logger.info("project 表创建成功")
        except Exception as e:
            logger.warning(f"创建 project 表失败: {e}")
        
        try:
            result = await session.exec(text("SELECT name FROM sqlite_master WHERE type='table' AND name='subcategory'"))
            if not result.fetchone():
                logger.info("正在创建 subcategory 表...")
                await session.exec(text("""
                    CREATE TABLE subcategory (
                        id INTEGER PRIMARY KEY,
                        category TEXT NOT NULL,
                        name TEXT NOT NULL,
                        project_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                await session.commit()
                logger.info("subcategory 表创建成功")
        except Exception as e:
            logger.warning(f"创建 subcategory 表失败: {e}")


async def create_db_and_tables():
    """创建数据库和所有表"""    
    await migrate_database()
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    logger.info("数据库表创建完成")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话的依赖函数"""
    async with async_session_factory() as session:
        yield session


async def init_db():
    """初始化数据库"""
    await create_db_and_tables()
    logger.info("数据库初始化完成")

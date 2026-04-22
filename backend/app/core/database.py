from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import get_settings

settings = get_settings()

# 创建异步引擎 (SQLite)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# 声明基类
Base = declarative_base()


async def get_db() -> AsyncSession:
    """获取数据库会话（依赖注入用）"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

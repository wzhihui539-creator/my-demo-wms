"""数据库初始化脚本"""
import asyncio
from app.core.database import engine, Base
from app.models import Warehouse, Zone, Location, SKU, Inventory, Lot, User
from app.models.inbound import InboundOrder, InboundItem, ReceiveRecord, PutawayTask


async def init_db():
    """创建所有数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 数据库表创建完成")


if __name__ == "__main__":
    asyncio.run(init_db())

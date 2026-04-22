import sys
import os
sys.path.insert(0, '/root/.openclaw/workspace/wms/backend')
os.chdir('/root/.openclaw/workspace/wms/backend')

from app.core.database import engine
from app.models import User
from sqlalchemy import select
import asyncio
from app.core.security import get_password_hash

async def init_user():
    async with engine.begin() as conn:
        # 检查是否已有用户
        result = await conn.execute(select(User).where(User.username == "admin"))
        user = result.scalar_one_or_none()
        
        if not user:
            # 创建默认管理员
            from uuid import uuid4
            await conn.execute(
                User.__table__.insert(),
                {
                    "id": uuid4(),
                    "username": "admin",
                    "password_hash": get_password_hash("123456"),
                    "real_name": "管理员",
                    "role": "admin",
                    "is_active": True
                }
            )
            print("创建默认用户: admin / 123456")
        else:
            # 更新密码
            await conn.execute(
                User.__table__.update()
                .where(User.username == "admin")
                .values(password_hash=get_password_hash("123456"))
            )
            print("更新用户密码: admin / 123456")

if __name__ == "__main__":
    asyncio.run(init_user())
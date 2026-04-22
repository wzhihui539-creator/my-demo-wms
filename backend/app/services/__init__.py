from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import joinedload
from typing import List, Optional
from uuid import UUID

from app.models import Warehouse, Zone, Location, SKU, Inventory, User
from app.schemas import (
    WarehouseCreate, WarehouseUpdate,
    ZoneCreate, LocationCreate,
    SKUCreate, SKUUpdate,
    UserCreate, InventoryAdjustRequest
)


class WarehouseService:
    """仓库服务"""
    
    @staticmethod
    async def create(db: AsyncSession, data: WarehouseCreate) -> Warehouse:
        warehouse = Warehouse(**data.model_dump())
        db.add(warehouse)
        await db.commit()
        await db.refresh(warehouse)
        return warehouse
    
    @staticmethod
    async def get_by_id(db: AsyncSession, warehouse_id: UUID) -> Optional[Warehouse]:
        result = await db.execute(
            select(Warehouse).where(Warehouse.id == warehouse_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_list(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Warehouse]:
        result = await db.execute(
            select(Warehouse).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def update(db: AsyncSession, warehouse_id: UUID, data: WarehouseUpdate) -> Optional[Warehouse]:
        warehouse = await WarehouseService.get_by_id(db, warehouse_id)
        if not warehouse:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(warehouse, field, value)
        
        await db.commit()
        await db.refresh(warehouse)
        return warehouse


class ZoneService:
    """库区服务"""
    
    @staticmethod
    async def create(db: AsyncSession, data: ZoneCreate) -> Zone:
        zone = Zone(**data.model_dump())
        db.add(zone)
        await db.commit()
        await db.refresh(zone)
        return zone
    
    @staticmethod
    async def get_by_warehouse(db: AsyncSession, warehouse_id: UUID) -> List[Zone]:
        result = await db.execute(
            select(Zone).where(Zone.warehouse_id == warehouse_id)
        )
        return result.scalars().all()


class LocationService:
    """库位服务"""
    
    @staticmethod
    async def create(db: AsyncSession, data: LocationCreate) -> Location:
        location = Location(**data.model_dump())
        db.add(location)
        await db.commit()
        await db.refresh(location)
        return location
    
    @staticmethod
    async def get_by_zone(db: AsyncSession, zone_id: UUID) -> List[Location]:
        result = await db.execute(
            select(Location).where(Location.zone_id == zone_id)
        )
        return result.scalars().all()


class SKUService:
    """商品服务"""
    
    @staticmethod
    async def create(db: AsyncSession, data: SKUCreate) -> SKU:
        sku = SKU(**data.model_dump())
        db.add(sku)
        await db.commit()
        await db.refresh(sku)
        return sku
    
    @staticmethod
    async def get_by_id(db: AsyncSession, sku_id: UUID) -> Optional[SKU]:
        result = await db.execute(
            select(SKU).where(SKU.id == sku_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_list(db: AsyncSession, skip: int = 0, limit: int = 100, 
                       category: Optional[str] = None) -> List[SKU]:
        query = select(SKU)
        if category:
            query = query.where(SKU.category == category)
        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()
    
    @staticmethod
    async def update(db: AsyncSession, sku_id: UUID, data: SKUUpdate) -> Optional[SKU]:
        sku = await SKUService.get_by_id(db, sku_id)
        if not sku:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(sku, field, value)
        
        await db.commit()
        await db.refresh(sku)
        return sku


class InventoryService:
    """库存服务"""
    
    @staticmethod
    async def get_all(db: AsyncSession) -> List[Inventory]:
        result = await db.execute(
            select(Inventory)
            .options(joinedload(Inventory.sku), joinedload(Inventory.location))
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_by_location(db: AsyncSession, location_id: UUID) -> List[Inventory]:
        result = await db.execute(
            select(Inventory)
            .options(joinedload(Inventory.sku), joinedload(Inventory.location))
            .where(Inventory.location_id == location_id)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_by_sku(db: AsyncSession, sku_id: UUID) -> List[Inventory]:
        result = await db.execute(
            select(Inventory)
            .options(joinedload(Inventory.sku), joinedload(Inventory.location))
            .where(Inventory.sku_id == sku_id)
        )
        return result.scalars().all()

    @staticmethod
    async def adjust(db: AsyncSession, inventory_id: UUID, data: InventoryAdjustRequest) -> Optional[Inventory]:
        inventory = await db.get(Inventory, inventory_id)
        if not inventory:
            return None

        if data.available_qty + data.locked_qty > data.quantity:
            raise ValueError("可用数量与锁定数量之和不能大于总数量")

        inventory.quantity = data.quantity
        inventory.available_qty = data.available_qty
        inventory.locked_qty = data.locked_qty

        if data.status:
            inventory.status = data.status
        elif data.quantity == 0:
            inventory.status = "empty"
        elif data.locked_qty > 0 and data.available_qty == 0:
            inventory.status = "locked"
        else:
            inventory.status = "normal"

        await db.commit()
        await db.refresh(inventory)
        return inventory


from app.services.outbound import OutboundService

__all__ = [
    "WarehouseService", "ZoneService", "LocationService", 
    "SKUService", "InventoryService", "UserService",
    "InboundService", "OutboundService"
]


class UserService:
    """用户服务"""
    
    @staticmethod
    async def create(db: AsyncSession, data: UserCreate) -> User:
        from app.core.security import get_password_hash
        
        user = User(
            username=data.username,
            password_hash=get_password_hash(data.password),
            real_name=data.real_name,
            phone=data.phone,
            email=data.email,
            role=data.role
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> Optional[User]:
        result = await db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()


from app.services.alert import AlertService
from app.services.check import CheckService
from app.services.outbound import OutboundService
from app.services.inbound import InboundService

from app.services.report import ReportService
from app.services.alert import AlertService
from app.services.check import CheckService
from app.services.outbound import OutboundService
from app.services.inbound import InboundService

__all__ = [
    "WarehouseService", "ZoneService", "LocationService", 
    "SKUService", "InventoryService", "UserService",
    "InboundService", "OutboundService", "CheckService", 
    "AlertService", "ReportService"
]

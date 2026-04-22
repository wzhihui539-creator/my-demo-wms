from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.orm import joinedload, selectinload
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.models import CheckOrder, CheckItem, Inventory, SKU, Location
from app.schemas import (
    CheckOrderCreate, CheckOrderUpdate,
    CheckItemCount, CheckItemAdjust
)


class CheckService:
    """盘点服务"""
    
    @staticmethod
    def _generate_order_no() -> str:
        """生成盘点单号: CK + 年月日 + 时分秒"""
        return f"CK{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    @staticmethod
    async def create_order(db: AsyncSession, data: CheckOrderCreate, created_by: str = None) -> CheckOrder:
        """创建盘点单"""
        # 创建盘点单
        order = CheckOrder(
            order_no=CheckService._generate_order_no(),
            check_type=data.check_type,
            warehouse_id=data.warehouse_id,
            zone_id=data.zone_id,
            status="pending",
            remark=data.remark,
            created_by=created_by
        )
        db.add(order)
        await db.flush()
        
        # 如果提供了盘点明细，直接创建
        if data.items:
            for item_data in data.items:
                # 查询 SKU 和库位信息用于冗余存储
                sku_result = await db.execute(select(SKU).where(SKU.id == item_data.sku_id))
                sku = sku_result.scalar_one_or_none()
                
                loc_result = await db.execute(select(Location).where(Location.id == item_data.location_id))
                loc = loc_result.scalar_one_or_none()
                
                item = CheckItem(
                    check_order_id=order.id,
                    sku_id=item_data.sku_id,
                    sku_code=sku.code if sku else None,
                    sku_name=sku.name if sku else None,
                    location_id=item_data.location_id,
                    location_code=loc.code if loc else None,
                    lot_id=item_data.lot_id,
                    book_qty=item_data.book_qty,
                    status="pending"
                )
                db.add(item)
            
            order.total_items = len(data.items)
        else:
            # 自动生成盘点明细（全盘或抽盘）
            await CheckService._generate_check_items(db, order)
        
        await db.commit()
        await db.refresh(order)
        return order
    
    @staticmethod
    async def _generate_check_items(db: AsyncSession, order: CheckOrder):
        """自动生成盘点明细"""
        from app.models import Zone, Location
        
        # 查询库存记录
        query = select(Inventory).where(Inventory.quantity > 0)
        
        if order.zone_id:
            # 如果指定了库区，查询该库区下的库位
            loc_result = await db.execute(
                select(Location.id).where(Location.zone_id == order.zone_id)
            )
            location_ids = [row[0] for row in loc_result.all()]
            if location_ids:
                query = query.where(Inventory.location_id.in_(location_ids))
        
        result = await db.execute(query)
        inventories = result.scalars().all()
        
        for inv in inventories:
            sku_result = await db.execute(select(SKU).where(SKU.id == inv.sku_id))
            sku = sku_result.scalar_one_or_none()
            
            loc_result = await db.execute(select(Location).where(Location.id == inv.location_id))
            loc = loc_result.scalar_one_or_none()
            
            item = CheckItem(
                check_order_id=order.id,
                sku_id=inv.sku_id,
                sku_code=sku.code if sku else None,
                sku_name=sku.name if sku else None,
                location_id=inv.location_id,
                location_code=loc.code if loc else None,
                lot_id=inv.lot_id,
                book_qty=inv.quantity,
                status="pending"
            )
            db.add(item)
        
        order.total_items = len(inventories)
    
    @staticmethod
    async def get_order_by_id(db: AsyncSession, order_id: UUID) -> Optional[CheckOrder]:
        """获取盘点单详情（含明细）"""
        result = await db.execute(
            select(CheckOrder)
            .options(selectinload(CheckOrder.items))
            .where(CheckOrder.id == order_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_orders(
        db: AsyncSession,
        warehouse_id: Optional[UUID] = None,
        check_type: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[CheckOrder]:
        """获取盘点单列表"""
        query = select(CheckOrder).options(selectinload(CheckOrder.items))
        
        if warehouse_id:
            query = query.where(CheckOrder.warehouse_id == warehouse_id)
        if check_type:
            query = query.where(CheckOrder.check_type == check_type)
        if status:
            query = query.where(CheckOrder.status == status)
        
        query = query.order_by(CheckOrder.created_at.desc())
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def start_check(db: AsyncSession, order_id: UUID) -> Optional[CheckOrder]:
        """开始盘点"""
        order = await CheckService.get_order_by_id(db, order_id)
        if not order or order.status != "pending":
            return None
        
        order.status = "counting"
        order.started_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(order)
        return order
    
    @staticmethod
    async def count_item(db: AsyncSession, item_id: UUID, data: CheckItemCount) -> Optional[CheckItem]:
        """盘点计数"""
        result = await db.execute(select(CheckItem).where(CheckItem.id == item_id))
        item = result.scalar_one_or_none()
        if not item or item.status not in ["pending", "counting"]:
            return None
        
        item.actual_qty = data.actual_qty
        item.diff_qty = data.actual_qty - item.book_qty
        item.status = "counted"
        item.checker = data.checker
        item.counted_at = datetime.utcnow()
        item.remark = data.remark
        
        await db.commit()
        await db.refresh(item)
        
        # 更新盘点单统计
        await CheckService._update_order_stats(db, item.check_order_id)
        
        return item
    
    @staticmethod
    async def adjust_item(db: AsyncSession, item_id: UUID, data: CheckItemAdjust) -> Optional[CheckItem]:
        """调整盘点差异"""
        result = await db.execute(select(CheckItem).where(CheckItem.id == item_id))
        item = result.scalar_one_or_none()
        if not item or item.status != "counted":
            return None
        
        item.adjusted_qty = data.adjusted_qty
        item.adjust_reason = data.adjust_reason
        item.adjusted_by = data.adjusted_by
        item.adjusted_at = datetime.utcnow()
        item.status = "adjusted"
        
        # 更新库存
        inv_result = await db.execute(
            select(Inventory).where(
                and_(
                    Inventory.sku_id == item.sku_id,
                    Inventory.location_id == item.location_id
                )
            )
        )
        inventory = inv_result.scalar_one_or_none()
        if inventory:
            diff = data.adjusted_qty - inventory.quantity
            inventory.quantity = data.adjusted_qty
            inventory.available_qty += diff
            if inventory.quantity == 0:
                inventory.status = "empty"
        
        await db.commit()
        await db.refresh(item)
        return item
    
    @staticmethod
    async def complete_check(db: AsyncSession, order_id: UUID) -> Optional[CheckOrder]:
        """完成盘点"""
        order = await CheckService.get_order_by_id(db, order_id)
        if not order or order.status != "counting":
            return None
        
        order.status = "completed"
        order.completed_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(order)
        return order
    
    @staticmethod
    async def _update_order_stats(db: AsyncSession, order_id: UUID):
        """更新盘点单统计"""
        result = await db.execute(
            select(CheckItem).where(CheckItem.check_order_id == order_id)
        )
        items = result.scalars().all()
        
        order_result = await db.execute(
            select(CheckOrder).where(CheckOrder.id == order_id)
        )
        order = order_result.scalar_one()
        
        order.matched_items = sum(1 for item in items if item.diff_qty == 0 and item.status == "counted")
        order.diff_items = sum(1 for item in items if item.diff_qty != 0 and item.status == "counted")
        
        await db.commit()

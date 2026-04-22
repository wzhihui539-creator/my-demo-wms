from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.orm import joinedload, selectinload
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.models import (
    OutboundOrder, OutboundItem, PickTask, Wave, ShipRecord,
    Inventory, SKU, Location
)
from app.schemas import (
    OutboundOrderCreate, OutboundOrderUpdate,
    PickRequest, ShipRequest, StartPickRequest
)


class OutboundService:
    """出库服务"""
    
    @staticmethod
    def _generate_order_no() -> str:
        """生成出库单号: OUT + 年月日 + 时分秒"""
        return f"OUT{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    @staticmethod
    async def create_order(db: AsyncSession, data: OutboundOrderCreate, created_by: str = None) -> OutboundOrder:
        """创建出库单"""
        # 计算总数量
        total_qty = sum(item.expected_qty for item in data.items)
        
        # 创建出库单
        order = OutboundOrder(
            order_no=OutboundService._generate_order_no(),
            order_type=data.order_type,
            warehouse_id=data.warehouse_id,
            customer_id=data.customer_id,
            related_order_no=data.related_order_no,
            status="pending",
            total_qty=total_qty,
            expected_date=data.expected_date,
            priority=data.priority,
            remark=data.remark,
            created_by=created_by
        )
        db.add(order)
        await db.flush()
        
        # 创建出库明细
        for item_data in data.items:
            # 查询 SKU 信息用于冗余存储
            sku_result = await db.execute(select(SKU).where(SKU.id == item_data.sku_id))
            sku = sku_result.scalar_one_or_none()
            
            item = OutboundItem(
                order_id=order.id,
                sku_id=item_data.sku_id,
                sku_code=sku.code if sku else None,
                sku_name=sku.name if sku else None,
                lot_id=item_data.lot_id,
                expected_qty=item_data.expected_qty,
                status="pending"
            )
            db.add(item)
        
        await db.commit()
        await db.refresh(order)
        return order
    
    @staticmethod
    async def get_order_by_id(db: AsyncSession, order_id: UUID) -> Optional[OutboundOrder]:
        """获取出库单详情（含明细）"""
        result = await db.execute(
            select(OutboundOrder)
            .options(selectinload(OutboundOrder.items))
            .where(OutboundOrder.id == order_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_orders(
        db: AsyncSession,
        warehouse_id: Optional[UUID] = None,
        order_type: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[OutboundOrder]:
        """获取出库单列表"""
        query = select(OutboundOrder).options(selectinload(OutboundOrder.items))
        
        if warehouse_id:
            query = query.where(OutboundOrder.warehouse_id == warehouse_id)
        if order_type:
            query = query.where(OutboundOrder.order_type == order_type)
        if status:
            query = query.where(OutboundOrder.status == status)
        
        query = query.order_by(OutboundOrder.created_at.desc())
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def pick(db: AsyncSession, order_id: UUID, data: PickRequest) -> PickTask:
        """拣货操作 - 扣减库存"""
        # 获取出库明细
        item_result = await db.execute(
            select(OutboundItem).where(OutboundItem.id == data.outbound_item_id)
        )
        item = item_result.scalar_one_or_none()
        if not item or item.order_id != order_id:
            raise ValueError("出库明细不存在")

        remain_qty = item.expected_qty - item.picked_qty
        if data.quantity > remain_qty:
            raise ValueError(f"拣货数量不能超过待拣数量，待拣数量: {remain_qty}")
        
        # 检查库存是否足够
        inv_result = await db.execute(
            select(Inventory).where(
                and_(
                    Inventory.sku_id == item.sku_id,
                    Inventory.location_id == data.from_location_id,
                    Inventory.available_qty >= data.quantity
                )
            )
        )
        inventory = inv_result.scalar_one_or_none()
        if not inventory:
            raise ValueError("库存不足或库位不存在")
        
        # 生成任务号
        task_no = f"PK{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 创建拣货任务
        task = PickTask(
            task_no=task_no,
            outbound_order_id=order_id,
            outbound_item_id=data.outbound_item_id,
            sku_id=item.sku_id,
            lot_id=data.lot_id,
            quantity=data.quantity,
            picked_qty=data.quantity,
            from_location_id=data.from_location_id,
            status="completed",
            operator=data.operator,
            completed_at=datetime.utcnow()
        )
        db.add(task)
        
        # 扣减库存
        inventory.quantity -= data.quantity
        inventory.available_qty -= data.quantity
        if inventory.quantity == 0:
            inventory.status = "empty"
        
        # 更新出库明细
        item.picked_qty += data.quantity
        if item.picked_qty >= item.expected_qty:
            item.status = "picked"
        else:
            item.status = "picking"
        
        # 更新出库单
        order_result = await db.execute(
            select(OutboundOrder).where(OutboundOrder.id == order_id)
        )
        order = order_result.scalar_one()
        order.picked_qty += data.quantity
        order.picked_date = datetime.utcnow()

        # 检查是否全部拣货完成
        all_items_result = await db.execute(
            select(OutboundItem).where(OutboundItem.order_id == order_id)
        )
        all_items = all_items_result.scalars().all()
        all_picked = all(outbound_item.picked_qty >= outbound_item.expected_qty for outbound_item in all_items)
        order.status = "picked" if all_picked else "picking"
        
        await db.commit()
        await db.refresh(task)
        return task

    @staticmethod
    async def start_pick(db: AsyncSession, order_id: UUID, data: StartPickRequest) -> OutboundOrder:
        """开始拣货：将出库单从 pending 置为 picking"""
        order_result = await db.execute(
            select(OutboundOrder)
            .options(selectinload(OutboundOrder.items))
            .where(OutboundOrder.id == order_id)
        )
        order = order_result.scalar_one_or_none()
        if not order:
            raise ValueError("出库单不存在")

        if order.status != "pending":
            raise ValueError("当前状态不可开始拣货")

        order.status = "picking"
        order.picked_date = datetime.utcnow()
        for item in order.items:
            if item.status == "pending":
                item.status = "picking"

        await db.commit()
        await db.refresh(order)
        return order
    
    @staticmethod
    async def ship(db: AsyncSession, order_id: UUID, data: ShipRequest) -> ShipRecord:
        """发货操作"""
        # 获取出库明细
        item_result = await db.execute(
            select(OutboundItem).where(OutboundItem.id == data.outbound_item_id)
        )
        item = item_result.scalar_one_or_none()
        if not item or item.order_id != order_id:
            raise ValueError("出库明细不存在")
        
        # 创建发货记录
        record = ShipRecord(
            outbound_order_id=order_id,
            outbound_item_id=data.outbound_item_id,
            sku_id=item.sku_id,
            lot_id=item.lot_id,
            quantity=data.quantity,
            tracking_no=data.tracking_no,
            carrier=data.carrier,
            operator=data.operator
        )
        db.add(record)
        
        # 更新出库明细
        item.shipped_qty += data.quantity
        if item.shipped_qty >= item.expected_qty:
            item.status = "shipped"
        
        # 更新出库单
        order_result = await db.execute(
            select(OutboundOrder).where(OutboundOrder.id == order_id)
        )
        order = order_result.scalar_one()
        order.shipped_qty += data.quantity
        order.status = "shipped"
        order.shipped_date = datetime.utcnow()
        
        # 检查是否全部发货完成
        items_result = await db.execute(
            select(OutboundItem).where(OutboundItem.order_id == order_id)
        )
        all_items = items_result.scalars().all()
        all_completed = all(
            item.shipped_qty >= item.expected_qty 
            for item in all_items
        )
        if all_completed:
            order.status = "completed"
            order.completed_date = datetime.utcnow()
        
        await db.commit()
        await db.refresh(record)
        return record
    
    @staticmethod
    async def create_wave(db: AsyncSession, warehouse_id: UUID, order_ids: List[UUID]) -> Wave:
        """创建波次"""
        # 生成波次号
        wave_no = f"WV{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        wave = Wave(
            wave_no=wave_no,
            warehouse_id=warehouse_id,
            order_count=len(order_ids)
        )
        db.add(wave)
        await db.commit()
        await db.refresh(wave)
        return wave

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func
from sqlalchemy.orm import joinedload, selectinload
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.models import InboundOrder, InboundItem, ReceiveRecord, PutawayTask, SKU, Inventory, Location
from app.schemas import (
    InboundOrderCreate, InboundOrderUpdate,
    ReceiveRequest, PutawayRequest
)


class InboundService:
    """入库服务"""
    
    @staticmethod
    def _generate_order_no() -> str:
        """生成入库单号: IN + 年月日 + 4位序号"""
        from datetime import datetime
        return f"IN{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    @staticmethod
    async def create_order(db: AsyncSession, data: InboundOrderCreate, created_by: str = None) -> InboundOrder:
        """创建入库单"""
        # 计算总数量
        total_qty = sum(item.expected_qty for item in data.items)
        
        # 创建入库单
        order = InboundOrder(
            order_no=InboundService._generate_order_no(),
            order_type=data.order_type,
            warehouse_id=data.warehouse_id,
            supplier_id=data.supplier_id,
            related_order_no=data.related_order_no,
            status="pending",
            total_qty=total_qty,
            expected_date=data.expected_date,
            remark=data.remark,
            created_by=created_by
        )
        db.add(order)
        await db.flush()  # 获取 order.id
        
        # 创建入库明细
        for item_data in data.items:
            # 查询 SKU 信息用于冗余存储
            sku_result = await db.execute(select(SKU).where(SKU.id == item_data.sku_id))
            sku = sku_result.scalar_one_or_none()
            
            item = InboundItem(
                order_id=order.id,
                sku_id=item_data.sku_id,
                sku_code=sku.code if sku else "",
                sku_name=sku.name if sku else "",
                expected_qty=item_data.expected_qty,
                received_qty=0,
                putaway_qty=0,
                lot_no=item_data.lot_no,
                status="pending"
            )
            db.add(item)
        
        await db.commit()
        await db.refresh(order)
        return order
    
    @staticmethod
    async def get_orders(
        db: AsyncSession,
        warehouse_id: Optional[UUID] = None,
        order_type: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[InboundOrder]:
        """获取入库单列表"""
        query = select(InboundOrder).options(selectinload(InboundOrder.items))
        
        if warehouse_id:
            query = query.where(InboundOrder.warehouse_id == warehouse_id)
        if order_type:
            query = query.where(InboundOrder.order_type == order_type)
        if status:
            query = query.where(InboundOrder.status == status)
        
        query = query.order_by(InboundOrder.created_at.desc())
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_order_by_id(db: AsyncSession, order_id: UUID) -> Optional[InboundOrder]:
        """根据ID获取入库单"""
        result = await db.execute(
            select(InboundOrder)
            .options(selectinload(InboundOrder.items))
            .where(InboundOrder.id == order_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_order(db: AsyncSession, order_id: UUID, data: InboundOrderUpdate) -> Optional[InboundOrder]:
        """更新入库单（仅允许更新 pending 状态）"""
        order = await InboundService.get_order_by_id(db, order_id)
        if not order or order.status != "pending":
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(order, field, value)
        
        await db.commit()
        await db.refresh(order)
        return order
    
    @staticmethod
    async def receive(db: AsyncSession, order_id: UUID, data: ReceiveRequest) -> ReceiveRecord:
        """收货操作"""
        # 获取入库明细
        item_result = await db.execute(
            select(InboundItem).where(InboundItem.id == data.inbound_item_id)
        )
        item = item_result.scalar_one_or_none()
        if not item or item.order_id != order_id:
            raise ValueError("入库明细不存在")
        
        # 校验收货数量不超过预期数量
        if data.quantity > (item.expected_qty - item.received_qty):
            raise ValueError(f"收货数量不能超过待收数量，待收数量: {item.expected_qty - item.received_qty}")
        
        # 创建收货记录
        record = ReceiveRecord(
            inbound_order_id=order_id,
            inbound_item_id=data.inbound_item_id,
            sku_id=item.sku_id,
            lot_no=data.lot_no or item.lot_no,
            quantity=data.quantity,
            location_id=data.location_id,
            quality_status=data.quality_status,
            reject_reason=data.reject_reason,
            operator=data.operator
        )
        db.add(record)
        
        # 更新入库明细
        item.received_qty += data.quantity
        if item.received_qty >= item.expected_qty:
            item.status = "received"
        else:
            item.status = "receiving"
        
        # 更新入库单状态
        order_result = await db.execute(
            select(InboundOrder).where(InboundOrder.id == order_id)
        )
        order = order_result.scalar_one()
        order.received_qty += data.quantity
        order.status = "receiving"
        order.received_date = datetime.utcnow()
        
        await db.commit()
        await db.refresh(record)
        return record

    @staticmethod
    async def complete_receive(db: AsyncSession, order_id: UUID) -> InboundOrder:
        """完成收货 - 将状态从 receiving 改为 received"""
        order = await InboundService.get_order_by_id(db, order_id)
        if not order or order.status != "receiving":
            raise ValueError("入库单不存在或状态不是收货中")
        
        # 检查是否所有明细都已收完
        items_result = await db.execute(
            select(InboundItem).where(InboundItem.order_id == order_id)
        )
        items = items_result.scalars().all()
        
        # 更新所有明细状态为 received
        for item in items:
            item.status = "received"
        
        # 更新订单状态
        order.status = "received"
        
        await db.commit()
        await db.refresh(order)
        return order
    
    @staticmethod
    async def create_putaway_task(db: AsyncSession, order_id: UUID, receive_record_id: UUID, 
                                   to_location_id: UUID, quantity: int, operator: str = None) -> PutawayTask:
        """创建上架任务"""
        # 获取收货记录
        record_result = await db.execute(
            select(ReceiveRecord).where(ReceiveRecord.id == receive_record_id)
        )
        record = record_result.scalar_one_or_none()
        if not record:
            raise ValueError("收货记录不存在")
        if record.inbound_order_id != order_id:
            raise ValueError("收货记录不属于当前入库单")

        # 校验上架数量不超过可上架数量（累计任务）
        used_qty_result = await db.execute(
            select(func.coalesce(func.sum(PutawayTask.quantity), 0)).where(
                and_(
                    PutawayTask.receive_record_id == receive_record_id,
                    PutawayTask.status != "cancelled"
                )
            )
        )
        used_qty = used_qty_result.scalar() or 0
        remain_qty = record.quantity - used_qty
        if quantity > remain_qty:
            raise ValueError(f"上架数量不能超过可上架数量，剩余可上架: {remain_qty}")
        
        # 生成任务号
        task_no = f"PT{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        task = PutawayTask(
            task_no=task_no,
            inbound_order_id=order_id,
            receive_record_id=receive_record_id,
            sku_id=record.sku_id,
            lot_no=record.lot_no,
            from_location_id=record.location_id,
            to_location_id=to_location_id,
            quantity=quantity,
            operator=operator
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task

    @staticmethod
    async def get_receive_records_by_order(db: AsyncSession, order_id: UUID) -> List[dict]:
        """获取入库单收货记录（含可上架数量）"""
        records_result = await db.execute(
            select(ReceiveRecord, InboundItem)
            .join(InboundItem, InboundItem.id == ReceiveRecord.inbound_item_id)
            .where(ReceiveRecord.inbound_order_id == order_id)
            .order_by(ReceiveRecord.created_at.desc())
        )
        rows = records_result.all()

        result = []
        for record, item in rows:
            used_qty_result = await db.execute(
                select(func.coalesce(func.sum(PutawayTask.quantity), 0)).where(
                    and_(
                        PutawayTask.receive_record_id == record.id,
                        PutawayTask.status != "cancelled"
                    )
                )
            )
            used_qty = used_qty_result.scalar() or 0
            remain_qty = max(record.quantity - used_qty, 0)

            result.append({
                "id": str(record.id),
                "inbound_item_id": str(record.inbound_item_id),
                "sku_id": str(record.sku_id),
                "sku_name": item.sku_name,
                "lot_no": record.lot_no,
                "quantity": record.quantity,
                "putaway_qty": used_qty,
                "remain_qty": remain_qty,
                "location_id": str(record.location_id) if record.location_id else None,
                "created_at": record.created_at.isoformat() if record.created_at else None,
            })

        return result
    
    @staticmethod
    async def complete_putaway(db: AsyncSession, task_id: UUID, operator: str = None) -> PutawayTask:
        """完成上架任务"""
        task_result = await db.execute(
            select(PutawayTask).where(PutawayTask.id == task_id)
        )
        task = task_result.scalar_one_or_none()
        if not task or task.status != "pending":
            raise ValueError("上架任务不存在或状态错误")
        
        # 更新任务状态
        task.status = "completed"
        task.operator = operator
        task.completed_at = datetime.utcnow()
        
        # 更新入库明细的上架数量 - 使用独立的查询
        item_result = await db.execute(
            select(InboundItem).where(
                and_(
                    InboundItem.order_id == task.inbound_order_id,
                    InboundItem.sku_id == task.sku_id
                )
            )
        )
        item = item_result.scalar_one_or_none()
        if item:
            item.putaway_qty += task.quantity
            item.location_id = task.to_location_id
            if item.putaway_qty >= item.expected_qty:
                item.status = "completed"
        
        # 更新入库单
        order_result = await db.execute(
            select(InboundOrder).where(InboundOrder.id == task.inbound_order_id)
        )
        order = order_result.scalar_one()
        order.putaway_qty += task.quantity
        
        # 检查是否全部上架完成 - 查询所有明细
        items_result = await db.execute(
            select(InboundItem).where(InboundItem.order_id == task.inbound_order_id)
        )
        all_items = items_result.scalars().all()
        all_completed = all(
            item.putaway_qty >= item.expected_qty 
            for item in all_items
        )
        if all_completed:
            order.status = "completed"
            order.completed_date = datetime.utcnow()
        else:
            order.status = "putaway"
        
        # 更新库存 - 查找或创建库存记录
        inv_result = await db.execute(
            select(Inventory).where(
                and_(
                    Inventory.sku_id == task.sku_id,
                    Inventory.location_id == task.to_location_id,
                    Inventory.lot_id == None  # 简化：不考虑批次库存
                )
            )
        )
        inventory = inv_result.scalar_one_or_none()
        
        if inventory:
            # 更新现有库存
            inventory.quantity += task.quantity
            inventory.available_qty += task.quantity
        else:
            # 创建新库存记录
            inventory = Inventory(
                sku_id=task.sku_id,
                location_id=task.to_location_id,
                quantity=task.quantity,
                available_qty=task.quantity,
                locked_qty=0,
                status="normal"
            )
            db.add(inventory)
        
        await db.commit()
        await db.refresh(task)
        return task

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.orm import joinedload, selectinload
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from app.models import InventoryAlert, AlertRecord, Inventory, SKU, Warehouse, Location
from app.schemas import (
    InventoryAlertCreate, InventoryAlertUpdate,
    AlertRecordResolve, CheckAlertRequest
)


class AlertService:
    """库存预警服务"""
    
    @staticmethod
    async def create_alert(db: AsyncSession, data: InventoryAlertCreate) -> InventoryAlert:
        """创建预警规则"""
        alert = InventoryAlert(**data.model_dump())
        db.add(alert)
        await db.commit()
        await db.refresh(alert)
        return alert
    
    @staticmethod
    async def get_alert_by_id(db: AsyncSession, alert_id: UUID) -> Optional[InventoryAlert]:
        """获取预警规则"""
        result = await db.execute(
            select(InventoryAlert).where(InventoryAlert.id == alert_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_alerts(
        db: AsyncSession,
        alert_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[InventoryAlert]:
        """获取预警规则列表"""
        query = select(InventoryAlert)
        
        if alert_type:
            query = query.where(InventoryAlert.alert_type == alert_type)
        if is_active is not None:
            query = query.where(InventoryAlert.is_active == is_active)
        
        query = query.order_by(InventoryAlert.created_at.desc())
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_alert(db: AsyncSession, alert_id: UUID, data: InventoryAlertUpdate) -> Optional[InventoryAlert]:
        """更新预警规则"""
        alert = await AlertService.get_alert_by_id(db, alert_id)
        if not alert:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(alert, field, value)
        
        alert.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(alert)
        return alert
    
    @staticmethod
    async def delete_alert(db: AsyncSession, alert_id: UUID) -> bool:
        """删除预警规则"""
        alert = await AlertService.get_alert_by_id(db, alert_id)
        if not alert:
            return False
        
        await db.delete(alert)
        await db.commit()
        return True
    
    @staticmethod
    async def check_alerts(db: AsyncSession, request: Optional[CheckAlertRequest] = None) -> List[AlertRecord]:
        """检查库存预警"""
        records = []
        
        # 获取所有启用的预警规则
        query = select(InventoryAlert).where(InventoryAlert.is_active == True)
        result = await db.execute(query)
        alerts = result.scalars().all()
        
        for alert in alerts:
            # 根据预警类型检查
            if alert.alert_type == "low_stock":
                records.extend(await AlertService._check_low_stock(db, alert))
            elif alert.alert_type == "high_stock":
                records.extend(await AlertService._check_high_stock(db, alert))
            elif alert.alert_type == "expired":
                records.extend(await AlertService._check_expired(db, alert))
            elif alert.alert_type == "stagnant":
                records.extend(await AlertService._check_stagnant(db, alert))
        
        # 保存预警记录
        for record in records:
            db.add(record)
        
        await db.commit()
        return records
    
    @staticmethod
    async def _check_low_stock(db: AsyncSession, alert: InventoryAlert) -> List[AlertRecord]:
        """检查低库存预警"""
        records = []
        threshold = alert.threshold_min or 10
        
        # 构建查询条件
        conditions = [Inventory.quantity <= threshold]
        if alert.sku_id:
            conditions.append(Inventory.sku_id == alert.sku_id)
        if alert.location_id:
            conditions.append(Inventory.location_id == alert.location_id)
        
        result = await db.execute(
            select(Inventory, SKU).join(SKU).where(and_(*conditions))
        )
        
        for inv, sku in result.all():
            # 检查是否已存在未处理的相同预警
            existing = await db.execute(
                select(AlertRecord).where(
                    and_(
                        AlertRecord.sku_id == inv.sku_id,
                        AlertRecord.alert_type == "low_stock",
                        AlertRecord.status.in_(["unread", "read"])
                    )
                )
            )
            if existing.scalar_one_or_none():
                continue
            
            record = AlertRecord(
                alert_id=alert.id,
                sku_id=inv.sku_id,
                warehouse_id=alert.warehouse_id,
                location_id=inv.location_id,
                alert_type="low_stock",
                alert_level="warning" if inv.quantity > 0 else "critical",
                title=f"低库存预警: {sku.name}",
                content=f"商品 {sku.name}({sku.code}) 当前库存 {inv.quantity}，低于阈值 {threshold}",
                current_qty=inv.quantity,
                threshold_value=threshold,
                status="unread"
            )
            records.append(record)
            
            # 更新预警规则触发次数
            alert.trigger_count += 1
            alert.last_triggered_at = datetime.utcnow()
        
        return records
    
    @staticmethod
    async def _check_high_stock(db: AsyncSession, alert: InventoryAlert) -> List[AlertRecord]:
        """检查高库存预警"""
        records = []
        threshold = alert.threshold_max or 1000
        
        conditions = [Inventory.quantity >= threshold]
        if alert.sku_id:
            conditions.append(Inventory.sku_id == alert.sku_id)
        if alert.location_id:
            conditions.append(Inventory.location_id == alert.location_id)
        
        result = await db.execute(
            select(Inventory, SKU).join(SKU).where(and_(*conditions))
        )
        
        for inv, sku in result.all():
            existing = await db.execute(
                select(AlertRecord).where(
                    and_(
                        AlertRecord.sku_id == inv.sku_id,
                        AlertRecord.alert_type == "high_stock",
                        AlertRecord.status.in_(["unread", "read"])
                    )
                )
            )
            if existing.scalar_one_or_none():
                continue
            
            record = AlertRecord(
                alert_id=alert.id,
                sku_id=inv.sku_id,
                warehouse_id=alert.warehouse_id,
                location_id=inv.location_id,
                alert_type="high_stock",
                alert_level="warning",
                title=f"高库存预警: {sku.name}",
                content=f"商品 {sku.name}({sku.code}) 当前库存 {inv.quantity}，高于阈值 {threshold}",
                current_qty=inv.quantity,
                threshold_value=threshold,
                status="unread"
            )
            records.append(record)
            alert.trigger_count += 1
            alert.last_triggered_at = datetime.utcnow()
        
        return records
    
    @staticmethod
    async def _check_expired(db: AsyncSession, alert: InventoryAlert) -> List[AlertRecord]:
        """检查临期预警"""
        records = []
        days = alert.days_before_expire or 30
        expire_date = datetime.utcnow() + timedelta(days=days)
        
        # 这里简化处理，实际应该查询批次/lot的过期日期
        # 由于没有lot过期日期字段，这里演示逻辑
        
        return records
    
    @staticmethod
    async def _check_stagnant(db: AsyncSession, alert: InventoryAlert) -> List[AlertRecord]:
        """检查呆滞库存预警"""
        records = []
        days = alert.stagnant_days or 90
        stagnant_date = datetime.utcnow() - timedelta(days=days)
        
        # 查询长时间没有出入库操作的库存
        # 简化处理：查询创建时间较早的库存
        conditions = [Inventory.created_at <= stagnant_date, Inventory.quantity > 0]
        if alert.sku_id:
            conditions.append(Inventory.sku_id == alert.sku_id)
        if alert.location_id:
            conditions.append(Inventory.location_id == alert.location_id)
        
        result = await db.execute(
            select(Inventory, SKU).join(SKU).where(and_(*conditions))
        )
        
        for inv, sku in result.all():
            existing = await db.execute(
                select(AlertRecord).where(
                    and_(
                        AlertRecord.sku_id == inv.sku_id,
                        AlertRecord.alert_type == "stagnant",
                        AlertRecord.status.in_(["unread", "read"])
                    )
                )
            )
            if existing.scalar_one_or_none():
                continue
            
            record = AlertRecord(
                alert_id=alert.id,
                sku_id=inv.sku_id,
                warehouse_id=alert.warehouse_id,
                location_id=inv.location_id,
                alert_type="stagnant",
                alert_level="warning",
                title=f"呆滞库存预警: {sku.name}",
                content=f"商品 {sku.name}({sku.code}) 库存 {inv.quantity} 已呆滞超过 {days} 天",
                current_qty=inv.quantity,
                status="unread"
            )
            records.append(record)
            alert.trigger_count += 1
            alert.last_triggered_at = datetime.utcnow()
        
        return records
    
    @staticmethod
    async def get_alert_records(
        db: AsyncSession,
        status: Optional[str] = None,
        alert_type: Optional[str] = None,
        alert_level: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AlertRecord]:
        """获取预警记录列表"""
        query = select(AlertRecord).order_by(AlertRecord.created_at.desc())
        
        if status:
            query = query.where(AlertRecord.status == status)
        if alert_type:
            query = query.where(AlertRecord.alert_type == alert_type)
        if alert_level:
            query = query.where(AlertRecord.alert_level == alert_level)
        
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_alert_record_by_id(db: AsyncSession, record_id: UUID) -> Optional[AlertRecord]:
        """获取预警记录详情"""
        result = await db.execute(
            select(AlertRecord).where(AlertRecord.id == record_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def resolve_alert_record(
        db: AsyncSession,
        record_id: UUID,
        data: AlertRecordResolve,
        resolved_by: str
    ) -> Optional[AlertRecord]:
        """处理预警记录"""
        record = await AlertService.get_alert_record_by_id(db, record_id)
        if not record or record.status == "resolved":
            return None
        
        record.status = "resolved"
        record.resolved_by = resolved_by
        record.resolved_at = datetime.utcnow()
        record.resolve_note = data.resolve_note
        
        await db.commit()
        await db.refresh(record)
        return record
    
    @staticmethod
    async def read_alert_record(db: AsyncSession, record_id: UUID) -> Optional[AlertRecord]:
        """标记预警记录为已读"""
        record = await AlertService.get_alert_record_by_id(db, record_id)
        if not record or record.status != "unread":
            return None
        
        record.status = "read"
        record.read_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(record)
        return record
    
    @staticmethod
    async def get_alert_stats(db: AsyncSession) -> dict:
        """获取预警统计"""
        # 总预警数
        total_result = await db.execute(select(func.count(AlertRecord.id)))
        total = total_result.scalar()
        
        # 未读数
        unread_result = await db.execute(
            select(func.count(AlertRecord.id)).where(AlertRecord.status == "unread")
        )
        unread = unread_result.scalar()
        
        # 警告级别
        warning_result = await db.execute(
            select(func.count(AlertRecord.id)).where(AlertRecord.alert_level == "warning")
        )
        warning = warning_result.scalar()
        
        critical_result = await db.execute(
            select(func.count(AlertRecord.id)).where(AlertRecord.alert_level == "critical")
        )
        critical = critical_result.scalar()
        
        # 按类型统计
        low_stock_result = await db.execute(
            select(func.count(AlertRecord.id)).where(AlertRecord.alert_type == "low_stock")
        )
        low_stock = low_stock_result.scalar()
        
        high_stock_result = await db.execute(
            select(func.count(AlertRecord.id)).where(AlertRecord.alert_type == "high_stock")
        )
        high_stock = high_stock_result.scalar()
        
        expired_result = await db.execute(
            select(func.count(AlertRecord.id)).where(AlertRecord.alert_type == "expired")
        )
        expired = expired_result.scalar()
        
        stagnant_result = await db.execute(
            select(func.count(AlertRecord.id)).where(AlertRecord.alert_type == "stagnant")
        )
        stagnant = stagnant_result.scalar()
        
        return {
            "total_alerts": total,
            "unread_count": unread,
            "warning_count": warning,
            "critical_count": critical,
            "low_stock_count": low_stock,
            "high_stock_count": high_stock,
            "expired_count": expired,
            "stagnant_count": stagnant
        }

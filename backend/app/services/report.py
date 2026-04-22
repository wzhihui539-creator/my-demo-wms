from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, extract, case
from sqlalchemy.orm import joinedload
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta, date

from app.models import (
    InboundOrder, InboundItem, OutboundOrder, OutboundItem,
    Inventory, SKU, Warehouse, Location, Zone,
    ReceiveRecord, PutawayTask, PickTask, ShipRecord,
    CheckOrder, CheckItem, AlertRecord
)


class ReportService:
    """报表统计服务"""
    
    # ============= 库存报表 =============
    
    @staticmethod
    async def get_inventory_summary(db: AsyncSession, warehouse_id: Optional[UUID] = None) -> Dict[str, Any]:
        """库存汇总报表"""
        # 总库存数量
        query = select(func.sum(Inventory.quantity))
        if warehouse_id:
            # 通过location关联到zone再关联到warehouse
            query = query.join(Location).join(Zone).where(Zone.warehouse_id == warehouse_id)
        
        total_qty_result = await db.execute(query)
        total_qty = total_qty_result.scalar() or 0
        
        # 总SKU种类数
        sku_count_query = select(func.count(func.distinct(Inventory.sku_id)))
        if warehouse_id:
            sku_count_query = sku_count_query.join(Location).join(Zone).where(Zone.warehouse_id == warehouse_id)
        
        sku_count_result = await db.execute(sku_count_query)
        sku_count = sku_count_result.scalar() or 0
        
        # 总库位数
        location_count_query = select(func.count(func.distinct(Inventory.location_id)))
        if warehouse_id:
            location_count_query = location_count_query.join(Location).join(Zone).where(Zone.warehouse_id == warehouse_id)
        
        location_count_result = await db.execute(location_count_query)
        location_count = location_count_result.scalar() or 0
        
        # 空库位数
        empty_locations_query = select(func.count(Location.id)).where(Location.status == "empty")
        if warehouse_id:
            empty_locations_query = empty_locations_query.join(Zone).where(Zone.warehouse_id == warehouse_id)
        
        empty_locations_result = await db.execute(empty_locations_query)
        empty_locations = empty_locations_result.scalar() or 0
        
        return {
            "total_quantity": total_qty,
            "sku_count": sku_count,
            "location_count": location_count,
            "empty_location_count": empty_locations,
            "location_utilization": round((location_count - empty_locations) / location_count * 100, 2) if location_count > 0 else 0
        }
    
    @staticmethod
    async def get_inventory_by_category(db: AsyncSession, warehouse_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """按分类统计库存"""
        query = select(
            SKU.category,
            func.count(func.distinct(Inventory.sku_id)).label("sku_count"),
            func.sum(Inventory.quantity).label("total_qty"),
            func.sum(Inventory.quantity * 100).label("estimated_value")  # 简化估价
        ).join(Inventory).group_by(SKU.category)
        
        if warehouse_id:
            query = query.join(Location).join(Zone).where(Zone.warehouse_id == warehouse_id)
        
        result = await db.execute(query)
        
        return [
            {
                "category": row.category or "未分类",
                "sku_count": row.sku_count,
                "total_quantity": row.total_qty or 0,
                "estimated_value": row.estimated_value or 0
            }
            for row in result.all()
        ]
    
    @staticmethod
    async def get_inventory_by_warehouse(db: AsyncSession) -> List[Dict[str, Any]]:
        """按仓库统计库存"""
        result = await db.execute(
            select(
                Warehouse.id,
                Warehouse.name,
                Warehouse.code,
                func.count(func.distinct(Inventory.sku_id)).label("sku_count"),
                func.sum(Inventory.quantity).label("total_qty")
            )
            .join(Zone, Zone.warehouse_id == Warehouse.id)
            .join(Location, Location.zone_id == Zone.id)
            .join(Inventory, Inventory.location_id == Location.id)
            .group_by(Warehouse.id)
        )
        
        return [
            {
                "warehouse_id": row.id,
                "warehouse_name": row.name,
                "warehouse_code": row.code,
                "sku_count": row.sku_count,
                "total_quantity": row.total_qty or 0
            }
            for row in result.all()
        ]
    
    # ============= 入库报表 =============
    
    @staticmethod
    async def get_inbound_summary(
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        warehouse_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """入库汇总报表"""
        conditions = []
        if start_date:
            conditions.append(InboundOrder.created_at >= start_date)
        if end_date:
            conditions.append(InboundOrder.created_at <= end_date)
        if warehouse_id:
            conditions.append(InboundOrder.warehouse_id == warehouse_id)
        
        # 总入库单数
        order_count_query = select(func.count(InboundOrder.id))
        if conditions:
            order_count_query = order_count_query.where(and_(*conditions))
        
        order_count_result = await db.execute(order_count_query)
        order_count = order_count_result.scalar() or 0
        
        # 总入库数量
        qty_query = select(func.sum(InboundItem.expected_qty)).join(InboundOrder)
        if conditions:
            qty_query = qty_query.where(and_(*conditions))
        
        qty_result = await db.execute(qty_query)
        total_qty = qty_result.scalar() or 0
        
        # 按状态统计
        status_query = select(
            InboundOrder.status,
            func.count(InboundOrder.id).label("count"),
            func.sum(InboundOrder.total_qty).label("qty")
        ).group_by(InboundOrder.status)
        
        if conditions:
            status_query = status_query.where(and_(*conditions))
        
        status_result = await db.execute(status_query)
        status_stats = [
            {"status": row.status, "count": row.count, "quantity": row.qty or 0}
            for row in status_result.all()
        ]
        
        return {
            "order_count": order_count,
            "total_quantity": total_qty,
            "status_stats": status_stats
        }
    
    @staticmethod
    async def get_inbound_daily(
        db: AsyncSession,
        days: int = 30,
        warehouse_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """入库日报表"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = select(
            func.date(InboundOrder.created_at).label("date"),
            func.count(InboundOrder.id).label("order_count"),
            func.sum(InboundOrder.total_qty).label("total_qty")
        ).where(InboundOrder.created_at >= start_date)
        
        if warehouse_id:
            query = query.where(InboundOrder.warehouse_id == warehouse_id)
        
        query = query.group_by(func.date(InboundOrder.created_at)).order_by(func.date(InboundOrder.created_at))
        
        result = await db.execute(query)
        
        return [
            {
                "date": str(row.date),
                "order_count": row.order_count,
                "total_quantity": row.total_qty or 0
            }
            for row in result.all()
        ]
    
    # ============= 出库报表 =============
    
    @staticmethod
    async def get_outbound_summary(
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        warehouse_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """出库汇总报表"""
        conditions = []
        if start_date:
            conditions.append(OutboundOrder.created_at >= start_date)
        if end_date:
            conditions.append(OutboundOrder.created_at <= end_date)
        if warehouse_id:
            conditions.append(OutboundOrder.warehouse_id == warehouse_id)
        
        # 总出库单数
        order_count_query = select(func.count(OutboundOrder.id))
        if conditions:
            order_count_query = order_count_query.where(and_(*conditions))
        
        order_count_result = await db.execute(order_count_query)
        order_count = order_count_result.scalar() or 0
        
        # 总出库数量
        qty_query = select(func.sum(OutboundItem.expected_qty)).join(OutboundOrder)
        if conditions:
            qty_query = qty_query.where(and_(*conditions))
        
        qty_result = await db.execute(qty_query)
        total_qty = qty_result.scalar() or 0
        
        # 按状态统计
        status_query = select(
            OutboundOrder.status,
            func.count(OutboundOrder.id).label("count"),
            func.sum(OutboundOrder.total_qty).label("qty")
        ).group_by(OutboundOrder.status)
        
        if conditions:
            status_query = status_query.where(and_(*conditions))
        
        status_result = await db.execute(status_query)
        status_stats = [
            {"status": row.status, "count": row.count, "quantity": row.qty or 0}
            for row in status_result.all()
        ]
        
        return {
            "order_count": order_count,
            "total_quantity": total_qty,
            "status_stats": status_stats
        }
    
    @staticmethod
    async def get_outbound_daily(
        db: AsyncSession,
        days: int = 30,
        warehouse_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """出库日报表"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = select(
            func.date(OutboundOrder.created_at).label("date"),
            func.count(OutboundOrder.id).label("order_count"),
            func.sum(OutboundOrder.total_qty).label("total_qty")
        ).where(OutboundOrder.created_at >= start_date)
        
        if warehouse_id:
            query = query.where(OutboundOrder.warehouse_id == warehouse_id)
        
        query = query.group_by(func.date(OutboundOrder.created_at)).order_by(func.date(OutboundOrder.created_at))
        
        result = await db.execute(query)
        
        return [
            {
                "date": str(row.date),
                "order_count": row.order_count,
                "total_quantity": row.total_qty or 0
            }
            for row in result.all()
        ]
    
    # ============= 盘点报表 =============
    
    @staticmethod
    async def get_check_summary(
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """盘点汇总报表"""
        conditions = []
        if start_date:
            conditions.append(CheckOrder.created_at >= start_date)
        if end_date:
            conditions.append(CheckOrder.created_at <= end_date)
        
        # 总盘点单数
        order_count_query = select(func.count(CheckOrder.id))
        if conditions:
            order_count_query = order_count_query.where(and_(*conditions))
        
        order_count_result = await db.execute(order_count_query)
        order_count = order_count_result.scalar() or 0
        
        # 按状态统计
        status_query = select(
            CheckOrder.status,
            func.count(CheckOrder.id).label("count")
        ).group_by(CheckOrder.status)
        
        if conditions:
            status_query = status_query.where(and_(*conditions))
        
        status_result = await db.execute(status_query)
        status_stats = [
            {"status": row.status, "count": row.count}
            for row in status_result.all()
        ]
        
        # 差异统计
        diff_query = select(
            func.sum(CheckOrder.matched_items).label("matched"),
            func.sum(CheckOrder.diff_items).label("diff")
        )
        
        if conditions:
            diff_query = diff_query.where(and_(*conditions))
        
        diff_result = await db.execute(diff_query)
        diff_row = diff_result.one_or_none()
        
        return {
            "order_count": order_count,
            "status_stats": status_stats,
            "matched_items": diff_row.matched if diff_row else 0,
            "diff_items": diff_row.diff if diff_row else 0
        }
    
    # ============= 预警报表 =============
    
    @staticmethod
    async def get_alert_summary(
        db: AsyncSession,
        days: int = 30
    ) -> Dict[str, Any]:
        """预警汇总报表"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # 总预警数
        total_query = select(func.count(AlertRecord.id)).where(AlertRecord.created_at >= start_date)
        total_result = await db.execute(total_query)
        total = total_result.scalar() or 0
        
        # 按类型统计
        type_query = select(
            AlertRecord.alert_type,
            func.count(AlertRecord.id).label("count")
        ).where(AlertRecord.created_at >= start_date).group_by(AlertRecord.alert_type)
        
        type_result = await db.execute(type_query)
        type_stats = [
            {"type": row.alert_type, "count": row.count}
            for row in type_result.all()
        ]
        
        # 按级别统计
        level_query = select(
            AlertRecord.alert_level,
            func.count(AlertRecord.id).label("count")
        ).where(AlertRecord.created_at >= start_date).group_by(AlertRecord.alert_level)
        
        level_result = await db.execute(level_query)
        level_stats = [
            {"level": row.alert_level, "count": row.count}
            for row in level_result.all()
        ]
        
        return {
            "total": total,
            "type_stats": type_stats,
            "level_stats": level_stats
        }
    
    # ============= 综合报表 =============
    
    @staticmethod
    async def get_dashboard_data(db: AsyncSession, warehouse_id: Optional[UUID] = None) -> Dict[str, Any]:
        """仪表盘数据"""
        # 库存概览
        inventory_summary = await ReportService.get_inventory_summary(db, warehouse_id)
        
        # 今日入库
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        inbound_today = await ReportService.get_inbound_summary(db, start_date=today, warehouse_id=warehouse_id)
        
        # 今日出库
        outbound_today = await ReportService.get_outbound_summary(db, start_date=today, warehouse_id=warehouse_id)
        
        # 待处理预警
        pending_alerts_query = select(func.count(AlertRecord.id)).where(
            and_(
                AlertRecord.status == "unread",
                AlertRecord.created_at >= today - timedelta(days=7)
            )
        )
        pending_alerts_result = await db.execute(pending_alerts_query)
        pending_alerts = pending_alerts_result.scalar() or 0
        
        # 待处理入库单
        pending_inbound_query = select(func.count(InboundOrder.id)).where(
            InboundOrder.status.in_(["pending", "receiving"])
        )
        if warehouse_id:
            pending_inbound_query = pending_inbound_query.where(InboundOrder.warehouse_id == warehouse_id)
        
        pending_inbound_result = await db.execute(pending_inbound_query)
        pending_inbound = pending_inbound_result.scalar() or 0
        
        # 待处理出库单
        pending_outbound_query = select(func.count(OutboundOrder.id)).where(
            OutboundOrder.status.in_(["pending", "picking"])
        )
        if warehouse_id:
            pending_outbound_query = pending_outbound_query.where(OutboundOrder.warehouse_id == warehouse_id)
        
        pending_outbound_result = await db.execute(pending_outbound_query)
        pending_outbound = pending_outbound_result.scalar() or 0
        
        return {
            "inventory": inventory_summary,
            "inbound_today": inbound_today,
            "outbound_today": outbound_today,
            "pending_tasks": {
                "alerts": pending_alerts,
                "inbound_orders": pending_inbound,
                "outbound_orders": pending_outbound
            }
        }

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta

from app.core.database import get_db
from app.services import ReportService

router = APIRouter(prefix="/reports", tags=["报表统计"])


# ============= 仪表盘 =============

@router.get("/dashboard")
async def get_dashboard(
    warehouse_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    """仪表盘数据"""
    return await ReportService.get_dashboard_data(db, warehouse_id)


# ============= 库存报表 =============

@router.get("/inventory/summary")
async def get_inventory_summary(
    warehouse_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    """库存汇总报表"""
    return await ReportService.get_inventory_summary(db, warehouse_id)


@router.get("/inventory/by-category")
async def get_inventory_by_category(
    warehouse_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    """按分类统计库存"""
    return await ReportService.get_inventory_by_category(db, warehouse_id)


@router.get("/inventory/by-warehouse")
async def get_inventory_by_warehouse(
    db: AsyncSession = Depends(get_db)
):
    """按仓库统计库存"""
    return await ReportService.get_inventory_by_warehouse(db)


# ============= 入库报表 =============

@router.get("/inbound/summary")
async def get_inbound_summary(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    warehouse_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    """入库汇总报表"""
    return await ReportService.get_inbound_summary(db, start_date, end_date, warehouse_id)


@router.get("/inbound/daily")
async def get_inbound_daily(
    days: int = Query(default=30, ge=1, le=365),
    warehouse_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    """入库日报表"""
    return await ReportService.get_inbound_daily(db, days, warehouse_id)


# ============= 出库报表 =============

@router.get("/outbound/summary")
async def get_outbound_summary(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    warehouse_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    """出库汇总报表"""
    return await ReportService.get_outbound_summary(db, start_date, end_date, warehouse_id)


@router.get("/outbound/daily")
async def get_outbound_daily(
    days: int = Query(default=30, ge=1, le=365),
    warehouse_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    """出库日报表"""
    return await ReportService.get_outbound_daily(db, days, warehouse_id)


# ============= 盘点报表 =============

@router.get("/check/summary")
async def get_check_summary(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    """盘点汇总报表"""
    return await ReportService.get_check_summary(db, start_date, end_date)


# ============= 预警报表 =============

@router.get("/alert/summary")
async def get_alert_summary(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """预警汇总报表"""
    return await ReportService.get_alert_summary(db, days)

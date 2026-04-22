from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.services import AlertService
from app.schemas import (
    InventoryAlertCreate, InventoryAlertUpdate, InventoryAlertResponse,
    AlertRecordResponse, AlertRecordResolve, AlertStats, CheckAlertRequest,
    PaginationParams
)

router = APIRouter(prefix="/alerts", tags=["库存预警"])


# ============= 预警规则管理 =============

@router.post("/rules", response_model=InventoryAlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert_rule(
    data: InventoryAlertCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建预警规则"""
    alert = await AlertService.create_alert(db, data)
    return alert


@router.get("/rules", response_model=List[InventoryAlertResponse])
async def list_alert_rules(
    alert_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """获取预警规则列表"""
    alerts = await AlertService.get_alerts(
        db,
        alert_type=alert_type,
        is_active=is_active,
        skip=(pagination.page - 1) * pagination.page_size,
        limit=pagination.page_size
    )
    return alerts


@router.get("/rules/{alert_id}", response_model=InventoryAlertResponse)
async def get_alert_rule(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """获取预警规则详情"""
    alert = await AlertService.get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="预警规则不存在")
    return alert


@router.put("/rules/{alert_id}", response_model=InventoryAlertResponse)
async def update_alert_rule(
    alert_id: UUID,
    data: InventoryAlertUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新预警规则"""
    alert = await AlertService.update_alert(db, alert_id, data)
    if not alert:
        raise HTTPException(status_code=404, detail="预警规则不存在")
    return alert


@router.delete("/rules/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert_rule(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """删除预警规则"""
    success = await AlertService.delete_alert(db, alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="预警规则不存在")
    return None


# ============= 预警检查 =============

@router.post("/check", response_model=List[AlertRecordResponse])
async def check_alerts(
    request: Optional[CheckAlertRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    """检查库存预警"""
    records = await AlertService.check_alerts(db, request)
    return records


# ============= 预警记录 =============

@router.get("/records", response_model=List[AlertRecordResponse])
async def list_alert_records(
    status: Optional[str] = None,
    alert_type: Optional[str] = None,
    alert_level: Optional[str] = None,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """获取预警记录列表"""
    records = await AlertService.get_alert_records(
        db,
        status=status,
        alert_type=alert_type,
        alert_level=alert_level,
        skip=(pagination.page - 1) * pagination.page_size,
        limit=pagination.page_size
    )
    return records


@router.get("/records/{record_id}", response_model=AlertRecordResponse)
async def get_alert_record(
    record_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """获取预警记录详情"""
    record = await AlertService.get_alert_record_by_id(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="预警记录不存在")
    return record


@router.post("/records/{record_id}/read", response_model=AlertRecordResponse)
async def read_alert_record(
    record_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """标记预警记录为已读"""
    record = await AlertService.read_alert_record(db, record_id)
    if not record:
        raise HTTPException(status_code=400, detail="预警记录不存在或状态不允许")
    return record


@router.post("/records/{record_id}/resolve", response_model=AlertRecordResponse)
async def resolve_alert_record(
    record_id: UUID,
    data: AlertRecordResolve,
    db: AsyncSession = Depends(get_db)
):
    """处理预警记录"""
    record = await AlertService.resolve_alert_record(db, record_id, data, "admin")
    if not record:
        raise HTTPException(status_code=400, detail="预警记录不存在或状态不允许")
    return record


# ============= 预警统计 =============

@router.get("/stats", response_model=AlertStats)
async def get_alert_stats(
    db: AsyncSession = Depends(get_db)
):
    """获取预警统计"""
    stats = await AlertService.get_alert_stats(db)
    return AlertStats(**stats)

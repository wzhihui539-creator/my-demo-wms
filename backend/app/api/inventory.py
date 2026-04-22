from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.services import InventoryService
from app.schemas import InventoryResponse

router = APIRouter(prefix="/inventory", tags=["库存管理"])


@router.get("/")
async def get_all_inventory(
    db: AsyncSession = Depends(get_db)
):
    """获取所有库存"""
    inventories = await InventoryService.get_all(db)
    result = []
    for inv in inventories:
        result.append({
            "id": str(inv.id),
            "sku_id": str(inv.sku_id),
            "location_id": str(inv.location_id),
            "lot_id": str(inv.lot_id) if inv.lot_id else None,
            "quantity": inv.quantity,
            "available_qty": inv.available_qty,
            "locked_qty": inv.locked_qty,
            "status": inv.status,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
            "updated_at": inv.updated_at.isoformat() if inv.updated_at else None
        })
    return result


@router.get("/location/{location_id}")
async def get_inventory_by_location(
    location_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """获取库位库存"""
    inventories = await InventoryService.get_by_location(db, location_id)
    # 手动构建响应，避免关联加载问题
    result = []
    for inv in inventories:
        result.append({
            "id": str(inv.id),
            "sku_id": str(inv.sku_id),
            "location_id": str(inv.location_id),
            "lot_id": str(inv.lot_id) if inv.lot_id else None,
            "quantity": inv.quantity,
            "available_qty": inv.available_qty,
            "locked_qty": inv.locked_qty,
            "status": inv.status,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
            "updated_at": inv.updated_at.isoformat() if inv.updated_at else None
        })
    return result


@router.get("/sku/{sku_id}")
async def get_inventory_by_sku(
    sku_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """获取商品库存分布"""
    inventories = await InventoryService.get_by_sku(db, sku_id)
    # 手动构建响应，避免关联加载问题
    result = []
    for inv in inventories:
        result.append({
            "id": str(inv.id),
            "sku_id": str(inv.sku_id),
            "location_id": str(inv.location_id),
            "lot_id": str(inv.lot_id) if inv.lot_id else None,
            "quantity": inv.quantity,
            "available_qty": inv.available_qty,
            "locked_qty": inv.locked_qty,
            "status": inv.status,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
            "updated_at": inv.updated_at.isoformat() if inv.updated_at else None
        })
    return result

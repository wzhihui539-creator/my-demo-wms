from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.services import WarehouseService, ZoneService, LocationService
from app.schemas import (
    WarehouseCreate, WarehouseUpdate, WarehouseResponse,
    ZoneCreate, ZoneResponse,
    LocationCreate, LocationResponse,
    PaginationParams
)

router = APIRouter(prefix="/warehouses", tags=["仓库管理"])


@router.post("", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
async def create_warehouse(
    data: WarehouseCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建仓库"""
    warehouse = await WarehouseService.create(db, data)
    return warehouse


@router.get("", response_model=List[WarehouseResponse])
async def list_warehouses(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """获取仓库列表"""
    warehouses = await WarehouseService.get_list(
        db, 
        skip=(pagination.page - 1) * pagination.page_size,
        limit=pagination.page_size
    )
    return warehouses


@router.get("/{warehouse_id}", response_model=WarehouseResponse)
async def get_warehouse(
    warehouse_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """获取仓库详情"""
    warehouse = await WarehouseService.get_by_id(db, warehouse_id)
    if not warehouse:
        raise HTTPException(status_code=404, detail="仓库不存在")
    return warehouse


@router.put("/{warehouse_id}", response_model=WarehouseResponse)
async def update_warehouse(
    warehouse_id: UUID,
    data: WarehouseUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新仓库"""
    warehouse = await WarehouseService.update(db, warehouse_id, data)
    if not warehouse:
        raise HTTPException(status_code=404, detail="仓库不存在")
    return warehouse


# 库区管理
@router.post("/{warehouse_id}/zones", response_model=ZoneResponse, status_code=status.HTTP_201_CREATED)
async def create_zone(
    warehouse_id: UUID,
    data: ZoneCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建库区"""
    # 验证仓库存在
    warehouse = await WarehouseService.get_by_id(db, warehouse_id)
    if not warehouse:
        raise HTTPException(status_code=404, detail="仓库不存在")
    
    data.warehouse_id = warehouse_id
    zone = await ZoneService.create(db, data)
    return zone


@router.get("/{warehouse_id}/zones", response_model=List[ZoneResponse])
async def list_zones(
    warehouse_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """获取仓库下的库区列表"""
    zones = await ZoneService.get_by_warehouse(db, warehouse_id)
    return zones


# 库位管理
@router.post("/zones/{zone_id}/locations", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    zone_id: UUID,
    data: LocationCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建库位"""
    data.zone_id = zone_id
    location = await LocationService.create(db, data)
    return location


@router.get("/zones/{zone_id}/locations", response_model=List[LocationResponse])
async def list_locations(
    zone_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """获取库区下的库位列表"""
    locations = await LocationService.get_by_zone(db, zone_id)
    return locations

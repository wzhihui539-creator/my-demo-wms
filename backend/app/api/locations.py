from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.services import LocationService
from app.schemas import LocationResponse, PaginationParams

router = APIRouter(prefix="/locations", tags=["库位"])


@router.get("", response_model=List[LocationResponse])
async def list_all_locations(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """获取全部库位列表（供前端下拉选择）"""
    return await LocationService.get_all(
        db,
        skip=(pagination.page - 1) * pagination.page_size,
        limit=pagination.page_size,
    )

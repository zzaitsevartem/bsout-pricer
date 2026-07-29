from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.modules.plans.schema.plans import PlanResponse
from src.modules.plans.service.plans_service import PlanService

router = APIRouter(tags=["plans"])


@router.get("/api/plans", response_model=list[PlanResponse])
async def list_plans(db: AsyncSession = Depends(get_db)):
    return await PlanService.get_all(db)

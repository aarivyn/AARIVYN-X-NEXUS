from typing import List
from fastapi import APIRouter
from schemas import InterventionCardSchema
from services.optimizer_service import INTERVENTIONS_DATASET

router = APIRouter(prefix="/interventions", tags=["Legacy Interventions Endpoints"])

@router.get("/", response_model=List[InterventionCardSchema])
def get_all_interventions():
    return [InterventionCardSchema(**item) for item in INTERVENTIONS_DATASET]

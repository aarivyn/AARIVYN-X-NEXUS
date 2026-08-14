from typing import List, Optional
from fastapi import APIRouter, HTTPException, Path
from schemas import PortfolioSchema, ImplementationPlanResponse
from services.optimizer_service import run_nsga2_optimization
from services.portfolio_service import generate_implementation_plan

router = APIRouter(prefix="/portfolio", tags=["Module 7: Portfolios & Implementation Plan"])

@router.get("/pareto")
def get_pareto_portfolios():
    portfolios = run_nsga2_optimization()
    return {"status": "success", "portfolios": portfolios}

@router.post("/{portfolio_id}/implementation-plan", response_model=ImplementationPlanResponse)
def create_portfolio_implementation_plan(portfolio_id: str = Path(...)):
    portfolios = run_nsga2_optimization()
    matched = None
    for p in portfolios:
        if p["id"] == portfolio_id:
            matched = p
            break
            
    if not matched:
        # Fallback to first portfolio if ID not found
        matched = portfolios[0]
        
    portfolio_obj = PortfolioSchema(**matched)
    return generate_implementation_plan(portfolio_obj)

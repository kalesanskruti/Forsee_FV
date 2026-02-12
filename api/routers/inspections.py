from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from uuid import UUID

from api import deps
from models.user import User, Role
from schemas.inspection import (
    InspectionCreate, 
    InspectionUpdate, 
    InspectionResponse, 
    InspectionPreviewRequest, 
    InspectionPreviewResponse
)
from services.inspection_service import InspectionService

router = APIRouter()

@router.post("/draft", response_model=InspectionResponse)
def create_draft_inspection(
    *,
    db: Session = Depends(deps.get_db),
    inspection_in: InspectionCreate,
    current_user: User = Depends(deps.require_role([Role.ENGINEER, Role.ADMIN])),
) -> Any:
    """
    Create a new manual inspection draft.
    """
    try:
        inspection = InspectionService.create_draft(db, inspection_in, current_user.id)
        return inspection
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{inspection_id}/commit", response_model=InspectionResponse)
def commit_inspection(
    *,
    db: Session = Depends(deps.get_db),
    inspection_id: UUID,
    current_user: User = Depends(deps.require_role([Role.ENGINEER, Role.ADMIN])),
) -> Any:
    """
    Finalize and submit an inspection.
    Triggers degradation update and RUL recalculation.
    """
    try:
        # Verify ownership or admin if needed - Service handles logic
        inspection = InspectionService.submit_inspection(db, inspection_id, current_user.id)
        return inspection
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/preview", response_model=InspectionPreviewResponse)
def preview_inspection_impact(
    *,
    inspection_in: InspectionPreviewRequest,
    current_user: User = Depends(deps.require_role([Role.ENGINEER, Role.ADMIN])),
) -> Any:
    """
    Simulate the impact of an inspection without saving.
    """
    # Use service logic to calculate impact on the fly
    # Map schemas to dummy items if needed by the helper
    # For now, simplistic approximation using the same logic as service
    from models.inspection import InspectionItem
    
    dummy_items = [
        InspectionItem(severity=item.severity) for item in inspection_in.items
    ]
    
    impact = InspectionService._calculate_impact(dummy_items)
    
    return {
        "projected_damage_modifier": impact["rate_modifier"],
        "projected_step_damage": impact["step_damage"],
        "projected_confidence_change": impact["confidence_penalty"],
        "rul_impact_assessment": "Significant reduction likely" if impact["overall_severity"] == "SEVERE" else "Minor adjustment"
    }

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from api import deps
from services.admin_service import AdminService
from models.user import User, Role
from schemas.user import User as UserSchema # Assuming basic user schema exists, or we use dicts
from pydantic import BaseModel

router = APIRouter()

# --- Request Schemas ---
class PolicyUpdate(BaseModel):
    warning_threshold: str | None = None
    critical_threshold: str | None = None

class SimulationControl(BaseModel):
    action: str # "TRIGGER_RETRAINING", "SIMULATE_DRIFT"
    target_id: str | None = None

# --- Dependencies ---
def get_current_admin(
    current_user: User = Depends(deps.get_current_active_user),
) -> User:
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user

# --- Endpoints ---

@router.get("/system-context", response_model=Dict[str, Any])
def get_system_context(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    1. GLOBAL SYSTEM CONTEXT SERVICE
    Returns environment state, active users, and global alert status.
    """
    return AdminService.get_global_system_context(db, str(current_user.org_id))

@router.get("/kpi", response_model=Dict[str, Any])
def get_kpi_metrics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    2. SYSTEM OVERVIEW & KPI AGGREGATION SERVICE
    Returns aggregated metrics for top-level cards.
    """
    return AdminService.get_kpi_aggregation(db, str(current_user.org_id))

@router.get("/fleet", response_model=List[Dict[str, Any]])
def get_fleet_intelligence(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    3. ASSET & FLEET INTELLIGENCE SERVICE
    Returns paginated asset list with calculated risk levels.
    """
    return AdminService.get_asset_fleet_table(db, str(current_user.org_id), skip, limit)

@router.post("/policy", response_model=Dict[str, Any])
def update_policy_thresholds(
    policy_update: PolicyUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    6. ORGANIZATION THRESHOLDS & POLICY ENGINE
    Updates org-wide risk thresholds.
    """
    updates = policy_update.dict(exclude_unset=True)
    updated_org = AdminService.update_organization_policy(
        db, str(current_user.org_id), str(current_user.id), updates
    )
    return {"status": "updated", "warning_threshold": updated_org.warning_threshold}

@router.get("/audit-logs", response_model=List[Dict[str, Any]])
def get_audit_logs(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    8. AUDIT & COMPLIANCE LEDGER
    Returns immutable audit logs.
    """
    # Simple query implementation directly here or in service
    from models.platform import AuditLog
    logs = db.query(AuditLog).filter(
        AuditLog.org_id == current_user.org_id
    ).order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "action": log.action,
            "details": log.details,
            "timestamp": log.timestamp,
            "user_id": str(log.user_id)
        }
        for log in logs
    ]

@router.post("/simulation/control", response_model=Dict[str, Any])
def trigger_simulation(
    control: SimulationControl,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    9. ADMIN SIMULATION & CONTROL
    Allows Admin to trigger system-wide events like Re-training.
    """
    # Log the attempt
    AdminService.log_admin_action(
        db, str(current_user.org_id), str(current_user.id),
        action="TRIGGER_SIMULATION",
        details=control.dict()
    )
    
    # Logic placeholder - in real system this would push to Redis queue
    return {
        "status": "initiated", 
        "message": f"Simulation {control.action} started. Monitoring impact."
    }

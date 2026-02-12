from typing import List, Optional, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from uuid import UUID
from enum import Enum

class InspectionStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    ARCHIVED = "ARCHIVED"

class InspectionSeverity(str, Enum):
    NONE = "NONE"
    MILD = "MILD"
    MODERATE = "MODERATE"
    SEVERE = "SEVERE"

class InspectionPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

# --- Items ---

class InspectionItemBase(BaseModel):
    component_name: str
    severity: InspectionSeverity = InspectionSeverity.NONE
    priority: InspectionPriority = InspectionPriority.LOW
    comments: Optional[str] = None
    value_numeric: Optional[float] = None
    value_unit: Optional[str] = None
    evidence_url: Optional[str] = None

class InspectionItemCreate(InspectionItemBase):
    pass

class InspectionItemUpdate(InspectionItemBase):
    pass

class InspectionItemResponse(InspectionItemBase):
    id: UUID
    inspection_id: UUID
    
    class Config:
        orm_mode = True

# --- Main Inspection ---

class InspectionBase(BaseModel):
    asset_id: UUID
    shift_id: Optional[str] = None
    is_in_shift: bool
    off_shift_activity_detected: bool = False

class InspectionCreate(InspectionBase):
    items: List[InspectionItemCreate] = []

class InspectionUpdate(BaseModel):
    items: Optional[List[InspectionItemCreate]] = None # Full replace for items in draft? simpler
    shift_id: Optional[str] = None
    is_in_shift: Optional[bool] = None
    off_shift_activity_detected: Optional[bool] = None
    status: Optional[InspectionStatus] = None

class InspectionResponse(InspectionBase):
    id: UUID
    inspector_id: UUID
    status: InspectionStatus
    submitted_at: Optional[datetime]
    
    overall_severity: InspectionSeverity
    calculated_damage_modifier: float
    calculated_step_damage: float
    confidence_adjustment: float
    
    items: List[InspectionItemResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class InspectionPreviewRequest(InspectionCreate):
    pass

class InspectionPreviewResponse(BaseModel):
    projected_damage_modifier: float
    projected_step_damage: float
    projected_confidence_change: float
    rul_impact_assessment: str

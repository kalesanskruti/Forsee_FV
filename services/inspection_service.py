from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from typing import Dict, Any, List
import json

from models.inspection import Inspection, InspectionItem, InspectionStatus, InspectionSeverity
from models.ml import Asset
from models.outbox import OutboxEvent, OutboxStatus
from models.platform import AuditLog
from schemas.inspection import InspectionCreate, InspectionUpdate
from core.events import InspectionSubmittedEvent # Schema for payload

class InspectionService:
    
    @staticmethod
    def _calculate_impact(items: List[InspectionItem]) -> Dict[str, float]:
        """
        Derive multipliers and step damage from items.
        """
        max_severity = InspectionSeverity.NONE
        severity_rank = {
            InspectionSeverity.NONE: 0,
            InspectionSeverity.MILD: 1,
            InspectionSeverity.MODERATE: 2,
            InspectionSeverity.SEVERE: 3
        }
        
        step_damage = 0.0
        rate_modifier_sum = 0.0
        confidence_penalty = 0.0
        
        for item in items:
            # Track max severity
            if severity_rank[item.severity] > severity_rank.get(max_severity, 0):
                max_severity = item.severity
            
            # Step Damage (Accumulates)
            if item.severity == InspectionSeverity.MILD:
                step_damage += 0.0001
            elif item.severity == InspectionSeverity.MODERATE:
                step_damage += 0.0005
                confidence_penalty += 0.05
            elif item.severity == InspectionSeverity.SEVERE:
                step_damage += 0.002
                rate_modifier_sum += 0.1 # Permanent rate increase for severe issues
                confidence_penalty += 0.15
        
        # Base modifier is 1.0, plus sum of severity impacts
        final_rate_modifier = 1.0 + rate_modifier_sum
        
        # Cap confidence penalty
        final_confidence_penalty = min(0.5, confidence_penalty)
        
        return {
            "overall_severity": max_severity,
            "step_damage": step_damage,
            "rate_modifier": final_rate_modifier,
            "confidence_penalty": final_confidence_penalty
        }

    @staticmethod
    def create_draft(db: Session, schema: InspectionCreate, user_id: UUID) -> Inspection:
        """
        Create a new draft.
        """
        db_obj = Inspection(
            asset_id=schema.asset_id,
            inspector_id=user_id,
            status=InspectionStatus.DRAFT,
            is_in_shift=schema.is_in_shift,
            off_shift_activity_detected=schema.off_shift_activity_detected,
            shift_id=schema.shift_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        # Add items
        for item_in in schema.items:
            item = InspectionItem(
                inspection_id=db_obj.id,
                **item_in.dict()
            )
            db.add(item)
        
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def submit_inspection(db: Session, inspection_id: UUID, user_id: UUID) -> Inspection:
        """
        Finalize inspection and create Outbox Event.
        DOES NOT call IntelligenceService directly anymore.
        """
        insp = db.query(Inspection).filter(Inspection.id == inspection_id).first()
        if not insp: raise ValueError("Inspection not found")
        if insp.status != InspectionStatus.DRAFT: raise ValueError("Inspection already submitted")
        
        # 1. Calculate Final Impact
        impact = InspectionService._calculate_impact(insp.items)
        
        insp.overall_severity = impact["overall_severity"]
        insp.calculated_damage_modifier = impact["rate_modifier"]
        insp.calculated_step_damage = impact["step_damage"]
        insp.confidence_adjustment = impact["confidence_penalty"]
        insp.status = InspectionStatus.SUBMITTED
        insp.submitted_at = datetime.utcnow()
        
        from core import context
        ctx = context.get_context()
        org_id = str(ctx.org_id) if ctx and ctx.org_id else str(insp.asset_id)

        # 2. Create Transactional Outbox Event
        # Payload schema matches core.events.InspectionSubmittedEvent fields
        event_payload = {
            "event_id": str(datetime.utcnow().timestamp()), # Simple ID for now
            "schema_version": "1.0",
            "timestamp": datetime.utcnow().isoformat(),
            "asset_id": str(insp.asset_id),
            "tenant_id": org_id,
            "inspection_id": str(insp.id),
            "overall_severity": insp.overall_severity,
            "calculated_damage_modifier": insp.calculated_damage_modifier,
            "calculated_step_damage": insp.calculated_step_damage,
            "confidence_adjustment": insp.confidence_adjustment
        }
        
        outbox_entry = OutboxEvent(
            topic="inspection.submitted",
            payload=event_payload,
            status=OutboxStatus.PENDING,
            org_id=UUID(org_id) if ctx and ctx.org_id else None
        )
        db.add(outbox_entry)
        
        # 3. Log Audit
        audit = AuditLog(
            action="INSPECTION_SUBMITTED",
            details={
                "inspection_id": str(insp.id),
                "asset_id": str(insp.asset_id),
                "severity": insp.overall_severity
            },
            timestamp=datetime.utcnow(),
            user_id=user_id,
            org_id=UUID(org_id) if ctx and ctx.org_id else None
        )
        db.add(audit)
        
        db.commit()
        db.refresh(insp)
        return insp

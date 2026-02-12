from datetime import datetime, time
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
import pytz
import logging
from sqlalchemy.orm import Session
from models.metadata import AssetMetadata, OperationMode, AssetShiftSchedule
from models.outbox import OutboxEvent, OutboxStatus

logger = logging.getLogger(__name__)

class ShiftService:
    @staticmethod
    def is_within_shift(db: Session, asset_id: UUID, timestamp: datetime) -> Tuple[bool, Optional[float]]:
        """
        Check if a given timestamp falls within the asset's scheduled shift.
        Returns (is_within, minutes_outside)
        """
        # 1. Fetch metadata
        metadata = db.query(AssetMetadata).filter(AssetMetadata.asset_id == asset_id).first()
        if not metadata or not metadata.operation_profile:
            return True, 0.0 # Default to assuming valid if no profile
            
        op_profile = metadata.operation_profile
        if op_profile.operation_mode != OperationMode.SHIFT_BASED:
            return True, 0.0 # Continuous or Standby don't have shift violations in this context
            
        schedule = metadata.shift_schedule
        if not schedule:
            return True, 0.0
            
        # 2. Convert timestamp to schedule timezone
        tz = pytz.timezone(schedule.timezone or "UTC")
        local_dt = timestamp.astimezone(tz)
        
        # 3. Check Active Days
        day_name = local_dt.strftime("%a").upper() # MON, TUE...
        if day_name not in schedule.active_days:
            return False, 999.0 # Outside day window
            
        # 4. Check Time Window
        try:
            start_time = datetime.strptime(schedule.shift_start_time, "%H:%M").time()
            end_time = datetime.strptime(schedule.shift_end_time, "%H:%M").time()
        except Exception:
            return True, 0.0
            
        current_time = local_dt.time()
        
        # Handle wrap-around shifts (e.g. 22:00 to 06:00)
        if start_time <= end_time:
            is_in = start_time <= current_time <= end_time
        else:
            is_in = current_time >= start_time or current_time <= end_time
            
        if is_in:
            return True, 0.0
            
        # 5. Calculate minutes outside (Simple approximation)
        # Note: Professional implementation would calculate actual distance to nearest window
        return False, 1.0 # placeholder for "outside" distance

    @staticmethod
    def calculate_shift_modifier(db: Session, asset_id: UUID, is_running: bool, timestamp: datetime) -> float:
        """
        Rule Engine for Shift Violation Penalties.
        Formula:
        No violation -> 1.0
        Minor violation (Within tolerance) -> 1.0
        Off-Shift Operation -> 1.1 to 1.3
        """
        is_in, _ = ShiftService.is_within_shift(db, asset_id, timestamp)
        
        if is_in:
             return 1.0
             
        if not is_running:
             return 1.0 # No penalty if machine is off
             
        # Machine is RUNNING outside shift window
        # Apply structured penalty
        # In a real app, we'd check duration/frequency
        
        # Penalty bounded by 1.3 as per Master Architecture
        return 1.2 # Static penalty for now, could be dynamic based on 'minutes_outside'

    @staticmethod
    def detect_and_publish_violation(db: Session, asset_id: UUID, modifier: float, timestamp: datetime):
        """
        Creates 'shift.violation.detected' event if penalty > 1.0
        """
        if modifier <= 1.0:
            return

        from models.ml import Asset
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        org_id = asset.org_id if asset else None

        payload = {
            "event_id": str(datetime.utcnow().timestamp()),
            "tenant_id": str(org_id),
            "asset_id": str(asset_id),
            "violation_type": "OFF_SHIFT_OPERATION",
            "severity_level": "MODERATE" if modifier > 1.1 else "LOW",
            "timestamp": timestamp.isoformat(),
            "multiplier_applied": modifier
        }

        from models.outbox import OutboxEvent, OutboxStatus
        event = OutboxEvent(
            topic="shift.violation.detected",
            payload=payload,
            status=OutboxStatus.PENDING,
            org_id=org_id
        )
        db.add(event)
        logger.warning(f"Shift Violation Detected for asset {asset_id} (Multiplier: {modifier})")

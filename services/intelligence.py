from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List, Optional
from uuid import UUID
import json
import hashlib
from datetime import datetime, timedelta

from models.intelligence import (
    DecisionRecord, AutonomyLevel, FailureMode, AssetDependency, 
    CostModel, TechnicalResource, SparePart, AssetHealthState
)
from models.ml import Asset, MLModel, MaintenanceEvent
from models.user import User
from models.outbox import OutboxEvent, OutboxStatus
from core.events import SensorBatchIngestedEvent
from ml.models.degradation_model import DegradationModel
from services.cache import CacheService

class IntelligenceService:
    @staticmethod
    def ingest_sensor_data(db: Session, asset_id: UUID, sensor_data: Dict[str, float]) -> str:
        """
        Ingest telemetry asynchronously.
        Creates an Outbox Event 'sensor.batch.ingested'.
        """
        batch_id = str(datetime.utcnow().timestamp())
        
        # Create Event Payload
        payload = {
            "event_id": batch_id,
            "schema_version": "1.0",
            "timestamp": datetime.utcnow().isoformat(),
            "asset_id": str(asset_id),
            "batch_id": batch_id,
            "row_count": 1,
            "sensor_data": sensor_data
        }

        from core import context
        ctx = context.get_context()
        org_id = str(ctx.org_id) if ctx and ctx.org_id else str(asset_id)

        payload["tenant_id"] = org_id
        
        event = OutboxEvent(
            topic="sensor.batch.ingested",
            payload=payload,
            status=OutboxStatus.PENDING,
            org_id=UUID(org_id) if ctx and ctx.org_id else None
        )
        db.add(event)
        # db.commit() # Let caller commit to bundle with other logic if needed
        return batch_id

    @staticmethod
    def get_asset_health_state(db: Session, asset_id: UUID) -> AssetHealthState:
        """Fetch or initialize health state for an asset."""
        state = db.query(AssetHealthState).filter(AssetHealthState.asset_id == asset_id).first()
        if not state:
            state = AssetHealthState(asset_id=asset_id)
            db.add(state)
            db.commit()
            db.refresh(state)
        return state

    @staticmethod
    def normalize_stress(sensor_data: Dict[str, float], asset: Asset) -> Dict[str, float]:
        """
        4. SEPARATE STRESS FROM DAMAGE
        Implement a stress normalization layer BEFORE damage estimation.
        """
        metadata = asset.meta_data or {}
        duty_pattern = metadata.get("duty_pattern", "continuous") # continuous, shift, intermittent
        typical_load = metadata.get("typical_load_range", [0, 100])
        
        # Example Normalizations
        vibration = sensor_data.get("vibration", 0.0)
        load = sensor_data.get("load", 1.0)
        
        normalized_data = sensor_data.copy()
        
        # Vibration ÷ load
        normalized_data["vibration_normalized"] = vibration / (load + 1e-6)
        
        # Temperature ÷ ambient
        temp = sensor_data.get("temperature", 60.0)
        ambient = sensor_data.get("ambient_temp", 25.0)
        normalized_data["temp_delta"] = temp - ambient
        
        # Current ÷ RPM
        current = sensor_data.get("current", 10.0)
        rpm = sensor_data.get("rpm", 1500)
        normalized_data["current_normalized"] = current / (rpm + 1e-6)
        
        return normalized_data

    @staticmethod
    def process_telemetry_window(
        db: Session, 
        asset_id: UUID, 
        sensor_data: Dict[str, float],
        human_modifier: float = 1.0 # 9. HUMAN INPUT INTEGRATION
    ):
        """
        Main entry point for periodic telemetry processing.
        """
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset: return
        
        # 1. Shift Violation Evaluation
        from services.shift_service import ShiftService
        meta = asset.meta_data or {}
        
        # Determine if running (Sync with DegradationModel logic)
        rpm = sensor_data.get("rpm", 0)
        idle_rpm = meta.get("idle_rpm_threshold", 100)
        is_running = rpm >= idle_rpm
        
        # Calculate Modifier (1.0 to 1.3)
        now = datetime.utcnow()
        shift_modifier = ShiftService.calculate_shift_modifier(db, asset_id, is_running, now)
        
        # 2. Context Extraction
        dt_hours = sensor_data.get("dt_hours", 1.0 / 60.0) 
        
        context = {
            "dt_hours": dt_hours,
            "shift_modifier": shift_modifier
        }
        
        # 3. Damage Calculation
        increment = DegradationModel.compute_damage_proxy(sensor_data, meta, context)
        
        # 9. Human Modulation (Bounded and confidence-weighted)
        effective_modifier = max(0.5, min(2.0, human_modifier))
        
        # 4. Integrate Cumulative Damage
        health = IntelligenceService.get_asset_health_state(db, asset_id)

        # Update Shift State & Anomaly Score
        if shift_modifier > 1.0:
            health.shift_violation_count += 1
            health.shift_anomaly_score = min(1.0, health.shift_anomaly_score + 0.1)
            # Publish Event
            ShiftService.detect_and_publish_violation(db, asset_id, shift_modifier, now)
        else:
            health.shift_anomaly_score = max(0.0, health.shift_anomaly_score - 0.02)
            
        health.last_shift_modifier = shift_modifier
        
        # Apply modifier to usage components only (Physics says environment is invariant to human opinion mostly)
        health.cumulative_mechanical_damage += (increment.mechanical * effective_modifier)
        health.cumulative_thermal_damage += (increment.thermal * effective_modifier)
        health.cumulative_electrical_damage += (increment.electrical * effective_modifier)
        health.cumulative_strain_damage += (increment.strain * effective_modifier)
        health.cumulative_environmental_damage += increment.environmental
        
        # Total now includes environmental
        total_inc = (increment.total - increment.environmental) * effective_modifier + increment.environmental
        health.total_cumulative_damage += total_inc
        
        # Update damage rate history (sliding window for RUL)
        history = list(health.damage_rate_history or [])
        history.append(total_inc)
        if len(history) > 100: history.pop(0) # Keep last 100 increments
        health.damage_rate_history = history
        
        # 5. Update Health Vectors (Score 0-100)
        limit = health.failure_threshold_mean
        
        # Mechanical Score (Includes Strain)
        mech_total = health.cumulative_mechanical_damage + health.cumulative_strain_damage
        health.mechanical_health_score = max(0, 100 * (1 - (mech_total / limit)))
        
        # Thermal Score (Includes Environmental as it's often degradation of materials)
        therm_total = health.cumulative_thermal_damage + health.cumulative_environmental_damage
        health.thermal_health_score = max(0, 100 * (1 - (therm_total / limit)))
        
        # Electrical Score
        health.electrical_health_score = max(0, 100 * (1 - (health.cumulative_electrical_damage / limit)))
        
        # Environmental Score (Absolute Completeness)
        health.environmental_health_score = max(0, 100 * (1 - (health.cumulative_environmental_damage / limit)))
        
        # Overall
        health.operational_health_score = max(0, 100 * (1 - (health.total_cumulative_damage / limit)))
        
        db.commit()
        return health

    @staticmethod
    def get_probabilistic_rul(db: Session, asset_id: UUID) -> Dict[str, Any]:
        """
        Check Redis Cache first. Fallback to DB if miss.
        """
        # 1. Fetch Asset for tenant scoping
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset: return {}
        
        tenant_id = str(asset.org_id)
        
        # 2. Try Cache
        cached = CacheService.get_json(tenant_id, str(asset_id), "rul")
        if cached:
            # logger.info("RUL Cache HIT")
            return cached.get("rul_data", {})
            
        # 3. Cache Miss: Compute
        health = IntelligenceService.get_asset_health_state(db, asset_id)
        remaining_capacity = health.failure_threshold_mean - health.total_cumulative_damage
        result = DegradationModel.estimate_rul_bounds(
            remaining_capacity=remaining_capacity,
            damage_rate_history=health.damage_rate_history or [],
            shift_violation_penalty=health.shift_anomaly_score
        )
        
        # 4. Populate Cache for subsequent reads
        cache_payload = {
            "rul_data": result,
            "timestamp": datetime.utcnow().isoformat(),
            "asset_id": str(asset_id),
            "tenant_id": tenant_id
        }
        CacheService.set_json(tenant_id, str(asset_id), "rul", cache_payload, ttl_seconds=300)
        
        # 5. Publish Event to Outbox
        from models.outbox import OutboxEvent, OutboxStatus
        payload = {
            "asset_id": str(asset_id),
            "rul_mean": result["mean"],
            "lower_bound": result["lower_bound"],
            "upper_bound": result["upper_bound"],
            "confidence": result["confidence"],
            "timestamp": datetime.utcnow().isoformat()
        }
        event = OutboxEvent(
            topic="rul.updated",
            payload=payload,
            status=OutboxStatus.PENDING,
            org_id=UUID(tenant_id)
        )
        db.add(event)
        db.commit()
        
        return result

    @staticmethod
    def apply_inspection_impact(
        db: Session,
        asset_id: UUID,
        damage_step: float,
        rate_modifier: float,
        confidence_penalty: float
    ):
        """
        Apply manual inspection results to the physics model.
        1. Apply immediate 'step' damage (if severity found).
        2. Adjust long-term rate modifier in metadata.
        3. Adjust confidence score.
        """
        # 1. Step Damage
        health = IntelligenceService.get_asset_health_state(db, asset_id)
        if damage_step > 0:
            # Distribute step damage (assume widespread if generic)
            health.total_cumulative_damage += damage_step
            # For now, attribute to mechanical as default if not specified
            health.cumulative_mechanical_damage += damage_step
            
        # 2. Rate Modifier (Updates Metadata for future DegradationModel calls)
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if asset:
            meta = asset.meta_data or {}
            # Update or Set modifier. If it exists, maybe average it? 
            # For now, we take the latest inspection as the truth for the modifier.
            meta["human_degradation_modifier"] = float(rate_modifier)
            asset.meta_data = meta
            
        # 3. Confidence Adjustment
        if confidence_penalty > 0:
            # Reduce confidence
            health.confidence_score = max(0.1, health.confidence_score - confidence_penalty)
            
        db.flush() # Caller commits

    @staticmethod
    def create_decision_record(
        db: Session,
        asset_id: UUID,
        model_id: UUID,
        risk_score: float,
        recommendation: str,
        urgency: str,
        confidence: float,
        drift_status: str,
        snapshot: Dict[str, Any],
        explainability: Dict[str, Any]
    ) -> DecisionRecord:
        """
        1. DECISION LEDGER
        Creates an immutable decision record.
        """
        # Calculate Hash Chain (Simple implementation)
        last_record = db.query(DecisionRecord).filter(DecisionRecord.asset_id == asset_id).order_by(DecisionRecord.timestamp.desc()).first()
        prev_hash = last_record.hash_chain if last_record and last_record.hash_chain else "GENESIS"
        
        # Payload to hash
        payload = f"{asset_id}{model_id}{risk_score}{recommendation}{prev_hash}{datetime.utcnow().isoformat()}"
        curr_hash = hashlib.sha256(payload.encode()).hexdigest()
        
        record = DecisionRecord(
            asset_id=asset_id,
            model_id=model_id,
            asset_state_snapshot=snapshot,
            risk_score=risk_score,
            recommended_action=recommendation,
            urgency_level=urgency,
            confidence_score=confidence,
            explainability_payload=explainability,
            data_drift_status=drift_status,
            hash_chain=curr_hash
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def check_autonomy(
        db: Session,
        asset: Asset,
        confidence: float,
        drift_status: str
    ) -> Dict[str, Any]:
        """
        2. HUMAN-AI AUTONOMY CONTROL
        Decides if action can be taken automatically.
        """
        policy = asset.autonomy_level
        
        # Hard limits
        if drift_status == "DRIFT_DETECTED":
            return {"allowed": False, "reason": "Data Drift Detected - Human Approval Required", "level": policy}
            
        if policy == AutonomyLevel.ADVISORY:
             return {"allowed": False, "reason": "Asset is in Advisory Mode", "level": policy}
             
        if policy == AutonomyLevel.APPROVAL_REQUIRED:
            return {"allowed": False, "reason": "Policy Requires Approval", "level": policy}
            
        if policy == AutonomyLevel.FULL_AUTONOMY:
            if confidence > 0.85: # Threshold
                return {"allowed": True, "reason": "High Confidence - Autonomy Granted", "level": policy}
            else:
                return {"allowed": False, "reason": "Low Confidence for Autonomy", "level": policy}
                
        return {"allowed": False, "reason": "Unknown Policy", "level": policy}

    @staticmethod
    def calculate_failure_economics(
        db: Session,
        asset: Asset,
        failure_mode_name: str
    ) -> Dict[str, float]:
        """
        3. FAILURE ECONOMICS ENGINE
        6. CROSS-ASSET DEPENDENCY GRAPH (Cost Propagation)
        """
        # Find Cost Model
        cost_config = db.query(CostModel).filter(CostModel.asset_id == asset.id).first()
        if not cost_config:
            # Fallback to defaults (using a mock object or org default)
            cost_config = CostModel(labor_rate_hourly=50, downtime_cost_hourly=500)
            
        # Find Failure Mode
        mode = db.query(FailureMode).filter(
            FailureMode.name == failure_mode_name, 
            FailureMode.asset_type == asset.type
        ).first()
        
        direct_cost = 0.0
        indirect_cost = 0.0
        
        if mode:
            direct_cost = mode.direct_cost_est
            indirect_cost = mode.avg_mttr_hours * cost_config.downtime_cost_hourly
        
        # 6. Propagation (Cross-Asset)
        downstream = db.query(AssetDependency).filter(AssetDependency.upstream_asset_id == asset.id).all()
        cascading_cost = 0.0
        
        for dep in downstream:
            # Simplified: Add 20% of parent downtime cost * weight
            cascading_cost += (indirect_cost * 0.2 * dep.impact_weight)
            
        total_risk = direct_cost + indirect_cost + cascading_cost
        
        return {
            "direct_cost": direct_cost,
            "indirect_cost": indirect_cost,
            "cascading_risk": cascading_cost,
            "total_failure_cost": total_risk
        }

    @staticmethod
    def check_feasibility(
        db: Session,
        action_required: str
    ) -> Dict[str, Any]:
        """
        5. EXECUTION FEASIBILITY ENGINE
        """
        # Heuristic mapping of action -> skills/parts
        # In real system, this is a table.
        required_skill = "General"
        if "Replace" in action_required: required_skill = "Mechanical"
        if "Calibrate" in action_required: required_skill = "Calibration"
        
        # Check Techs
        techs = db.query(TechnicalResource).all()
        available_techs = [t for t in techs if t.is_available and required_skill in (t.skills or [])]
        
        score = 100
        issues = []
        
        if not available_techs:
            score -= 50
            issues.append(f"No technicians with {required_skill} skill available.")
            
        # Check Parts (Mock)
        # If we had parts linked to action
        
        return {
            "feasibility_score": score,
            "is_feasible": score > 0,
            "issues": issues
        }

    @staticmethod
    def process_outcome_feedback(
        db: Session,
        asset_id: UUID,
        action_taken: str,
        was_successful: bool,
        notes: str,
        degradation_modifier: Optional[float] = None
    ):
        """
        4. OUTCOME FEEDBACK & LEARNING LOOP
        9. HUMAN INPUT INTEGRATION
        """
        # Find the last decision for this asset
        last_decision = db.query(DecisionRecord).filter(
            DecisionRecord.asset_id == asset_id
        ).order_by(DecisionRecord.timestamp.desc()).first()
        
        # Update Health State based on human observation
        health = IntelligenceService.get_asset_health_state(db, asset_id)
        
        if degradation_modifier is not None:
             # Store modifier in metadata for future timesteps
             asset = db.query(Asset).filter(Asset.id == asset_id).first()
             if asset:
                 meta = asset.meta_data or {}
                 meta["human_degradation_modifier"] = float(degradation_modifier)
                 asset.meta_data = meta
                 
             # Adjust current confidence if human flags discrepancy
             health.confidence_score *= 0.9 # Temporary decay on disagreement
        
        if last_decision:
            # Update Outcome
            last_decision.outcome = {
                "action_taken": action_taken,
                "success": was_successful,
                "notes": notes,
                "processed_at": datetime.utcnow().isoformat()
            }
            db.commit()
            
            # TRIGGER LEARNING (Step 9 & 10)
            # If AI was wrong (success=False), we flag the model
            if not was_successful:
                print(f"Outcome Feedback: AI Mismatch for Asset {asset_id}. Triggering review.")
                # Logic to lower model confidence or trigger retraining would go here.

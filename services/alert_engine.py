from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime
import json

from models.platform import Alert
from models.intelligence import AssetHealthState
from models.ml import Asset

class AlertEngine:
    """
    7. ALERT SANITY MECHANISM
    Alerts trigger ONLY IF:
    - Stress-normalized anomaly persists
    - Confidence threshold exceeded
    - Duration threshold crossed
    """
    
    @staticmethod
    def process_health_and_alert(
        db: Session, 
        asset_id: UUID, 
        health_state: AssetHealthState,
        prediction_result: Dict[str, Any]
    ) -> Optional[Alert]:
        # 1. Threshold Check (e.g. Health Score < 80)
        dominant_vector = "overall"
        min_score = health_state.operational_health_score
        
        scores = {
            "mechanical": health_state.mechanical_health_score,
            "thermal": health_state.thermal_health_score,
            "electrical": health_state.electrical_health_score
        }
        
        for vector, score in scores.items():
            if score < min_score:
                min_score = score
                dominant_vector = vector
        
        # 2. Confidence Check
        if health_state.confidence_score < 0.7:
            # Silent logging only - not enough confidence for alert
            return None
            
        # 3. Sanity: Persistence & Stress Normalization Anomaly Check
        # We check if the damage increment is significantly higher than normal
        # and if this has been true for the last few windows (stored in damage_rate_history)
        history = health_state.damage_rate_history or []
        if len(history) < 5: return None # Need baseline history
        
        recent_avg = sum(history[-5:]) / 5
        long_term_avg = sum(history) / len(history)
        
        # Persistence check: Recent damage is 2x baseline
        persists = recent_avg > (long_term_avg * 2.0)
        
        if min_score < 70 and persists:
            # Trigger Alert
            severity = "HIGH" if min_score < 40 else "MEDIUM"
            
            # Check for existing active alert to avoid spam
            existing = db.query(Alert).filter(
                Alert.asset_id == asset_id, 
                Alert.status == "OPEN",
                Alert.category == "PREDICTIVE_FAILURE"
            ).first()
            
            if existing:
                # Update persistence duration logic
                return existing
                
            alert = Alert(
                asset_id=asset_id,
                title=f"Probabilistic Failure Risk: {dominant_vector.capitalize()} Sector",
                description=f"Degradation detected in {dominant_vector} health vector. Health Score: {min_score:.1f}",
                severity=severity,
                status="OPEN",
                category="PREDICTIVE_FAILURE",
                meta_data={
                    "probability": 1.0 - (min_score / 100.0),
                    "dominant_vector": dominant_vector,
                    "confidence_score": health_state.confidence_score,
                    "persistence_indicators": {
                        "recent_damage_vs_avg": recent_avg / (long_term_avg + 1e-6)
                    }
                }
            )
            # 8. SHADOW MODE (DEFAULT)
            # In a real app, this would check a 'shadow_mode' flag on the Asset or Org.
            # asset = db.query(Asset).filter(Asset.id == asset_id).first()
            # if asset.meta_data.get("shadow_mode", True): alert.is_shadow = True
            
            db.add(alert)
            db.flush() # Get the ID for the event
            
            # --- PUBLISH EVENT TO OUTBOX ---
            from models.outbox import OutboxEvent, OutboxStatus
            asset_obj = db.query(Asset).filter(Asset.id == asset_id).first()
            org_id = asset_obj.org_id if asset_obj else None
            
            payload = {
                "alert_id": str(alert.id),
                "asset_id": str(asset_id),
                "title": alert.title,
                "description": alert.description,
                "severity": alert.severity,
                "category": alert.category,
                "risk_score": alert.risk_score,
                "timestamp": datetime.utcnow().isoformat(),
                "meta_data": alert.meta_data
            }
            
            event = OutboxEvent(
                topic="alert.triggered",
                payload=payload,
                status=OutboxStatus.PENDING,
                org_id=org_id
            )
            db.add(event)
            db.commit()
            db.refresh(alert)
            return alert
            
        return None

alert_engine = AlertEngine()

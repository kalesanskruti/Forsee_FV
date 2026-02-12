from sqlalchemy.orm import Session
from typing import List, Dict, Any
from uuid import UUID
import numpy as np

from models.ml import ModelMetric, Prediction
from models.intelligence import AssetHealthState

class MonitoringService:
    """
    11. DRIFT & CONFIDENCE MONITORING
    - Prediction distribution shifts
    - Confidence decay
    - Error trend escalation
    """
    
    @staticmethod
    def monitor_model_drift(db: Session, asset_id: UUID, current_prediction: float):
        # 1. Prediction Distribution Shift Check
        # Fetch last 50 predictions for this asset
        history = db.query(Prediction).filter(Prediction.asset_id == asset_id).order_by(Prediction.timestamp.desc()).limit(50).all()
        if len(history) < 20: return # Need base for comparison
        
        # Convert JSON results to flat list of RUL values
        # (Assuming result = {"rul": 150} or similar)
        past_values = [p.result.get("rul", 0) for p in history if isinstance(p.result, dict)]
        
        # Simple KS-test or Z-score check for shift
        mean_past = np.mean(past_values)
        std_past = np.std(past_values)
        
        # If current prediction is 3 sigma away from rolling mean -> POTENTIAL DRIFT
        drift_detected = abs(current_prediction - mean_past) > (3 * std_past) if std_past > 0 else False
        
        if drift_detected:
            # 11. Reduce confidence automatically
            health = db.query(AssetHealthState).filter(AssetHealthState.asset_id == asset_id).first()
            if health:
                health.confidence_score *= 0.8
                db.commit()
                
            # Log as Metric
            metric = ModelMetric(
                metric_name="prediction_drift_zscore",
                metric_value=float(abs(current_prediction - mean_past) / (std_past + 1e-6)),
                timestamp=datetime.utcnow()
            )
            db.add(metric)
            db.commit()
            
        return drift_detected

    @staticmethod
    def monitor_confidence_decay(db: Session, asset_id: UUID):
        """
        Flag retraining if confidence stays low.
        """
        health = db.query(AssetHealthState).filter(AssetHealthState.asset_id == asset_id).first()
        if health and health.confidence_score < 0.4:
            # SURFACE UNCERTAINTY TO UI / Retraining Flag
            return True
        return False

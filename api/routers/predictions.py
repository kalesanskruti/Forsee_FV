from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api import deps
from models.ml import Asset, Prediction
from models.registry import TaskType
from models.user import User, Organization, Role
from models.platform import AuditLog, Alert
from ml.inference import inference_engine as engine
from schemas.prediction import PredictionRequest, PredictionResponse
from services.data_quality import data_quality_service
from core.ratelimit import limiter
from starlette.requests import Request
from datetime import datetime
import json
import logging

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=PredictionResponse)
@limiter.limit("60/minute") 
def predict(
    request: Request,
    *,
    db: Session = Depends(deps.get_db),
    pred_in: PredictionRequest,
    current_user: User = Depends(deps.require_role([Role.ADMIN, Role.ENGINEER, Role.VIEWER])),
) -> Any:
    # 0. Data Quality Check
    errors = data_quality_service.validate_input(pred_in.data)
    if errors:
        raise HTTPException(status_code=400, detail={"message": "Data Quality check failed", "errors": errors})

    # 1. Validate Asset
    asset = db.query(Asset).filter(Asset.id == pred_in.asset_id, Asset.org_id == current_user.org_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # 2. Map Model Type to TaskType
    try:
        task_type_str = pred_in.model_type.upper()
        # Handle simple mapping if frontend sends different strings
        if "RUL" in task_type_str:
            task_type = TaskType.RUL
        elif "PRECURSOR" in task_type_str:
            task_type = TaskType.PRECURSOR
        elif "CLUSTER" in task_type_str:
            task_type = TaskType.CLUSTERING
        elif "DRIFT" in task_type_str:
            task_type = TaskType.DRIFT
        else:
             # Fallback or strict match
             task_type = TaskType(pred_in.model_type.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid model type: {pred_in.model_type}")

    # 3. Predict & Update Health
    try:
        # A. Physical Degradation Processing (ASYNC INGESTION)
        # Convert telemetry + context into degradation estimates via Kafka
        # health_state = IntelligenceService.process_telemetry_window(db, asset.id, pred_in.data)
        
        # Queue ingestion event
        IntelligenceService.ingest_sensor_data(db, asset.id, pred_in.data)
        
        # Fetch CURRENT state (without waiting for this batch to process)
        health_state = IntelligenceService.get_asset_health_state(db, asset.id)
        
        # B. ML Model Inference (If requested or as secondary signal)
        ml_result = engine.predict(task_type, pred_in.data)
        
        # C. Probabilistic RUL (Physically Derived)
        prob_rul = IntelligenceService.get_probabilistic_rul(db, asset.id)
        
        # Combine results
        final_result = {
            "health_vectors": {
                "mechanical": health_state.mechanical_health_score,
                "thermal": health_state.thermal_health_score,
                "electrical": health_state.electrical_health_score,
                "operational": health_state.operational_health_score
            },
            "cumulative_damage": health_state.total_cumulative_damage,
            "rul_estimate": prob_rul,
            "ml_prediction": ml_result,
            "confidence_score": health_state.confidence_score
        }

        # D. Explanation Engine
        try:
            from services.explanation_simulation import ExplanationEngine
            explanation = ExplanationEngine.generate_explanation(
                asset.type, 
                final_result["health_vectors"], 
                ml_result, 
                health_state.confidence_score
            )
            final_result["explanation"] = explanation
        except Exception as e:
            logger.error(f"Explanation Engine Error: {e}")
            
        # E. Drift Monitoring (Background Logic)
        try:
            from services.monitoring_service import MonitoringService
            rul_val = prob_rul.get("mean", 0)
            MonitoringService.monitor_model_drift(db, asset.id, rul_val)
        except Exception as e:
            logger.error(f"Monitoring Service Error: {e}")
        
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction Error: {e}")
        raise HTTPException(status_code=500, detail=f"Intelligence layer failure: {e}")
        
    # 4. Thresholds & Alerts
    try:
        from services.alert_engine import alert_engine
        alert = alert_engine.process_health_and_alert(db, asset.id, health_state, final_result)
        if alert:
            final_result["active_alert"] = {
                "id": str(alert.id),
                "severity": alert.severity,
                "title": alert.title
            }
    except Exception as e:
        logger.error(f"Alert Engine Error: {e}")

    return {"prediction": final_result, "asset_id": str(asset.id)}

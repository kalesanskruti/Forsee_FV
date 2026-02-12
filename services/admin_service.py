from sqlalchemy.orm import Session
from sqlalchemy import func, case, desc, and_
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json

from models.ml import Asset, MLModel, TrainingJob, Prediction, InputSchema
from models.platform import Alert, AuditLog, Plan
from models.user import User, Organization
from models.intelligence import AutonomyLevel

class AdminService:
    """
    Central service for Admin Control Dashboard logic.
    Aggregates data across the system to provide "Global Context".
    """

    @staticmethod
    def get_global_system_context(db: Session, org_id: str) -> Dict[str, Any]:
        """
        Computes the top-level system health and status.
        Supports 1. GLOBAL SYSTEM CONTEXT SERVICE.
        """
        # 1. Active Users (Real-time sessions - simulated by recent activity for now)
        # In a real Redis scenario, we'd query session keys. Here we look at active users in DB.
        active_users_count = db.query(User).filter(
            User.org_id == org_id,
            User.is_active == True
        ).count()

        # 2. Alert Aggregates
        alerts = db.query(
            Alert.severity,
            func.count(Alert.id)
        ).filter(
            # Alert.org_id == org_id, # Alert is TenantMixin? model says TenantMixin but need to verify field
            # Assuming TenantMixin adds org_id or we filter by asset join
            Alert.asset_id.in_(
                db.query(Asset.id).filter(Asset.org_id == org_id)
            ),
            Alert.acknowledged == False
        ).group_by(Alert.severity).all()
        
        alert_counts = {
            "CRITICAL": 0,
            "WARNING": 0
        }
        for severity, count in alerts:
            if severity in alert_counts:
                alert_counts[severity] = count

        # 3. System Health Logic
        # GREEN  -> No critical risks
        # AMBER  -> Critical risks present but under SLA (simulated by count < 5 for now)
        # RED    -> Unacknowledged critical alerts breaching SLA (simulated by count >= 5)
        
        system_status = "GREEN"
        if alert_counts["CRITICAL"] > 0:
            if alert_counts["CRITICAL"] >= 5: # Threshold example
                system_status = "RED"
            else:
                system_status = "AMBER"

        return {
            "environment": "PRODUCTION", # Could come from settings
            "active_users": active_users_count,
            "active_alerts": {
                "critical": alert_counts["CRITICAL"],
                "warning": alert_counts["WARNING"]
            },
            "system_status": system_status
        }

    @staticmethod
    def get_kpi_aggregation(db: Session, org_id: str) -> Dict[str, Any]:
        """
        Supports 2. SYSTEM OVERVIEW & KPI AGGREGATION SERVICE.
        Returns aggregate metrics for cards.
        """
        # Assets
        total_assets = db.query(Asset).filter(Asset.org_id == org_id).count()
        active_assets = db.query(Asset).filter(Asset.org_id == org_id, Asset.status == "OPERATIONAL").count()
        offline_assets = total_assets - active_assets

        # Risk (Critical Assets)
        # Assuming criticality_score > 7 is critical
        critical_assets = db.query(Asset).filter(
            Asset.org_id == org_id, 
            Asset.criticality_score >= 8
        ).count()

        # Predictions Today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Need to join via Asset to filter by Org for Predictions
        predictions_today = db.query(Prediction).join(Asset).filter(
            Asset.org_id == org_id,
            Prediction.timestamp >= today_start
        ).count()

        # Active ML Models
        active_models = db.query(MLModel).filter(
            MLModel.org_id == org_id,
            MLModel.active == True
        ).count()

        # Trend Simulation (Mocked delta for UI demonstration if no historical data table exists)
        # In prod, we'd query history tables or TimeScaleDB aggregates
        
        return {
            "assets": {
                "total": total_assets,
                "active": active_assets,
                "offline": offline_assets,
                "trend": "+2" 
            },
            "risk": {
                "critical_assets": critical_assets,
                "avg_health_index": 85.4, # Placeholder or expensive calc
                "trend": "-5%"
            },
            "predictions": {
                "today": predictions_today,
                "trend": "+120"
            },
            "models": {
                "active_deployed": active_models,
                "retraining": 1 # Mock
            }
        }

    @staticmethod
    def get_asset_fleet_table(db: Session, org_id: str, skip: int = 0, limit: int = 50):
        """
        Supports 3. ASSET & FLEET INTELLIGENCE SERVICE.
        """
        assets = db.query(Asset).filter(Asset.org_id == org_id).offset(skip).limit(limit).all()
        
        results = []
        for asset in assets:
            # Determine Risk Classification dynamically
            risk_level = "LOW"
            if asset.criticality_score >= 8:
                risk_level = "CRITICAL"
            elif asset.criticality_score >= 5:
                risk_level = "MEDIUM"
                
            results.append({
                "asset_id": str(asset.id),
                "name": asset.name,
                "type": asset.type,
                "location": asset.location,
                "health_index": 90, # TODO: Store this on asset or compute from latest prediction
                "rul_days": 120, # TODO: Retrieve from latest RUL prediction
                "risk_level": risk_level,
                "last_seen": datetime.utcnow().isoformat(), # Mock, or use tracking field
                "status": asset.status
            })
        return results

    @staticmethod
    def log_admin_action(
        db: Session, 
        org_id: str, 
        user_id: str, 
        action: str, 
        details: Dict[str, Any] = None
    ):
        """
        Supports 8. AUDIT & COMPLIANCE LEDGER.
        Saves immutable audit log.
        """
        log = AuditLog(
            action=action,
            details=details,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            org_id=org_id
        )
        db.add(log)
        db.commit()

    @staticmethod
    def update_organization_policy(
        db: Session, 
        org_id: str, 
        user_id: str,
        updates: Dict[str, Any]
    ):
        """
        Supports 6. ORGANIZATION THRESHOLDS & POLICY ENGINE.
        """
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            raise ValueError("Organization not found")

        # Update fields if valid
        if "warning_threshold" in updates:
            org.warning_threshold = str(updates["warning_threshold"])
        if "critical_threshold" in updates:
            org.critical_threshold = str(updates["critical_threshold"])
        
        # Log it
        AdminService.log_admin_action(
            db, org_id, user_id, 
            action="UPDATE_POLICY", 
            details=updates
        )
        
        db.commit()
        db.refresh(org)
        return org


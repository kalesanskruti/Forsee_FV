import asyncio
import json
import logging
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session

from models.platform import NotificationPreference, NotificationLog, Alert, EscalationPolicy
from db.session import SessionLocal
from services.cache import CacheService
from notification_service.websocket_manager import ws_manager
from notification_service.delivery_engine import DeliveryEngine

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notification_service")

app = FastAPI(title="FORSEE Notification Service")

# --- Redis Keys ---
def get_cooldown_key(tenant_id: str, asset_id: str, event_type: str) -> str:
    return f"tenant:{tenant_id}:asset:{asset_id}:cooldown:{event_type}"

# --- Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Kafka Consumer Loop (Simulated) ---
async def kafka_consumer_loop():
    """
    Simulated background Kafka consumer.
    """
    logger.info("Starting Notification Kafka Consumer...")
    while True:
        # In production, this would poll Kafka topics
        await asyncio.sleep(60)
        pass

async def escalation_monitor_loop():
    """
    Periodically check for OPEN alerts breaching escalation policy window.
    """
    logger.info("Starting Alert Escalation Monitor...")
    while True:
        db = SessionLocal()
        try:
            # 1. Fetch OPEN alerts
            open_alerts = db.query(Alert).filter(Alert.status == "OPEN").all()
            
            for alert in open_alerts:
                # 2. Find Policy
                policy = db.query(EscalationPolicy).filter(
                    EscalationPolicy.org_id == alert.org_id,
                    EscalationPolicy.alert_category == alert.category
                ).first()
                
                if not policy: continue
                
                # 3. Check Steps
                for step in policy.steps:
                    delay_mins = step.get("delay_minutes", 0)
                    trigger_time = alert.created_at + timedelta(minutes=delay_mins)
                    
                    if datetime.utcnow() > trigger_time:
                        # Escalation Condition Met
                        # Topic: alert.escalated
                        logger.warning(f"Escalating Alert {alert.id} for Tenant {alert.org_id}")
                        
                        # In real app, we would publish 'alert.escalated' to Kafka
                        # For now, we process as a high-priority notification
                        await process_event(db, "alert.escalated", {
                            "alert_id": str(alert.id),
                            "asset_id": str(alert.asset_id),
                            "severity": alert.severity,
                            "escalation_step": step.get("action")
                        }, alert.org_id)
                        
            db.commit()
        except Exception as e:
            logger.error(f"Escalation Monitor Error: {e}")
        finally:
            db.close()
            
        await asyncio.sleep(300) # Check every 5 minutes

async def process_event(db: Session, topic: str, payload: Dict[str, Any], org_id: UUID):
    """
    Core Dispatch Logic: Preference Check -> Rate Limit -> Delivery
    """
    tenant_id = str(org_id)
    asset_id = payload.get("asset_id", "unknown")
    
    # 1. Fetch Tenant Preferences
    pref = db.query(NotificationPreference).filter(NotificationPreference.org_id == org_id).first()
    if not pref:
        pref = NotificationPreference(org_id=org_id)
    
    # 2. Rate Limiting / Cooldown
    if CacheService.get_json(tenant_id, asset_id, f"cooldown:{topic}"):
        logger.info(f"Notification suppressed due to cooldown: {asset_id}:{topic}")
        return

    # 3. Delivery Logic
    
    # A. WebSocket
    if pref.websocket_enabled:
        await ws_manager.broadcast_to_tenant(tenant_id, {
            "topic": topic,
            "payload": payload,
            "server_time": datetime.utcnow().isoformat()
        })

    # B. Email
    if pref.email_enabled and topic in ["alert.triggered", "device.health.reminder"]:
        subject = f"FORSEE Alert: {payload.get('title', topic)}"
        body = f"Event: {topic}\nAsset: {asset_id}\nPayload: {json.dumps(payload)}"
        await DeliveryEngine.send_email_async(tenant_id, "admin@tenant.com", subject, body, asset_id)

    # C. Webhook
    if pref.webhook_enabled and pref.webhook_url:
        await DeliveryEngine.trigger_webhook_async(
            tenant_id, 
            pref.webhook_url, 
            pref.webhook_secret or "secret", 
            payload
        )

    # 4. Set Cooldown in Redis (5 minutes)
    CacheService.set_json(tenant_id, asset_id, f"cooldown:{topic}", {"active": True}, ttl_seconds=300)

    # 5. Log Attempt
    log = NotificationLog(
        org_id=org_id,
        asset_id=UUID(asset_id) if asset_id != "unknown" else None,
        channel="ALL",
        recipient="MULTI",
        status="PROCESSED",
        timestamp=datetime.utcnow()
    )
    db.add(log)
    db.commit()

# --- WebSocket Endpoint ---

@app.websocket("/ws/{tenant_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, tenant_id: str, user_id: str):
    try:
        await ws_manager.connect(websocket, tenant_id, user_id)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, tenant_id, user_id)
    except Exception as e:
        logger.error(f"WS Error: {e}")
        ws_manager.disconnect(websocket, tenant_id, user_id)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(kafka_consumer_loop())
    asyncio.create_task(escalation_monitor_loop())

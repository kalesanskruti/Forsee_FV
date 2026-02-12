import uuid
from uuid import UUID
from datetime import datetime
from core import context
from services.cache import CacheService
from models.outbox import OutboxEvent, OutboxStatus
from services.intelligence import IntelligenceService
from services.inspection_service import InspectionService
from unittest.mock import MagicMock

def verify_multi_tenancy():
    print("--- Verifying Multi-Tenant Isolation ---")
    
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    asset_id = uuid.uuid4()
    
    # 1. Cache Isolation
    print("\n1. Testing Cache Isolation...")
    context.set_context(context.RequestContext(org_id=tenant_a))
    try:
        CacheService.set_json(None, str(asset_id), "test", {"data": "tenant_a_data"})
        print("✅ Set data for Tenant A (using context)")
        
        # Switch Context to Tenant B
        context.set_context(context.RequestContext(org_id=tenant_b))
        data_b = CacheService.get_json(None, str(asset_id), "test")
        if data_b is None:
            print("✅ Tenant B cannot see Tenant A data (Cache Miss as expected)")
        else:
            print("❌ SECURITY BREACH: Tenant B saw Tenant A data!")
            
    except Exception as e:
        print(f"❌ Cache Test Error: {e}")

    # 2. Event Isolation (Outbox)
    print("\n2. Testing Outbox Event Isolation...")
    db = MagicMock()
    
    # Ingest for Tenant A
    context.set_context(context.RequestContext(org_id=tenant_a))
    IntelligenceService.ingest_sensor_data(db, asset_id, {"temp": 100})
    
    # Check what was added to DB
    event = db.add.call_args[0][0]
    if event.org_id == tenant_a and event.payload.get("tenant_id") == str(tenant_a):
        print("✅ OutboxEvent correctly tagged with Tenant A org_id")
    else:
        print(f"❌ OutboxEvent Tagging Failed: {event.org_id} != {tenant_a}")

    # 3. Fail-Fast on missing tenant
    print("\n3. Testing Fail-Fast on missing context...")
    context.set_context(None)
    try:
        CacheService.get_json(None, str(asset_id), "test")
        print("❌ FAILED: Cache allowed operation without tenant context!")
    except ValueError as e:
        print(f"✅ Correctly failed: {e}")

    print("\n--- Multi-Tenant Verification Complete ---")

if __name__ == "__main__":
    verify_multi_tenancy()

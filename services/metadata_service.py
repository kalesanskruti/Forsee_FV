from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from typing import Dict, Any, Optional

from models.metadata import AssetMetadata, AssetOperationProfile, AssetShiftSchedule, AssetEnvironmentProfile
from models.outbox import OutboxEvent, OutboxStatus
from models.platform import AuditLog
from schemas.metadata import AssetMetadataCreate, AssetMetadataUpdate
from core.events import MetadataUpdatedEvent
from services.cache import CacheService

class MetadataService:
    @staticmethod
    def get_metadata(db: Session, asset_id: UUID) -> Optional[AssetMetadata]:
        """
        Check Cache -> DB.
        """
        # Fetch asset to get org_id for cache key
        from models.ml import Asset
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset: return None
        
        tenant_id = str(asset.org_id)
        
        # 1. Try Cache
        cached = CacheService.get_json(tenant_id, str(asset_id), "metadata")
        if cached:
            return AssetMetadata(**cached) # This might need ORM-to-dict conversion if we want pure ORM back
            
        # 2. DB Query
        metadata = db.query(AssetMetadata).filter(AssetMetadata.asset_id == asset_id).first()
        
        # 3. Populate Cache
        if metadata:
            # Note: Serializing ORM objects directly is hard, usually we use schemas or dicts
            # For simplicity, let's assume we store a dict represention
            meta_dict = {
                "asset_id": str(metadata.asset_id),
                "version": metadata.version,
                "criticality_level": metadata.criticality_level
                # add more fields as needed or use schema.dict()
            }
            CacheService.set_json(tenant_id, str(asset_id), "metadata", meta_dict, ttl_seconds=86400)
            
        return metadata

    @staticmethod
    def create_or_update_metadata(db: Session, asset_id: UUID, schema: AssetMetadataCreate) -> AssetMetadata:
        """
        Create or Update metadata.
        Increments version and publishes 'metadata.updated' event.
        """
        existing = MetadataService.get_metadata(db, asset_id)
        
        if existing:
            # Update Logic
            existing.version += 1
            change_type = "UPDATED"
            
            # Static fields
            if schema.asset_type: existing.asset_type = schema.asset_type
            if schema.industry_type: existing.industry_type = schema.industry_type
            if schema.installation_date: existing.installation_date = schema.installation_date
            if schema.expected_design_life_hours: existing.expected_design_life_hours = schema.expected_design_life_hours
            existing.criticality_level = schema.criticality_level
            existing.failure_impact_score = schema.failure_impact_score
            
            # Sub-profiles (Cascade update or replace)
            # Simplest approach: Update fields if exists, else create
            if schema.operation_profile:
                if existing.operation_profile:
                    for k, v in schema.operation_profile.dict(exclude_unset=True).items():
                        setattr(existing.operation_profile, k, v)
                else:
                    existing.operation_profile = AssetOperationProfile(asset_metadata_id=existing.id, **schema.operation_profile.dict())
            
            if schema.shift_schedule:
                if existing.shift_schedule:
                     for k, v in schema.shift_schedule.dict(exclude_unset=True).items():
                        setattr(existing.shift_schedule, k, v)
                else:
                    existing.shift_schedule = AssetShiftSchedule(asset_metadata_id=existing.id, **schema.shift_schedule.dict())

            if schema.environment_profile:
                if existing.environment_profile:
                     for k, v in schema.environment_profile.dict(exclude_unset=True).items():
                        setattr(existing.environment_profile, k, v)
                else:
                    existing.environment_profile = AssetEnvironmentProfile(asset_metadata_id=existing.id, **schema.environment_profile.dict())

            metadata_obj = existing
        else:
            # Create Logic
            change_type = "CREATED"
            metadata_obj = AssetMetadata(
                asset_id=asset_id,
                asset_type=schema.asset_type,
                industry_type=schema.industry_type,
                installation_date=schema.installation_date,
                expected_design_life_hours=schema.expected_design_life_hours,
                criticality_level=schema.criticality_level,
                failure_impact_score=schema.failure_impact_score,
                version=1
            )
            db.add(metadata_obj)
            db.flush() # Get ID
            
            if schema.operation_profile:
                op = AssetOperationProfile(asset_metadata_id=metadata_obj.id, **schema.operation_profile.dict())
                db.add(op)
            if schema.shift_schedule:
                shift = AssetShiftSchedule(asset_metadata_id=metadata_obj.id, **schema.shift_schedule.dict())
                db.add(shift)
            if schema.environment_profile:
                env = AssetEnvironmentProfile(asset_metadata_id=metadata_obj.id, **schema.environment_profile.dict())
                db.add(env)
        
        # Publish Event
        event_payload = {
            "event_id": str(datetime.utcnow().timestamp()),
            "schema_version": "1.0",
            "timestamp": datetime.utcnow().isoformat(),
            "asset_id": str(asset_id),
            "metadata_version": metadata_obj.version,
            "change_type": change_type
        }
        
        outbox = OutboxEvent(
            topic="metadata.updated",
            payload=event_payload,
            status=OutboxStatus.PENDING
        )
        db.add(outbox)
        
        # Log Audit
        from core import context
        ctx = context.get_context()
        audit = AuditLog(
            action=f"METADATA_{change_type}",
            details={"asset_id": str(asset_id), "version": metadata_obj.version},
            timestamp=datetime.utcnow(),
            user_id=ctx.user_id if ctx else None,
            org_id=ctx.org_id if ctx else None
        )
        db.add(audit)
        
        db.commit()
        db.refresh(metadata_obj)
        
        # Invalidate Cache
        from models.ml import Asset
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if asset:
            CacheService.invalidate(str(asset.org_id), str(asset_id), "metadata")
            
        return metadata_obj

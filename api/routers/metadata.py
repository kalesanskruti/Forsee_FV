from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from uuid import UUID

from api import deps
from models.user import User, Role
from models.metadata import AssetMetadata
from schemas.metadata import AssetMetadataCreate, AssetMetadataResponse
from services.metadata_service import MetadataService

router = APIRouter()

@router.get("/{asset_id}", response_model=AssetMetadataResponse)
def get_asset_metadata(
    *,
    db: Session = Depends(deps.get_db),
    asset_id: UUID,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get metadata for an asset.
    """
    metadata = MetadataService.get_metadata(db, asset_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Metadata not found for this asset")
    return metadata

@router.put("/{asset_id}", response_model=AssetMetadataResponse)
def upser_asset_metadata(
    *,
    db: Session = Depends(deps.get_db),
    asset_id: UUID,
    metadata_in: AssetMetadataCreate,
    current_user: User = Depends(deps.require_role([Role.ENGINEER, Role.ADMIN])),
) -> Any:
    """
    Create or Update asset metadata.
    Increments version and triggers 'metadata.updated' event.
    """
    # Ensure asset_id in path matches body or override
    metadata_in.asset_id = asset_id 
    
    try:
        metadata = MetadataService.create_or_update_metadata(db, asset_id, metadata_in)
        return metadata
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

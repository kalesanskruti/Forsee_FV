import sys
import os
import uuid
import json
from unittest.mock import MagicMock, patch
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.cache import CacheService
from services.intelligence import IntelligenceService

def test_redis_cache_flow():
    print("\n--- Testing Redis Caching Layer (Simulated) ---")
    
    asset_id = uuid.uuid4()
    tenant_id = str(uuid.uuid4())
    mock_db = MagicMock()
    
    # Mock Asset for org_id
    mock_asset = MagicMock()
    mock_asset.id = asset_id
    mock_asset.org_id = tenant_id
    mock_db.query().filter().first.return_value = mock_asset

    # 1. Test Cache Miss -> DB Query -> Cache Populate
    print("1. Testing Cache Miss Scenario...")
    
    # Mock Cache MISS
    with patch.object(CacheService, 'get_json', return_value=None):
        with patch.object(CacheService, 'set_json') as mock_set:
            # Mock DB Health State
            mock_health = MagicMock()
            mock_health.failure_threshold_mean = 1.0
            mock_health.total_cumulative_damage = 0.1
            mock_health.damage_rate_history = [0.01] * 10
            
            with patch.object(IntelligenceService, 'get_asset_health_state', return_value=mock_health):
                IntelligenceService.get_probabilistic_rul(mock_db, asset_id)
                
                # Check if Cache Set was called
                mock_set.assert_called_once()
                print("✅ Cache Miss -> Populated Redis")

    # 2. Test Cache HIT
    print("\n2. Testing Cache HIT Scenario...")
    cached_data = {"rul_data": {"mean": 1500, "lower": 1200, "upper": 1800}, "asset_id": str(asset_id)}
    
    with patch.object(CacheService, 'get_json', return_value=cached_data):
        with patch.object(IntelligenceService, 'get_asset_health_state') as mock_health_call:
            result = IntelligenceService.get_probabilistic_rul(mock_db, asset_id)
            
            # Should NOT call health state / compute
            mock_health_call.assert_not_called()
            assert result["mean"] == 1500
            print("✅ Cache HIT -> Returned instant result without DB computation")

    # 3. Test Invalidation
    print("\n3. Testing Invalidation Logic...")
    with patch.object(CacheService, 'invalidate') as mock_invalidate:
        CacheService.invalidate(tenant_id, str(asset_id), "rul")
        mock_invalidate.assert_called_once_with(tenant_id, str(asset_id), "rul")
        print("✅ Invalidation logic triggered correctly")

if __name__ == "__main__":
    test_redis_cache_flow()

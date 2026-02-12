
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ml.models.degradation_model import DegradationModel, OperatingRegime

def test_environmental_damage():
    print("\n--- Testing Environmental Damage ---")
    data = {"ambient_temp": 25.0, "humidity": 50.0}
    damage_1h = DegradationModel.compute_environmental_damage(data, dt_hours=1.0)
    print(f"Base Damage (25C, 50%H, 1h): {damage_1h}")
    
    # Test Temp Scaling (Arrhenius: +10C -> ~2x)
    data_hot = {"ambient_temp": 35.0, "humidity": 50.0}
    damage_hot = DegradationModel.compute_environmental_damage(data_hot, dt_hours=1.0)
    print(f"Hot Damage (35C): {damage_hot}")
    
    ratio = damage_hot / damage_1h
    print(f"Ratio (should be ~2.0): {ratio:.2f}")
    assert 1.9 < ratio < 2.1, f"Temp scaling failed: {ratio}"

def test_usage_damage_regimes():
    print("\n--- Testing Usage Damage Regimes ---")
    meta = {"typical_load": 1.0, "rated_temp": 100.0}
    
    # IDLE
    idle_data = {"rpm": 0, "load": 0, "vibration": 0, "current": 0}
    regime = DegradationModel.detect_regime(idle_data, meta)
    assert regime == OperatingRegime.IDLE
    mech, therm, elec, strain = DegradationModel.compute_usage_damage(idle_data, meta, regime)
    total = mech + therm + elec + strain
    print(f"IDLE Total Usage Damage: {total}")
    assert total == 0.0
    
    # NORMAL
    normal_data = {"rpm": 1500, "load": 0.5, "vibration": 0.1, "current": 10, "temperature": 60}
    regime = DegradationModel.detect_regime(normal_data, meta)
    assert regime == OperatingRegime.RUN_NORMAL, f"Expected RUN_NORMAL, got {regime}"
    mech_n, _, _, _ = DegradationModel.compute_usage_damage(normal_data, meta, regime)
    print(f"NORMAL Mechanical Damage: {mech_n}")
    
    # HIGH STESS
    high_data = {"rpm": 2000, "load": 0.9, "vibration": 0.5, "current": 20, "temperature": 90}
    regime = DegradationModel.detect_regime(high_data, meta)
    assert regime == OperatingRegime.RUN_HIGH_STRESS, f"Expected HIGH_STRESS, got {regime}"
    mech_h, _, _, _ = DegradationModel.compute_usage_damage(high_data, meta, regime)
    print(f"HIGH STRESS Mechanical Damage: {mech_h}")
    
    assert mech_h > mech_n, "High stress should cause more damage"

def test_shift_logic():
    print("\n--- Testing Shift Logic ---")
    meta = {"typical_load": 1.0}
    data = {"rpm": 1500, "load": 0.5, "vibration": 0.2, "current": 10, "temperature": 60}
    
    # In Shift
    context = {"is_in_shift": True, "dt_hours": 1.0}
    res_in = DegradationModel.compute_damage_proxy(data, meta, context)
    print(f"In-Shift Total: {res_in.total}")
    
    # Out of Shift (Same operation)
    context_out = {"is_in_shift": False, "dt_hours": 1.0}
    res_out = DegradationModel.compute_damage_proxy(data, meta, context_out)
    print(f"Out-of-Shift Total: {res_out.total}")
    
    # Expect penalty (roughly 2x usage damage, env damage constant)
    # Total = Usage + Env
    # Out = Usage*2 + Env
    assert res_out.total > res_in.total, "Out of shift should be higher"
    assert res_out.mechanical > res_in.mechanical, "Mechanical component should be penalized"
    
def test_rul_uncertainty():
    print("\n--- Testing RUL Uncertainty ---")
    capacity = 0.5
    
    # Stable history
    history_stable = [0.001, 0.0011, 0.0009, 0.001, 0.001]
    res_stable = DegradationModel.estimate_rul_bounds(capacity, history_stable)
    print(f"Stable RUL Confidence: {res_stable['confidence']:.2f}, Volatility: {res_stable['volatility_index']:.4f}")
    
    # Volatile history
    history_volatile = [0.001, 0.005, 0.0001, 0.008, 0.002]
    res_volatile = DegradationModel.estimate_rul_bounds(capacity, history_volatile)
    print(f"Volatile RUL Confidence: {res_volatile['confidence']:.2f}, Volatility: {res_volatile['volatility_index']:.4f}")
    
    assert res_stable['confidence'] > res_volatile['confidence'], "Stable history should have higher confidence"

if __name__ == "__main__":
    test_environmental_damage()
    test_usage_damage_regimes()
    test_shift_logic()
    test_rul_uncertainty()
    print("\nALL TESTS PASSED")

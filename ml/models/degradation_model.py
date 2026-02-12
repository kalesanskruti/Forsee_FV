import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class OperatingRegime(str, Enum):
    IDLE = "IDLE"
    RUN_NORMAL = "RUN_NORMAL"
    RUN_HIGH_STRESS = "RUN_HIGH_STRESS"
    TRANSIENT = "TRANSIENT"
    FAULT = "FAULT"

@dataclass
class DamageIncrement:
    mechanical: float
    thermal: float
    electrical: float
    strain: float
    environmental: float
    total: float
    regime: OperatingRegime

class DegradationModel:
    """
    Physically grounded logic for converting telemetry into damage.
    Core Philosophy: Use stress normalization and physical proxies.
    Distinguishes between Usage Damage (Operating Context) and Environmental Damage (Always Active).
    """

    @staticmethod
    def detect_regime(sensor_data: Dict[str, float], operating_metadata: Dict[str, Any]) -> OperatingRegime:
        """
        Classify current operation into a regime for stress weighting.
        """
        rpm = sensor_data.get("rpm", 0)
        load = sensor_data.get("load", 0)
        vibration = sensor_data.get("vibration", 0)
        
        # Thresholds (Should be loaded from metadata in production)
        idle_rpm = operating_metadata.get("idle_rpm_threshold", 100)
        high_load = operating_metadata.get("high_load_threshold", 0.8)
        fault_vib = operating_metadata.get("fault_vibration_threshold", 0.8)
        
        if rpm < idle_rpm:
            return OperatingRegime.IDLE
        elif vibration > fault_vib:
            return OperatingRegime.FAULT
        elif load > high_load:
            return OperatingRegime.RUN_HIGH_STRESS
        else:
            return OperatingRegime.RUN_NORMAL

    @staticmethod
    def compute_environmental_damage(
        sensor_data: Dict[str, float],
        dt_hours: float = 1.0
    ) -> float:
        """
        Damage that happens even when machine is off (Corrosion, shelf-aging).
        Scales with Ambient Temperature and Humidity.
        """
        ambient_temp = sensor_data.get("ambient_temp", 25.0)
        humidity = sensor_data.get("humidity", 50.0)
        
        # Arrhenius-style aging factor
        # Baseline: 25C -> 1.0x rate
        # Every 10C rise doubles the aging rate (approximation)
        temp_factor = 2 ** ((ambient_temp - 25) / 10.0)
        
        # Humidity factor (linear proxy for corrosion)
        humidity_factor = (humidity / 50.0)
        
        # Base environmental degradation rate (very low)
        base_rate = 1e-7 
        
        return base_rate * temp_factor * humidity_factor * dt_hours

    @staticmethod
    def compute_usage_damage(
        sensor_data: Dict[str, float],
        operating_metadata: Dict[str, Any],
        regime: OperatingRegime
    ) -> Tuple[float, float, float, float]:
        """
        Damage due to physical operation.
        Returns (mechanical, thermal, electrical, strain)
        """
        if regime == OperatingRegime.IDLE:
            return 0.0, 0.0, 0.0, 0.0
            
        # Regime Multipliers
        multipliers = {
            OperatingRegime.RUN_NORMAL: 1.0,
            OperatingRegime.RUN_HIGH_STRESS: 1.5,
            OperatingRegime.TRANSIENT: 1.2,
            OperatingRegime.FAULT: 5.0
        }
        regime_factor = multipliers.get(regime, 1.0)
        
        load = sensor_data.get("load", 1.0)
        
        # 1. Mechanical Fatigue (Vibration Energy normalized by Load)
        raw_vibration = sensor_data.get("vibration", 0.0)
        mech_stress = raw_vibration / (load + 1e-6)
        mech_damage = (mech_stress ** 2) * 1e-5 * regime_factor

        # 2. Thermal Aging (Process Temperature)
        temp = sensor_data.get("temperature", 60.0)
        # Non-linear: (Temp / Rated)^4 is common for insulation life
        rated_temp = operating_metadata.get("rated_temp", 100.0)
        thermal_stress = max(0, temp / rated_temp)
        thermal_damage = (thermal_stress ** 4) * 1e-5 * regime_factor

        # 3. Electrical Stress
        current = sensor_data.get("current", 10.0)
        rpm = sensor_data.get("rpm", 1500)
        elec_stress = current / (rpm + 1e-6)
        elec_damage = (elec_stress ** 2) * 1e-5 * regime_factor

        # 4. Mechanical Strain (Torque/Load)
        torque = sensor_data.get("torque", 50.0)
        strain_damage = (torque * load) * 1e-6 * regime_factor
        
        return mech_damage, thermal_damage, elec_damage, strain_damage

    @staticmethod
    def compute_damage_proxy(
        sensor_data: Dict[str, float],
        operating_metadata: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> DamageIncrement:
        """
        Main entry point for calculating damage increment.
        Supports Shift_Modifier from the Shift Violation Engine.
        """
        if context is None: context = {}
        
        # Time delta (assume 1 hour if not specified for rate calc)
        dt_hours = context.get("dt_hours", 1.0)
        shift_modifier = context.get("shift_modifier", 1.0)
        
        # 1. Detect Regime
        regime = DegradationModel.detect_regime(sensor_data, operating_metadata)
        
        # 2. Compute Environmental Damage (Always active)
        env_damage = DegradationModel.compute_environmental_damage(sensor_data, dt_hours)
        
        # 3. Compute Usage Damage
        mech, therm, elec, strain = DegradationModel.compute_usage_damage(sensor_data, operating_metadata, regime)
        
        # 4. Apply Operating Context Logic (Shift Enforcement)
        # Multiplier bounded (max 1.3 recommended, enforced in ShiftService)
        mech *= shift_modifier
        therm *= shift_modifier
        elec *= shift_modifier
        strain *= shift_modifier
        
        total = mech + therm + elec + strain + env_damage
        
        return DamageIncrement(
            mechanical=mech,
            thermal=therm,
            electrical=elec,
            strain=strain,
            environmental=env_damage,
            total=total,
            regime=regime
        )

    @staticmethod
    def estimate_rul_bounds(
        remaining_capacity: float,
        damage_rate_history: List[float],
        confidence_level: float = 0.95,
        shift_violation_penalty: float = 0.0
    ) -> Dict[str, Any]:
        """
        RUL = Remaining_Capacity / Expected_Damage_Rate
        shift_violation_penalty: 0.0 to 1.0 factor to reduce confidence.
        """
        if not damage_rate_history:
            expected_rate = 0.001 
            std_dev = 0.0001
        else:
            expected_rate = np.mean(damage_rate_history)
            std_dev = np.std(damage_rate_history)
            
        expected_rate = max(expected_rate, 1e-9)
        rul_mean = remaining_capacity / expected_rate
        
        cv = std_dev / expected_rate
        uncertainty_factor = (1 + cv) 
        
        lower_bound = rul_mean / uncertainty_factor
        upper_bound = rul_mean * uncertainty_factor
        
        # Confidence Score (0-100%)
        base_confidence = 1.0
        if len(damage_rate_history) < 10: base_confidence *= 0.5
        volatility_penalty = min(0.5, cv)
        
        # Apply Shift Violation Penalty (Gradual decay)
        final_confidence = max(0.1, base_confidence - volatility_penalty - shift_violation_penalty)
        
        return {
            "mean": float(rul_mean),
            "lower_bound": float(lower_bound),
            "upper_bound": float(upper_bound),
            "confidence": float(final_confidence),
            "volatility_index": float(cv)
        }

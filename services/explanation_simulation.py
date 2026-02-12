from typing import Dict, Any, List
from datetime import datetime

class ExplanationEngine:
    """
    10. EXPLANATION ENGINE
    Explanations must:
    - Be correlation-framed, not causal
    - Be confidence-scored
    - Reference historical patterns
    """
    
    @staticmethod
    def generate_explanation(
        asset_type: str,
        health_vectors: Dict[str, float],
        prediction_result: Dict[str, Any],
        confidence_score: float
    ) -> Dict[str, Any]:
        # Identify dominant issue
        weakest_vector = min(health_vectors, key=health_vectors.get)
        score = health_vectors[weakest_vector]
        
        # Correlation-framed phrasing
        evidence = f"Historical patterns link {weakest_vector} stress levels in {asset_type} assets with the currently observed sensor trend deltas."
        
        explanation = {
            "primary_indicator": weakest_vector,
            "confidence_score": confidence_score,
            "narrative": f"The system has detected a high correlation between {weakest_vector} degradation pathways and current telemetry. This is not strictly causal but follows established failure precursors.",
            "evidence": evidence,
            "timelines": [
                {"event": f"{weakest_vector} stress normalized spike", "timestamp": datetime.utcnow().isoformat()}
            ],
            "historical_cases_count": 12 # Mock: reference to historical db
        }
        
        return explanation

class SimulationEngineRules:
    """
    12. SIMULATION ENGINE RULES
    Simulations must:
    - Operate on degradation capacity
    - Respect operating profile assumptions
    - Output reliability score
    """
    
    @staticmethod
    def run_regime_simulation(
        current_health_state: Dict[str, Any],
        scenario_multiplier: float,
        duration_hours: int
    ) -> Dict[str, Any]:
        # Operates on degradation capacity
        current_damage = current_health_state.get("total_cumulative_damage", 0.0)
        threshold = current_health_state.get("failure_threshold_mean", 1.0)
        capacity = threshold - current_damage
        
        # Expected daily damage rate
        history = current_health_state.get("damage_rate_history", [])
        avg_rate = sum(history[-10:]) / 10 if history else 0.001
        
        # Simulate under new regime
        sim_damage = avg_rate * scenario_multiplier * (duration_hours / 24.0)
        projected_capacity = capacity - sim_damage
        
        reliability_score = max(0, min(1.0, projected_capacity / threshold))
        
        return {
            "reliability_score": reliability_score,
            "projected_degradation": sim_damage,
            "remaining_capacity": projected_capacity,
            "assumptions_used": f"Load multiplier {scenario_multiplier}x applied to historical baseline.",
            "confidence_level": 0.85 if duration_hours < 720 else 0.6 # Decay on long term extrapolation
        }

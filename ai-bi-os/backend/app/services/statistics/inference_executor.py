import logging
from typing import Dict, Any, List
import time

from app.services.statistics.hypothesis_engine import hypothesis_engine
from app.services.statistics.confidence_engine import confidence_engine
from app.services.statistics.distribution_engine import distribution_engine
from app.services.statistics.sampling_engine import sampling_engine
from app.services.statistics.probability_engine import probability_engine

logger = logging.getLogger("InferenceExecutor")

class InferenceExecutor:
    """Orchestrates execution across all statistical engines."""
    
    def execute_plan(self, population_size: int, hypothesis_plan: List[Dict[str, Any]], 
                     metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        
        start_time = time.time()
        time.sleep(0.3)
        
        # 1. Hypotheses
        h_results = hypothesis_engine.execute(hypothesis_plan)
        
        # 2. Confidence Intervals
        c_results = confidence_engine.calculate_intervals(metrics)
        
        # 3. Distributions
        d_results = distribution_engine.fit_distributions(metrics)
        
        # 4. Sampling Profile
        s_result = sampling_engine.determine_strategy(population_size)
        
        # 5. Probabilities
        p_results = probability_engine.calculate_probabilities(h_results)
        
        # 6. Business Interpretations
        i_results = []
        for h in h_results:
            sig_level = "SIGNIFICANT" if h["reject_null_hypothesis"] else "NOT_SIGNIFICANT"
            if h["p_value"] < 0.01: sig_level = "HIGHLY_SIGNIFICANT"
            
            i_results.append({
                "business_metric": h["target_metric"],
                "statistical_method": h["test_name"],
                "significance_level": sig_level,
                "confidence_description": f"{1 - h['alpha']:.0%} Confidence",
                "risk_level": "LOW" if sig_level != "NOT_SIGNIFICANT" else "HIGH",
                "supporting_statistics": {"p_value": h["p_value"], "t_stat": h["test_statistic"]}
            })
            
        return {
            "hypothesis_results": h_results,
            "confidence_results": c_results,
            "distribution_results": d_results,
            "sampling_profile": s_result,
            "probability_results": p_results,
            "inference_results": i_results,
            "execution_time_ms": (time.time() - start_time) * 1000
        }

inference_executor = InferenceExecutor()

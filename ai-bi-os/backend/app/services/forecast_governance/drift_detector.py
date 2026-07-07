import numpy as np
from scipy import stats
from typing import List, Dict, Any

class DriftDetector:
    def __init__(self, p_value_threshold: float = 0.05):
        self.p_value_threshold = p_value_threshold

    def detect_drift(self, reference_data: List[float], current_data: List[float]) -> Dict[str, Any]:
        """
        Detect various types of drift using statistical tests.
        In a real-world scenario, you might pass separate datasets for feature drift vs prediction drift.
        Here we assume `reference_data` and `current_data` could be predictions or residuals to detect prediction drift.
        """
        if not reference_data or not current_data:
            return {
                "data_drift_detected": False,
                "feature_drift_detected": False,
                "prediction_drift_detected": False,
                "concept_drift_detected": False,
                "performance_drift_detected": False,
                "details": {"error": "Insufficient data for drift detection"}
            }

        ref_arr = np.array(reference_data)
        curr_arr = np.array(current_data)

        # Kolmogorov-Smirnov test for numerical distribution drift (used here for prediction drift)
        statistic, p_value = stats.ks_2samp(ref_arr, curr_arr)
        
        drift_detected = bool(p_value < self.p_value_threshold)

        return {
            "data_drift_detected": drift_detected,
            "feature_drift_detected": drift_detected,
            "prediction_drift_detected": drift_detected,
            "concept_drift_detected": False, # Requires target vs prediction tracking over time
            "performance_drift_detected": False, # Handled by accuracy dropping over time
            "details": {
                "ks_statistic": float(statistic),
                "p_value": float(p_value),
                "threshold": self.p_value_threshold
            }
        }

drift_detector = DriftDetector()

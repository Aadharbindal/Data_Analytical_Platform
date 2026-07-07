import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger("ChangePointDetector")

class ChangePointDetector:
    """Extracts structural breaks and reversals (CUSUM mock)."""
    
    def detect_change_points(self, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        points = []
        
        cp_meta = metadata.get("change_points", [])
        for cp in cp_meta:
            points.append({
                "detection_method": cp.get("method", "CUSUM"),
                "shift_type": cp.get("type", "STRUCTURAL_BREAK"),
                "timestamp": datetime.fromisoformat(cp["timestamp"].replace("Z", "+00:00")) if "timestamp" in cp else datetime.utcnow(),
                "magnitude": cp.get("magnitude", 10.0),
                "confidence": cp.get("confidence", 95.0),
                "business_event_flag": cp.get("magnitude", 0) > 20.0
            })
            
        return points

change_point_detector = ChangePointDetector()

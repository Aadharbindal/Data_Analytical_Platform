import logging
from typing import Dict, Any

logger = logging.getLogger("BusinessRuleFilter")

class BusinessRuleFilter:
    """Estimates revenue/cost impact, risk score, severity."""
    
    def assess_severity(self, outlier: Dict[str, Any], col_stats: Dict[str, Any]) -> Dict[str, Any]:
        
        std = col_stats.get("std_dev", 1.0)
        dist_mean = outlier.get("distance_from_mean", 0.0)
        
        # If distance from mean is > 5 standard deviations, CRITICAL
        z = dist_mean / std if std > 0 else 0
        
        severity = "LOW"
        risk_score = 10.0
        
        if z > 5.0:
            severity = "CRITICAL"
            risk_score = 95.0
        elif z > 4.0:
            severity = "HIGH"
            risk_score = 75.0
        elif z > 3.0:
            severity = "MEDIUM"
            risk_score = 45.0
            
        return {
            "severity": severity,
            "business_impact": f"{severity} risk detected based on variance magnitude.",
            "risk_score": risk_score
        }

business_rule_filter = BusinessRuleFilter()

from typing import Dict, Any

class RiskEngine:
    """Calculates granular risk scores based on classification and compliance status."""
    
    @staticmethod
    def calculate_scores(classification: Dict[str, Any], compliance: Dict[str, Any]) -> Dict[str, Any]:
        privacy_risk = 0.0
        compliance_risk = 0.0
        business_risk = 0.0
        
        # Privacy Risk based on classification
        cls = classification.get("overall_classification", "Public")
        if cls == "Highly Confidential":
            privacy_risk = 100.0
        elif cls == "Confidential":
            privacy_risk = 75.0
        elif cls == "Restricted":
            privacy_risk = 50.0
        elif cls == "Internal":
            privacy_risk = 25.0
            
        # Compliance Risk
        if compliance.get("pci_dss_status") == "Violations Found":
            compliance_risk += 50.0
        if compliance.get("hipaa_status") == "Violations Found":
            compliance_risk += 50.0
        if compliance.get("gdpr_status") == "Violations Found":
            compliance_risk += 40.0
            
        compliance_risk = min(100.0, compliance_risk)
        
        # Business Risk is a weighted average
        business_risk = (privacy_risk * 0.6) + (compliance_risk * 0.4)
        
        # Exposure Risk (assuming worst case since data is fresh and unmasked)
        exposure_risk = privacy_risk
        
        # Governance Score (Inverse of risks)
        avg_risk = (privacy_risk + compliance_risk + business_risk + exposure_risk) / 4
        governance_score = max(0.0, 100.0 - avg_risk)
        
        return {
            "privacy_risk_score": privacy_risk,
            "compliance_risk_score": compliance_risk,
            "business_risk_score": business_risk,
            "exposure_risk_score": exposure_risk,
            "overall_governance_score": governance_score
        }

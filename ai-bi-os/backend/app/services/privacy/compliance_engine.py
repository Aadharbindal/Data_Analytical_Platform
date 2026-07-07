from typing import List, Dict, Any

class ComplianceEngine:
    """Maps PII entities to regulatory compliance frameworks."""
    
    @staticmethod
    def evaluate(detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        gdpr_status = "Not Applicable"
        ccpa_status = "Not Applicable"
        pci_status = "Not Applicable"
        hipaa_status = "Not Applicable"
        
        violations = []
        recommendations = []
        
        entities = set([d["entity_type"] for d in detections])
        
        # PCI DSS
        if "Credit Card" in entities:
            pci_status = "Violations Found"
            violations.append("Unencrypted Credit Card data detected. This violates PCI DSS.")
            recommendations.append("Apply Tokenization or Full Masking to Credit Card columns immediately.")
            
        # HIPAA
        if "Medical Record Number" in entities or "Insurance Number" in entities:
            hipaa_status = "Violations Found"
            violations.append("Protected Health Information (PHI) detected.")
            recommendations.append("Apply strict Role-based Visibility and Data Encryption to comply with HIPAA.")
            
        # GDPR / CCPA (Broad PII)
        pii_entities = entities.intersection({"Email Address", "Phone Number", "Person Name", "Street Address", "Date of Birth", "GPS Coordinates"})
        if pii_entities:
            gdpr_status = "Violations Found"
            ccpa_status = "Violations Found"
            violations.append(f"Direct Identifiable PII detected: {', '.join(pii_entities)}.")
            recommendations.append("Implement Right-to-be-Forgotten workflows. Apply Pseudonymization (Hashing) where analytics is required.")
            
        return {
            "gdpr_status": gdpr_status,
            "ccpa_status": ccpa_status,
            "pci_dss_status": pci_status,
            "hipaa_status": hipaa_status,
            "violations": violations,
            "recommendations": recommendations
        }

from typing import List, Dict, Any

class ClassificationEngine:
    """Classifies dataset overall based on detected PII elements."""
    
    HIGHLY_CONFIDENTIAL = ["Credit Card", "SSN", "Passport", "Driver License", "Tax ID", "Passwords", "Private Keys", "Medical Record Number"]
    CONFIDENTIAL = ["Email Address", "Phone Number", "Mobile Number", "Date of Birth", "Person Name", "Street Address", "GPS Coordinates"]
    RESTRICTED = ["Customer ID", "Employee ID", "IP Address", "MAC Address"]
    
    @staticmethod
    def classify(detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        has_pii = False
        has_financial = False
        has_healthcare = False
        
        highest_classification = "Public"
        classification_rank = {"Public": 0, "Internal": 1, "Restricted": 2, "Confidential": 3, "Highly Confidential": 4}
        
        for det in detections:
            entity = det["entity_type"]
            
            # Determine flags
            if entity in ClassificationEngine.HIGHLY_CONFIDENTIAL or entity in ClassificationEngine.CONFIDENTIAL:
                has_pii = True
            if entity in ["Credit Card", "IBAN", "Bank Account", "SWIFT"]:
                has_financial = True
            if entity in ["Medical Record Number", "Insurance Number"]:
                has_healthcare = True
                
            # Determine level
            level = "Internal"
            if entity in ClassificationEngine.HIGHLY_CONFIDENTIAL:
                level = "Highly Confidential"
            elif entity in ClassificationEngine.CONFIDENTIAL:
                level = "Confidential"
            elif entity in ClassificationEngine.RESTRICTED:
                level = "Restricted"
                
            if classification_rank[level] > classification_rank[highest_classification]:
                highest_classification = level
                
        return {
            "overall_classification": highest_classification,
            "contains_pii": has_pii,
            "contains_financial": has_financial,
            "contains_healthcare": has_healthcare
        }

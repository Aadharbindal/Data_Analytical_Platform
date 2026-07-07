from typing import List, Dict, Any

class DomainEngine:
    """Infers the dataset's business domain using detected entities and metrics."""
    
    DOMAIN_RULES = {
        "E-Commerce & Retail": {
            "entities": ["Customer", "Order", "Product", "Invoice", "Store"],
            "metrics": ["Revenue", "Gross Merchandise Value", "Quantity", "Discount"]
        },
        "Finance & Banking": {
            "entities": ["Customer", "Account", "Transaction", "Branch"],
            "metrics": ["Balance", "Amount", "Interest", "Revenue", "Expense"]
        },
        "Human Resources": {
            "entities": ["Employee", "Department", "Candidate", "Role"],
            "metrics": ["Salary", "Bonus", "Headcount", "Tenure"]
        },
        "Healthcare": {
            "entities": ["Patient", "Doctor", "Hospital", "Encounter", "Treatment"],
            "metrics": ["Cost", "Length of Stay", "Readmission"]
        }
    }
    
    @staticmethod
    def infer_domain(detected_entities: List[str], detected_metrics: List[str]) -> Dict[str, Any]:
        best_domain = "General Business"
        highest_score = 0.0
        matched_rules = []
        
        detected_set = set(detected_entities + detected_metrics)
        
        if not detected_set:
            return {"primary_domain": best_domain, "confidence_score": 0.0, "matched_rules": []}
            
        for domain, rules in DomainEngine.DOMAIN_RULES.items():
            domain_set = set(rules["entities"] + rules["metrics"])
            overlap = detected_set.intersection(domain_set)
            
            # Simple scoring: percentage of detected terms that fit the domain
            if len(detected_set) > 0:
                score = len(overlap) / len(detected_set)
                if score > highest_score:
                    highest_score = score
                    best_domain = domain
                    matched_rules = list(overlap)
                    
        return {
            "primary_domain": best_domain,
            "confidence_score": highest_score,
            "matched_rules": matched_rules
        }

import re
from typing import Dict, Any

class ContextPlanner:
    """Infers intent and extracts keywords from the user question deterministically."""
    
    @staticmethod
    def plan(question: str) -> Dict[str, Any]:
        question_lower = question.lower()
        
        # Deterministic Intent Inference
        intent = "GENERAL_QUERY"
        if any(word in question_lower for word in ["why", "cause", "reason"]):
            intent = "DIAGNOSTIC"
        elif any(word in question_lower for word in ["what if", "predict", "forecast"]):
            intent = "PREDICTIVE"
        elif any(word in question_lower for word in ["should i", "recommend", "action"]):
            intent = "PRESCRIPTIVE"
            
        # Keyword Extraction (very basic stopword removal)
        stopwords = {"the", "a", "an", "is", "are", "what", "why", "how", "when", "to", "for", "in", "of", "and"}
        words = re.findall(r'\b\w+\b', question_lower)
        keywords = [w for w in words if w not in stopwords and len(w) > 2]
        
        return {
            "intent": intent,
            "keywords": keywords,
            "domain_hints": [kw for kw in keywords if kw in ["revenue", "cost", "marketing", "sales"]]
        }

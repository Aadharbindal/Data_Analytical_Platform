from app.schemas.orchestrator import IntentClassification

class IntentRouter:
    def __init__(self):
        pass
        
    def classify_intent(self, user_request: str) -> IntentClassification:
        # MVP classification heuristic (would be replaced by a small SLM/embeddings later)
        text = user_request.lower()
        if "forecast" in text or "predict" in text:
            return IntentClassification(intent="Forecast", confidence=0.85)
        elif "sql" in text or "select" in text:
            return IntentClassification(intent="SQL Query", confidence=0.90)
        elif "why" in text or "root cause" in text:
            return IntentClassification(intent="Root Cause Analysis", confidence=0.75)
        elif "dashboard" in text or "report" in text:
            return IntentClassification(intent="Business Analytics", confidence=0.80)
            
        return IntentClassification(intent="General Chat", confidence=0.50)

class IntentAnalyzer:
    def __init__(self):
        pass

    def analyze(self, user_request: str) -> str:
        """
        Classifies the request into SQL operations.
        (Aggregation, Filtering, Grouping, Top N, etc.)
        """
        # MVP classification
        lower_req = user_request.lower()
        if "top" in lower_req or "bottom" in lower_req:
            return "Top N"
        if "sum" in lower_req or "total" in lower_req or "average" in lower_req:
            return "Aggregation"
        if "group by" in lower_req or "by" in lower_req:
            return "Grouping"
        return "Custom SQL"

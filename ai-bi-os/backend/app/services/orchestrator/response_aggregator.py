from typing import Dict, Any

class ResponseAggregator:
    def __init__(self):
        pass

    def aggregate(self, execution_results: list) -> Dict[str, Any]:
        """
        Aggregates outputs if multiple agents or tools were executed.
        """
        if not execution_results:
            return {"content": "No response generated."}
        
        # MVP: just return the first result
        return execution_results[0]

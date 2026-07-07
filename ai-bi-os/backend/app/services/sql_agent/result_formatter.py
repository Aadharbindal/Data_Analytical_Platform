from typing import Dict, Any, List

class ResultFormatter:
    def __init__(self):
        pass

    def format(self, raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Formats raw database rows into structured analytics payload.
        """
        if not raw_data:
            return {"data": [], "summary": "No data returned."}
            
        columns = list(raw_data[0].keys())
        return {
            "columns": columns,
            "data": raw_data,
            "row_count": len(raw_data)
        }

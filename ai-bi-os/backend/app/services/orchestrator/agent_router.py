class AgentRouter:
    def __init__(self):
        pass

    def select_agent(self, intent: str) -> str:
        if intent == "SQL Query":
            return "sql_agent"
        elif intent == "Forecast" or intent == "Trend Analysis":
            return "python_analytics_agent"
        else:
            return "general_agent"

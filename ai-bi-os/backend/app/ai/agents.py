class BaseAgent:
    """Base class for specialized AI agents."""
    def __init__(self, name: str):
        self.name = name

    def execute(self, task: str, context: dict) -> str:
        raise NotImplementedError

class AnalyticsPlanner(BaseAgent):
    """Drafts a multi-step execution plan for complex queries."""
    def __init__(self):
        super().__init__("Planner")

    def execute(self, task: str, context: dict) -> list:
        # Returns a list of steps to execute
        return [
            {"agent": "sql", "task": "Query revenue by region"},
            {"agent": "analytics", "task": "Calculate correlation between marketing spend and revenue"},
            {"agent": "insight", "task": "Summarize the findings"}
        ]

class SQLAgent(BaseAgent):
    """Text-to-DuckDB Agent for data retrieval."""
    def __init__(self):
        super().__init__("SQLAgent")

    def execute(self, task: str, context: dict) -> str:
        return f"SELECT * FROM data WHERE context='{task}'"

class AnalyticsAgent(BaseAgent):
    """Python-based EDA agent."""
    def __init__(self):
        super().__init__("AnalyticsAgent")

    def execute(self, task: str, context: dict) -> str:
        return "Calculated Pearson correlation: 0.85"

class InsightAgent(BaseAgent):
    """Generates natural language narratives."""
    def __init__(self):
        super().__init__("InsightAgent")

    def execute(self, task: str, context: dict) -> str:
        return "Based on the data, revenue is strongly correlated with marketing spend."

import os
from app.ai.registry import ModelRegistry

import json
from app.ai.mcp_tools import MCPToolAbstraction, register_duckdb_tools, register_rag_tools
from app.ai.telemetry import TelemetryLogger
from app.ai.cost_tracker import CostTracker

class AgentOrchestrator:
    """Orchestrates the agents based on the Planner's output."""
    def __init__(self):
        self.planner = AnalyticsPlanner()
        self.registry = ModelRegistry()
        self.telemetry = TelemetryLogger()
        self.cost_tracker = CostTracker()
        self.agents = {
            "sql": SQLAgent(),
            "analytics": AnalyticsAgent(),
            "insight": InsightAgent()
        }
        
        self.system_prompt = (
            "You are the core AI Business Analyst for the DataMind Copilot Platform. "
            "You have access to a DuckDB analytical engine via tools, and a semantic knowledge base. "
            "If a user asks a quantitative data question, ALWAYS use the query_duckdb tool to find the exact mathematical answer. "
            "If the SQL query fails, fix the SQL and try again. "
            "CRITICAL: If the user explicitly asks for a chart, graph, or visualization, you MUST return your FINAL response as a valid JSON object with exactly two keys: "
            "'text_response' (string with your analysis) and 'chart_config' (object with 'type' string e.g. 'bar', 'line', 'area' and 'data' array of objects). "
            "If no chart is requested, return standard text."
        )

    def run_query(self, user_query: str, db_engine=None) -> dict:
        """Main entry point for a conversational query with ReAct Tool Calling Loop."""
        
        span_id = self.telemetry.start_span("AgentOrchestrator.run_query")
        
        query_prompt_tokens = 0
        query_completion_tokens = 0

        mcp = MCPToolAbstraction()
        # Always register the RAG tools
        register_rag_tools(mcp)
        
        if db_engine:
            register_duckdb_tools(mcp, db_engine)
            
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_query}
        ]
        
        executed_sql = []
        max_loops = 3
        for _ in range(max_loops):
            msg = self.registry.route_request(
                messages=messages,
                tools=mcp.get_tool_schema()
            )
            
            # Extract usage if available
            usage = getattr(msg, "usage", None)
            if usage:
                query_prompt_tokens += getattr(usage, "prompt_tokens", 0)
                query_completion_tokens += getattr(usage, "completion_tokens", 0)
            
            # If no tool calls, this is the final answer
            if not msg.tool_calls:
                self.cost_tracker.record_usage(query_prompt_tokens, query_completion_tokens)
                est_cost = self.cost_tracker.calculate_cost(query_prompt_tokens, query_completion_tokens)
                self.telemetry.end_span(span_id, {"status": "success", "tools_used": len(executed_sql), "cost": est_cost})
                return {
                    "query": user_query,
                    "final_insight": msg.content,
                    "executed_sql": executed_sql,
                    "cost_estimate": est_cost
                }
                
            # Handle tool calls
            messages.append({"role": "assistant", "content": msg.content, "tool_calls": msg.tool_calls})
            
            for tool_call in msg.tool_calls:
                func_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                
                if func_name == "query_duckdb" and "sql_query" in args:
                    executed_sql.append(args["sql_query"])
                
                try:
                    tool_result = mcp.execute_tool(func_name, **args)
                except Exception as e:
                    tool_result = str(e)
                    
                messages.append({
                    "role": "tool",
                    "name": func_name,
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })
                
        # If we exceed max loops, just force a final generation without tools
        final_msg = self.registry.route_request(messages=messages, tools=None)
        
        usage = getattr(final_msg, "usage", None)
        if usage:
            query_prompt_tokens += getattr(usage, "prompt_tokens", 0)
            query_completion_tokens += getattr(usage, "completion_tokens", 0)
            
        self.cost_tracker.record_usage(query_prompt_tokens, query_completion_tokens)
        est_cost = self.cost_tracker.calculate_cost(query_prompt_tokens, query_completion_tokens)
        
        self.telemetry.end_span(span_id, {"status": "timeout_fallback", "cost": est_cost})
        return {
            "query": user_query,
            "final_insight": final_msg.content or "Exceeded max loops trying to query data.",
            "executed_sql": executed_sql,
            "cost_estimate": est_cost
        }

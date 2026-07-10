from typing import Dict, Any, Callable
from app.ai.rag_engine import RAGEngine

class MCPToolAbstraction:
    """Abstracts tool execution following the Model Context Protocol (MCP) standard."""
    
    def __init__(self):
        self.registered_tools = {}

    def register_tool(self, name: str, description: str, parameters: dict, func: Callable):
        """Registers a tool with an MCP-compatible (and LiteLLM compatible) schema."""
        self.registered_tools[name] = {
            "schema": {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters
                }
            },
            "execute": func
        }

    def get_tool_schema(self) -> list:
        """Returns the schema of all registered tools for the LLM to understand."""
        return [data["schema"] for data in self.registered_tools.values()]

    def execute_tool(self, name: str, **kwargs):
        """Executes a requested tool."""
        if name in self.registered_tools:
            return self.registered_tools[name]["execute"](**kwargs)
        raise ValueError(f"Tool {name} not found")

def register_duckdb_tools(mcp: MCPToolAbstraction, db_engine):
    """Registers the DuckDB querying tools into the provided MCP instance."""
    
    def run_sql(sql_query: str) -> str:
        try:
            # We assume the table is named 'active_dataset'
            result = db_engine.execute(sql_query)
            rows = result.get("rows", [])
            if not rows:
                return "Query returned 0 rows."
            # Convert to JSON string for the LLM
            import json
            return json.dumps(rows)
        except Exception as e:
            return f"SQL Error: {str(e)}"
            
    mcp.register_tool(
        name="query_duckdb",
        description="Run a SQL query against the DuckDB analytics engine. The primary table is named 'active_dataset'.",
        parameters={
            "type": "object",
            "properties": {
                "sql_query": {
                    "type": "string",
                    "description": "The exact SQL query to execute."
                }
            },
            "required": ["sql_query"]
        },
        func=run_sql
    )

def register_rag_tools(mcp: MCPToolAbstraction):
    """Registers knowledge base search tools."""
    rag = RAGEngine()
    
    def search_kb(query: str) -> str:
        try:
            results = rag.retrieve_context(query)
            return "\n".join([f"- {r}" for r in results])
        except Exception as e:
            return f"Search Error: {str(e)}"
            
    mcp.register_tool(
        name="search_knowledge_base",
        description="Search the semantic knowledge base for business definitions, policies, or qualitative context.",
        parameters={
            "type": "object",
            "properties": {
                "search_query": {
                    "type": "string",
                    "description": "The concept or question to search for."
                }
            },
            "required": ["search_query"]
        },
        func=search_kb
    )

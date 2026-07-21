import os
import uuid
import logging
from app.ai.registry import ModelRegistry
from app.core.config import LLM_MODEL_COMPLEX
from app.ai.governance import AIGuardrails, PromptManager, AIEvaluationFramework

import json
from app.ai.mcp_tools import MCPToolAbstraction, register_duckdb_tools, register_rag_tools
from app.ai.telemetry import TelemetryLogger
from app.ai.cost_tracker import CostTracker

class AgentOrchestrator:
    """Core conversational agent orchestrator."""

    DEFAULT_SYSTEM_PROMPT = (
        "You are the core AI Business Analyst for the DataMind Copilot Platform. "
        "You have access to a DuckDB analytical engine via tools, and a semantic knowledge base. "
        "If a user asks a quantitative data question, ALWAYS use the query_duckdb tool to find the exact mathematical answer. "
        "If the SQL query fails, fix the SQL and try again. "
        "CRITICAL: If the user explicitly asks for a chart, graph, or visualization, you MUST return your FINAL response as a valid JSON object with exactly two keys: "
        "'text_response' (string with your analysis) and 'chart_config' (object with 'type' string e.g. 'bar', 'line', 'area' and 'data' array of objects). "
        "If no chart is requested, return standard text."
    )

    def __init__(self):
        self.registry = ModelRegistry()
        self.telemetry = TelemetryLogger()
        self.cost_tracker = CostTracker()
        self.guardrails = AIGuardrails()
        self.evaluator = AIEvaluationFramework()

        # DB-backed prompt versioning (see PromptManager): seeds the DB with
        # the hardcoded default below on first run, then serves whatever is
        # stored from then on - editable without a code deploy.
        self.system_prompt = PromptManager().get_prompt(
            "agent_system_prompt", default=self.DEFAULT_SYSTEM_PROMPT
        )

    def run_query(self, user_query: str, user_id: str = None, db_engine=None) -> dict:
        """Main entry point for a conversational query with ReAct Tool Calling Loop."""
        span_id = self.telemetry.start_span("AgentOrchestrator.run_query")

        if not self.guardrails.validate_input(user_query):
            self.telemetry.end_span(span_id, {"status": "blocked_input"})
            return {
                "query": user_query,
                "final_insight": "This request could not be processed - it appears to contain a prompt-injection attempt. Please rephrase your question about the data.",
                "executed_sql": [],
                "cost_estimate": 0.0,
                "trace_id": None
            }

        query_prompt_tokens = 0
        query_completion_tokens = 0

        mcp = MCPToolAbstraction()
        register_rag_tools(mcp, user_id)
        
        system_prompt = self.system_prompt
        
        if db_engine:
            register_duckdb_tools(mcp, db_engine)
            try:
                from app.services.schema_helper import get_schema_context
                ctx = get_schema_context(db_engine, "active_dataset")
                formatted_ctx = ctx["formatted_context"].replace("\n", "\\n")
                system_prompt += f"\\n\\n{formatted_ctx}\\n\\nRULES:\n- Use ONLY the table and column names listed above, exactly as spelled.\n- Use standard DuckDB SQL syntax.\n- Always alias aggregates.\n- Never invent columns.\n\nCRITICAL RULES:\n1. Answer ONLY from query results on the columns listed above. If a question requires data that does not exist (e.g. cost, profit, margin when no such column exists), say clearly that the data is not available and list which columns ARE available. NEVER assume, estimate, or invent values (prices, costs, counts).\n2. If you reinterpret the user's wording to a different column (e.g. 'branch' -> Region), SAY SO explicitly in the answer.\n3. Every number in your answer must come from a query result in this conversation. If you did not query it, do not state it."
            except Exception:
                pass
                
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
        
        executed_sql = []
        max_loops = 6 # Up to 3 attempts
        for loop_idx in range(max_loops):
            # Complex-tier model: this loop does multi-step tool selection and
            # SQL generation, which benefits from a more capable model far more
            # than the templated narrative-writing tasks elsewhere in the app do.
            msg = self.registry.route_request(
                messages=messages,
                tools=mcp.get_tool_schema(),
                target_model=LLM_MODEL_COMPLEX
            )

            usage = getattr(msg, "usage", None)
            if usage:
                query_prompt_tokens += getattr(usage, "prompt_tokens", 0)
                query_completion_tokens += getattr(usage, "completion_tokens", 0)

            if not msg.tool_calls:
                final_text = msg.content or ""
                final_text = __import__('re').sub(r'<function.*?>.*?</function>', '', final_text, flags=__import__('re').DOTALL).strip()
                if not final_text:
                    final_text = "I have processed your request."
                    
                import re
                if len(executed_sql) == 0 and re.search(r'\d', final_text):
                    final_text = "**Note: this answer was not computed from your data**\n\n" + final_text

                if final_text.strip().startswith("{"):
                    constraints = {"requires_json": True, "required_keys": ["text_response", "chart_config"]}
                    if not self.guardrails.validate_output(final_text, constraints):
                        logging.warning(f"AIGuardrails: chart response failed output validation for query: {user_query[:80]!r}")

                self.cost_tracker.record_usage(query_prompt_tokens, query_completion_tokens)
                est_cost = self.cost_tracker.calculate_cost(query_prompt_tokens, query_completion_tokens)
                self.telemetry.end_span(span_id, {"status": "success", "tools_used": len(executed_sql), "cost": est_cost})

                trace_id = str(uuid.uuid4())
                self.evaluator.log_response(trace_id, user_query, final_text, user_id=user_id)

                return {
                    "query": user_query,
                    "final_insight": final_text,
                    "executed_sql": executed_sql,
                    "cost_estimate": est_cost,
                    "trace_id": trace_id
                }
                
            messages.append({"role": "assistant", "content": msg.content, "tool_calls": msg.tool_calls})
            
            for tool_call in msg.tool_calls:
                func_name = tool_call.function.name
                args = __import__('json').loads(tool_call.function.arguments)
                
                if func_name == "query_duckdb" and "sql_query" in args:
                    executed_sql.append(args["sql_query"])
                
                try:
                    tool_result = mcp.execute_tool(func_name, **args)
                except Exception as e:
                    tool_result = f"SQL Error: {str(e)}"
                    
                if "SQL Error:" in tool_result or "Error:" in tool_result:
                    tool_result = f"Query failed: {tool_result}. Fix the query using only the schema provided and try again."
                    
                messages.append({
                    "role": "tool",
                    "name": func_name,
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })
                
        final_msg = self.registry.route_request(messages=messages, tools=None, target_model=LLM_MODEL_COMPLEX)
        usage = getattr(final_msg, "usage", None)
        if usage:
            query_prompt_tokens += getattr(usage, "prompt_tokens", 0)
            query_completion_tokens += getattr(usage, "completion_tokens", 0)

        self.cost_tracker.record_usage(query_prompt_tokens, query_completion_tokens)
        est_cost = self.cost_tracker.calculate_cost(query_prompt_tokens, query_completion_tokens)

        final_text = final_msg.content or "Exceeded max loops trying to query data."
        final_text = __import__('re').sub(r'<function.*?>.*?</function>', '', final_text, flags=__import__('re').DOTALL).strip()
        
        import re
        if len(executed_sql) == 0 and re.search(r'\d', final_text):
            final_text = "**Note: this answer was not computed from your data**\n\n" + final_text
        
        self.telemetry.end_span(span_id, {"status": "timeout_fallback", "cost": est_cost})

        trace_id = str(uuid.uuid4())
        self.evaluator.log_response(trace_id, user_query, final_text, user_id=user_id)

        return {
            "query": user_query,
            "final_insight": final_text,
            "executed_sql": executed_sql,
            "cost_estimate": est_cost,
            "trace_id": trace_id
        }
    def stream_query(self, user_messages: list, user_id: str = None, db_engine=None):
        """Yields Server-Sent Events (SSE) formatting for a streaming conversational query."""
        span_id = self.telemetry.start_span("AgentOrchestrator.stream_query")
        
        query_prompt_tokens = 0
        query_completion_tokens = 0

        mcp = MCPToolAbstraction()
        register_rag_tools(mcp, user_id)
        
        system_prompt = self.system_prompt
        
        if db_engine:
            register_duckdb_tools(mcp, db_engine)
            try:
                from app.services.schema_helper import get_schema_context
                ctx = get_schema_context(db_engine, "active_dataset")
                system_prompt += f"\n\n{ctx['formatted_context']}\n\nRULES:\n- Use ONLY the table and column names listed above, exactly as spelled.\n- Use standard DuckDB SQL syntax.\n- Always alias aggregates.\n- Never invent columns.\n\nCRITICAL RULES:\n1. Answer ONLY from query results on the columns listed above. If a question requires data that does not exist (e.g. cost, profit, margin when no such column exists), say clearly that the data is not available and list which columns ARE available. NEVER assume, estimate, or invent values (prices, costs, counts).\n2. If you reinterpret the user's wording to a different column (e.g. 'branch' -> Region), SAY SO explicitly in the answer.\n3. Every number in your answer must come from a query result in this conversation. If you did not query it, do not state it."
            except Exception:
                pass
                
        # user_messages is the history + current message
        messages = [{"role": "system", "content": system_prompt}] + user_messages
        
        executed_sql = []
        max_loops = 6 # Up to 3 attempts
        
        import json
        import re
        
        yield f"data: {json.dumps({'type': 'status', 'text': 'Analyzing your question...'})}\n\n"
        
        for loop_idx in range(max_loops):
            msg = self.registry.route_request(
                messages=messages,
                tools=mcp.get_tool_schema()
            )
            
            usage = getattr(msg, "usage", None)
            if usage:
                query_prompt_tokens += getattr(usage, "prompt_tokens", 0)
                query_completion_tokens += getattr(usage, "completion_tokens", 0)
            
            if not msg.tool_calls:
                break
                
            messages.append({"role": "assistant", "content": msg.content, "tool_calls": msg.tool_calls})
            
            for tool_call in msg.tool_calls:
                func_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                
                if func_name == "query_duckdb" and "sql_query" in args:
                    executed_sql.append(args["sql_query"])
                    yield f"data: {json.dumps({'type': 'status', 'text': 'Running SQL query...'})}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'status', 'text': f'Running {func_name}...'})}\n\n"
                
                try:
                    tool_result = mcp.execute_tool(func_name, **args)
                except Exception as e:
                    tool_result = f"SQL Error: {str(e)}"
                    
                if "SQL Error:" in tool_result or "Error:" in tool_result:
                    tool_result = f"Query failed: {tool_result}. Fix the query using only the schema provided and try again."
                    
                messages.append({
                    "role": "tool",
                    "name": func_name,
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })
                
        # Final stream
        try:
            final_response_stream = self.registry.route_request(messages=messages, tools=None, stream=True)
            final_text = ""
            
            for chunk in final_response_stream:
                delta = chunk.choices[0].delta
                content = delta.content
                if content:
                    final_text += content
                    yield f"data: {json.dumps({'type': 'token', 'text': content})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'text': str(e)})}\n\n"
            return
            
        final_text = re.sub(r'<function.*?>.*?</function>', '', final_text, flags=re.DOTALL).strip()
        if len(executed_sql) == 0 and re.search(r'\d', final_text):
            msg_data = {'type': 'token', 'text': '\n\n**Note: this answer was not computed from your data**'}
            yield f"data: {json.dumps(msg_data)}\n\n"
            
        self.cost_tracker.record_usage(query_prompt_tokens, query_completion_tokens)
        est_cost = self.cost_tracker.calculate_cost(query_prompt_tokens, query_completion_tokens)
        self.telemetry.end_span(span_id, {"status": "success", "cost": est_cost})
        
        yield f"data: {json.dumps({'type': 'done', 'executed_sql': executed_sql})}\n\n"

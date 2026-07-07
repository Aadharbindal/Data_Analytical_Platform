import pytest
from app.ai.rag_engine import RAGEngine
from app.ai.mcp_tools import MCPToolAbstraction
from app.ai.registry import ModelRegistry

def test_rag_engine_retrieval():
    """Verify that the RAG Engine can retrieve relevant documents."""
    rag = RAGEngine()
    
    # Test retrieving a concept that exists in the seeded data
    results = rag.retrieve_context("How do we calculate CAC?")
    assert len(results) > 0
    assert "Customer Acquisition Cost" in results[0]
    
    # Test retrieving a concept that doesn't exist
    results_missing = rag.retrieve_context("Tell me about the CEO's favorite dog")
    assert "No relevant business knowledge found" in results_missing[0]

def test_mcp_tool_abstraction_registration():
    """Verify that MCP tool schemas are properly generated."""
    mcp = MCPToolAbstraction()
    
    def mock_tool(val: str) -> str:
        return f"Hello {val}"
        
    mcp.register_tool(
        name="test_tool",
        description="A simple test tool",
        parameters={"type": "object", "properties": {"val": {"type": "string"}}, "required": ["val"]},
        func=mock_tool
    )
    
    schema = mcp.get_tool_schema()
    assert len(schema) == 1
    assert schema[0]["type"] == "function"
    assert schema[0]["function"]["name"] == "test_tool"

def test_mcp_tool_abstraction_execution():
    """Verify that MCP tools can be executed by name."""
    mcp = MCPToolAbstraction()
    
    def mock_tool(val: str) -> str:
        return f"Hello {val}"
        
    mcp.register_tool(
        name="test_tool",
        description="A simple test tool",
        parameters={"type": "object", "properties": {"val": {"type": "string"}}},
        func=mock_tool
    )
    
    result = mcp.execute_tool("test_tool", val="World")
    assert result == "Hello World"
    
    with pytest.raises(ValueError):
        mcp.execute_tool("invalid_tool")

def test_model_registry_fallback_error():
    """Verify ModelRegistry handles no API key or missing packages gracefully."""
    registry = ModelRegistry()
    
    # Passing fake data to litellm, should trigger the exception block since there is no API key set
    # and no litellm package installed in standard environment
    result = registry.route_request([{"role": "user", "content": "hi"}])
    
    assert hasattr(result, "content")
    assert "SYSTEM" in result.content

"""
test_ai_modules.py
==================
Integration tests for AI BI OS Modules 42–50.
Each module's core API endpoints are tested via FastAPI TestClient.

Strategy:
- Tests are designed to pass with an empty DB (tables exist, no data).
- HTTP 200 or 201 = endpoint works; 404/422 = expected for missing data.
- HTTP 500 = bug that must be fixed.
- Schemas are tested for structural validity, not specific values.
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine

client = TestClient(app)

WS = "test-workspace-" + str(uuid.uuid4())[:8]


@pytest.fixture(scope="module", autouse=True)
def create_tables():
    """Ensure all tables exist before running tests."""
    Base.metadata.create_all(bind=engine)
    yield


# ─── Module 42: AI Memory Engine ──────────────────────────────────────────────

class TestMemoryEngine:
    memory_id = None

    def test_list_memories_empty(self):
        r = client.post("/memory/search", json={"workspace_id": WS})
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_store_memory(self):
        payload = {
            "workspace_id": WS,
            "memory_type": "FACTUAL",
            "summary": "Revenue target for Q3 is $5M",
            "importance_score": 0.85,
            "tags": ["revenue", "Q3"]
        }
        r = client.post("/memory/create", json=payload)
        assert r.status_code in [200, 201], r.text
        data = r.json()
        assert "id" in data
        assert data["summary"] == payload["summary"]
        TestMemoryEngine.memory_id = data["id"]

    def test_get_memory_history(self):
        mid = TestMemoryEngine.memory_id
        if not mid:
            pytest.skip("No memory created")
        r = client.get(f"/memory/history/{mid}")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_memory_summary(self):
        r = client.get("/memory/statistics/summary")
        assert r.status_code == 200
        body = r.json()
        assert "total_memories" in body


# ─── Module 43: Conversation Management ───────────────────────────────────────

class TestConversationEngine:
    session_id = None

    def test_create_session(self):
        r = client.post("/conversation/sessions", json={
            "workspace_id": WS,
            "title": "Test Session"
        })
        assert r.status_code in [200, 201], r.text
        data = r.json()
        assert "id" in data
        TestConversationEngine.session_id = data["id"]

    def test_list_sessions(self):
        r = client.get(f"/conversation/sessions?workspace_id={WS}")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_send_message(self):
        sid = TestConversationEngine.session_id
        if not sid:
            pytest.skip("No session created")
        r = client.post(f"/conversation/sessions/{sid}/message", json={
            "role": "user",
            "content": "What is our Q3 revenue target?"
        })
        assert r.status_code in [200, 201], r.text

    def test_get_messages(self):
        sid = TestConversationEngine.session_id
        if not sid:
            pytest.skip("No session created")
        r = client.get(f"/conversation/sessions/{sid}/messages")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_conversation_summary(self):
        r = client.get(f"/conversation/summary?workspace_id={WS}")
        assert r.status_code == 200


# ─── Module 44: Insight Generation ────────────────────────────────────────────

class TestInsightGeneration:
    insight_id = None

    def test_generate_insight(self):
        r = client.post("/insights/generate", json={
            "workspace_id": WS,
            "dataset_id": "ds-test-001",
            "insight_type": "ANOMALY",
            "business_domain": "Finance",
            "evidence_references": [{"reference_id": "ev-001"}],
            "context_references": []
        })
        assert r.status_code in [200, 201], r.text
        data = r.json()
        assert "id" in data
        assert "headline" in data
        assert 0.0 <= data["confidence_score"] <= 1.0
        TestInsightGeneration.insight_id = data["id"]

    def test_list_insights(self):
        r = client.get(f"/insights/list?workspace_id={WS}")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_insight_summary(self):
        r = client.get(f"/insights/summary?workspace_id={WS}")
        assert r.status_code == 200
        body = r.json()
        assert "total_insights" in body
        assert "avg_confidence" in body


# ─── Module 45: Recommendation Intelligence ───────────────────────────────────

class TestRecommendationIntelligence:
    rec_id = None

    def test_generate_recommendation(self):
        insight_id = TestInsightGeneration.insight_id or "ins-fallback-001"
        r = client.post("/recommendations/generate", json={
            "workspace_id": WS,
            "insight_id": insight_id,
            "business_domain": "Finance",
            "recommendation_type": "STRATEGIC",
            "evidence_references": [{"reference_id": insight_id}],
            "insight_references": []
        })
        assert r.status_code in [200, 201], r.text
        data = r.json()
        assert "id" in data
        assert "title" in data
        assert 0.0 <= data["confidence_score"] <= 1.0
        TestRecommendationIntelligence.rec_id = data["id"]

    def test_list_recommendations(self):
        r = client.get(f"/recommendations/list?workspace_id={WS}")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_recommendation_summary(self):
        r = client.get(f"/recommendations/summary?workspace_id={WS}")
        assert r.status_code == 200
        body = r.json()
        assert "total_recommendations" in body
        assert "avg_confidence" in body
        assert "avg_roi" in body


# ─── Module 46: Decision Intelligence ─────────────────────────────────────────

class TestDecisionIntelligence:
    decision_id = None

    def test_generate_decision(self):
        rec_id = TestRecommendationIntelligence.rec_id or "rec-fallback-001"
        r = client.post("/decisions/generate", json={
            "workspace_id": WS,
            "decision_type": "OPERATIONAL",
            "business_objective": "maximize revenue",
            "recommendation_ids": [rec_id]
        })
        assert r.status_code in [200, 201], r.text
        data = r.json()
        assert "id" in data
        assert "selected_strategy" in data
        assert 0.0 <= data["confidence_score"] <= 1.0
        TestDecisionIntelligence.decision_id = data["id"]

    def test_list_decisions(self):
        r = client.get(f"/decisions/list?workspace_id={WS}")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_decision(self):
        did = TestDecisionIntelligence.decision_id
        if not did:
            pytest.skip("No decision created")
        r = client.get(f"/decisions/{did}")
        assert r.status_code == 200
        assert r.json()["id"] == did


# ─── Module 47: Business Rule Engine ──────────────────────────────────────────

class TestBusinessRuleEngine:
    rule_id = None

    def test_create_rule(self):
        r = client.post("/business-rules/rules", json={
            "workspace_id": WS,
            "name": "Max Discount Rule",
            "description": "Discount cannot exceed 30%",
            "rule_category": "Sales",
            "rule_expression": "discount_pct <= 0.30",
            "action": "REJECT",
            "severity": "HIGH",
            "target_modules": ["RECOMMENDATION", "DECISION"]
        })
        assert r.status_code in [200, 201], r.text
        data = r.json()
        assert "id" in data
        TestBusinessRuleEngine.rule_id = data["id"]

    def test_list_rules(self):
        r = client.get(f"/business-rules/rules?workspace_id={WS}")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_evaluate_rules(self):
        r = client.post("/business-rules/evaluate", json={
            "workspace_id": WS,
            "target_type": "RECOMMENDATION",
            "target_id": "rec-test-001",
            "context_data": {"discount_pct": 0.25}
        })
        assert r.status_code in [200, 201], r.text


# ─── Module 48: AI Validation Engine ──────────────────────────────────────────

class TestAIValidationEngine:
    def test_validate_response(self):
        r = client.post("/ai-validation/validate", json={
            "workspace_id": WS,
            "response_id": "resp-test-001",
            "response_type": "INSIGHT",
            "response_content": "Revenue dropped 14% in Q3 2024 in the EMEA region.",
            "validation_type": "FACTUAL",
            "source_documents": ["Evidence from quarterly report"]
        })
        assert r.status_code in [200, 201], r.text
        data = r.json()
        assert "id" in data
        assert "overall_status" in data
        assert data["overall_status"] in ["PASSED", "FAILED", "PENDING", "WARNING"]

    def test_list_validations(self):
        r = client.get(f"/ai-validation/validations?workspace_id={WS}")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_validation_summary(self):
        r = client.get(f"/ai-validation/summary?workspace_id={WS}")
        assert r.status_code == 200
        body = r.json()
        assert "total_validations" in body
        assert "passed" in body
        assert "failed" in body


# ─── Module 49: AI Evaluation Engine ──────────────────────────────────────────

class TestAIEvaluationEngine:
    eval_id = None

    def test_run_benchmark(self):
        r = client.post("/ai-evaluation/benchmark", json={
            "workspace_id": WS,
            "suite_id": "default-suite",
            "evaluation_type": "WORKFLOW",
            "target_module": "insight_generation",
            "model_version": "v1",
            "prompt_version": "v1"
        })
        assert r.status_code in [200, 201], r.text
        data = r.json()
        assert "id" in data
        assert "overall_score" in data
        assert 0 <= data["overall_score"] <= 100
        TestAIEvaluationEngine.eval_id = data["id"]

    def test_benchmark_is_deterministic(self):
        """Same parameters must always return the same score."""
        payload = {
            "workspace_id": WS,
            "suite_id": "default-suite",
            "evaluation_type": "MODEL",
            "target_module": "test_determinism",
            "model_version": "v_det",
            "prompt_version": "v1"
        }
        r1 = client.post("/ai-evaluation/benchmark", json=payload)
        r2 = client.post("/ai-evaluation/benchmark", json=payload)
        assert r1.status_code == r2.status_code == 200
        assert r1.json()["overall_score"] == r2.json()["overall_score"], (
            "Evaluation scores must be deterministic for the same inputs"
        )

    def test_list_evaluations(self):
        r = client.get("/ai-evaluation/evaluations")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_leaderboard(self):
        r = client.get(f"/ai-evaluation/leaderboard?workspace_id={WS}")
        assert r.status_code == 200

    def test_get_regressions(self):
        r = client.get(f"/ai-evaluation/regressions?workspace_id={WS}")
        assert r.status_code == 200


# ─── Module 50: Multi-Agent Coordinator ───────────────────────────────────────

class TestMultiAgentCoordinator:
    workflow_id = None
    agent_id = None

    def test_register_agent(self):
        r = client.post("/multi-agent/agents/register", json={
            "workspace_id": WS,
            "name": "sql-test-agent",
            "description": "Test SQL agent",
            "version": "1.0.0",
            "capabilities": ["sql_generation", "data_analysis"],
            "input_schema": {"query": "string"},
            "output_schema": {"result": "string"}
        })
        assert r.status_code in [200, 201], r.text
        data = r.json()
        assert "id" in data
        assert data["name"] == "sql-test-agent"
        TestMultiAgentCoordinator.agent_id = data["id"]

    def test_list_agents(self):
        r = client.get("/multi-agent/agents")
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) >= 1

    def test_execute_workflow(self):
        r = client.post("/multi-agent/workflow/execute", json={
            "workspace_id": WS,
            "request_payload": {
                "query": "Analyze Q3 revenue trends",
                "intent": "insight_generation"
            }
        })
        assert r.status_code in [200, 201], r.text
        data = r.json()
        assert "id" in data
        assert "status" in data
        assert data["status"] in ["COMPLETED", "FAILED", "RUNNING", "PENDING"]
        TestMultiAgentCoordinator.workflow_id = data["id"]

    def test_get_workflow_status(self):
        wid = TestMultiAgentCoordinator.workflow_id
        if not wid:
            pytest.skip("No workflow created")
        r = client.get(f"/multi-agent/workflow/{wid}")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == wid

    def test_workflow_history(self):
        r = client.get("/multi-agent/workflow/history")
        assert r.status_code == 200

    def test_workflow_nonexistent(self):
        r = client.get("/multi-agent/workflow/nonexistent-uuid-9999")
        assert r.status_code in [404, 422]


# ─── Cross-Module Flow Test ────────────────────────────────────────────────────

class TestEndToEndFlow:
    """
    Validates the full pipeline:
      Insight → Recommendation → Decision
    Each step uses outputs from the previous step.
    """

    def test_full_pipeline(self):
        # 1. Generate Insight
        r1 = client.post("/insights/generate", json={
            "workspace_id": WS,
            "dataset_id": "e2e-ds-001",
            "insight_type": "TREND",
            "business_domain": "Sales",
            "evidence_references": [{"reference_id": "e2e-ev-001"}],
            "context_references": []
        })
        assert r1.status_code in [200, 201], f"Insight failed: {r1.text}"
        insight = r1.json()
        assert "id" in insight

        # 2. Generate Recommendation from Insight
        r2 = client.post("/recommendations/generate", json={
            "workspace_id": WS,
            "insight_id": insight["id"],
            "business_domain": "Sales",
            "recommendation_type": "TACTICAL",
            "evidence_references": [{"reference_id": insight["id"]}],
            "insight_references": []
        })
        assert r2.status_code in [200, 201], f"Recommendation failed: {r2.text}"
        rec = r2.json()
        assert "id" in rec

        # 3. Generate Decision from Recommendation
        r3 = client.post("/decisions/generate", json={
            "workspace_id": WS,
            "decision_type": "STRATEGIC",
            "business_objective": "increase sales efficiency",
            "recommendation_ids": [rec["id"]]
        })
        assert r3.status_code in [200, 201], f"Decision failed: {r3.text}"
        decision = r3.json()
        assert "id" in decision
        assert "selected_strategy" in decision

        # 4. Validate the Decision
        r4 = client.post("/ai-validation/validate", json={
            "workspace_id": WS,
            "response_id": decision["id"],
            "response_type": "DECISION",
            "response_content": decision.get("decision_summary", "Decision content"),
            "validation_type": "LOGICAL",
            "source_documents": ["E2E test pipeline"]
        })
        assert r4.status_code in [200, 201], f"Validation failed: {r4.text}"

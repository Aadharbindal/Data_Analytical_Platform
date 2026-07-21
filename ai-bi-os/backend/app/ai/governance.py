import json
import uuid
import logging
from datetime import datetime
from app.core.database import get_db_connection

logger = logging.getLogger("AI-BI-OS-Governance")


class AIGuardrails:
    """Intercepts LLM inputs and outputs to ensure safety and prevent hallucination."""

    FORBIDDEN_PHRASES = ["ignore previous instructions", "system prompt", "disregard the above instructions", "you are now"]

    def validate_input(self, prompt: str) -> bool:
        """Checks for prompt injection or policy violations."""
        lowered = (prompt or "").lower()
        return not any(phrase in lowered for phrase in self.FORBIDDEN_PHRASES)

    def validate_output(self, response: str, constraints: dict = None) -> bool:
        """
        Checks if the output adheres to requested constraints. Currently
        supports the one structured shape this app actually asks the LLM
        to produce: a chart response, which must be valid JSON containing
        the required keys (e.g. text_response/chart_config).
        """
        if not constraints:
            return True

        if constraints.get("requires_json"):
            try:
                parsed = json.loads(response)
            except (ValueError, TypeError):
                return False
            required_keys = constraints.get("required_keys") or []
            if required_keys and not (isinstance(parsed, dict) and all(k in parsed for k in required_keys)):
                return False

        return True


class PromptManager:
    """DB-backed prompt versioning system (see prompt_versions table)."""

    def save_prompt(self, name: str, template: str, version: str = "v1") -> str:
        prompt_id = str(uuid.uuid4())
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO prompt_versions (id, name, version, template, created_at) "
                "VALUES (%s, %s, %s, %s, %s) "
                "ON CONFLICT (name, version) DO UPDATE SET template = EXCLUDED.template",
                (prompt_id, name, version, template, datetime.utcnow().isoformat())
            )
            conn.commit()
        finally:
            cursor.close()
            conn.close()
        return prompt_id

    def get_prompt(self, name: str, version: str = "v1", default: str = None) -> str:
        """
        Returns the stored template for (name, version). If none exists yet
        and `default` is given, seeds the DB with it on first call so the
        prompt becomes editable going forward without a code deploy, while
        behaving identically to the previous hardcoded string until someone
        actually changes it.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT template FROM prompt_versions WHERE name = %s AND version = %s",
                (name, version)
            )
            row = cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

        if row:
            return row[0]
        if default is not None:
            self.save_prompt(name, default, version)
            return default
        return "Default Template"


class AIEvaluationFramework:
    """
    Logs AI outputs (DB-backed, see ai_evaluation_logs table) for offline
    regression review and records human feedback (RLHF-style scoring) via
    submit_human_feedback.
    """

    def log_response(self, trace_id: str, prompt: str, response: str, expected: str = None, user_id: str = None) -> None:
        """Logs the trace for offline regression review. Never raises -
        a logging failure must not break the caller's actual AI response."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO ai_evaluation_logs (trace_id, user_id, prompt, response, expected, created_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (trace_id, user_id, prompt, response, expected, datetime.utcnow().isoformat())
                )
                conn.commit()
            finally:
                cursor.close()
                conn.close()
        except Exception as e:
            logger.warning(f"Failed to log AI evaluation trace {trace_id}: {e}")

    def submit_human_feedback(self, trace_id: str, score: int, comments: str = None) -> bool:
        """Updates a logged trace with human feedback. Returns False if no
        matching trace_id was found (e.g. an unknown/expired id)."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE ai_evaluation_logs SET human_score = %s, comments = %s WHERE trace_id = %s",
                (score, comments, trace_id)
            )
            updated = cursor.rowcount > 0
            conn.commit()
        finally:
            cursor.close()
            conn.close()
        return updated

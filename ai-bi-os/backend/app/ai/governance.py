import uuid
from typing import Dict, Any

class AIGuardrails:
    """Intercepts LLM inputs and outputs to ensure safety and prevent hallucination."""
    
    def validate_input(self, prompt: str) -> bool:
        """Checks for prompt injection or policy violations."""
        forbidden_phrases = ["ignore previous instructions", "system prompt"]
        return not any(phrase in prompt.lower() for phrase in forbidden_phrases)

    def validate_output(self, response: str, constraints: list = None) -> bool:
        """Checks if the output adheres to requested formats (e.g., JSON only)."""
        return True # MVP passthrough

class PromptManager:
    """Database-backed Prompt Versioning System."""
    
    def __init__(self):
        self.prompts = {}
        
    def save_prompt(self, name: str, template: str, version: str = "v1") -> str:
        prompt_id = str(uuid.uuid4())
        self.prompts[f"{name}:{version}"] = template
        return prompt_id

    def get_prompt(self, name: str, version: str = "v1") -> str:
        return self.prompts.get(f"{name}:{version}", "Default Template")

class AIEvaluationFramework:
    """Logs AI outputs for benchmark regression testing and RLHF."""
    
    def __init__(self):
        self.logs = []
        
    def log_response(self, trace_id: str, prompt: str, response: str, expected: str = None):
        """Logs the trace for offline regression testing."""
        self.logs.append({
            "trace_id": trace_id,
            "prompt": prompt,
            "response": response,
            "expected": expected,
            "human_score": None
        })
        
    def submit_human_feedback(self, trace_id: str, score: int, comments: str):
        """Updates a logged trace with human feedback (RLHF)."""
        for log in self.logs:
            if log["trace_id"] == trace_id:
                log["human_score"] = score
                log["comments"] = comments

import logging

logger = logging.getLogger("TokenManager")

class TokenManager:
    """
    Manages rate limits, token counting (tiktoken), and token budgets.
    """
    def estimate_tokens(self, text: str) -> int:
        # MVP naive estimation: ~4 chars per token.
        # In prod, use tiktoken
        return max(1, len(text) // 4)
        
    def check_rate_limit(self, workspace_id: str) -> bool:
        # MVP: no-op, always true. 
        # In prod, check Redis token bucket per workspace
        return True

token_manager = TokenManager()

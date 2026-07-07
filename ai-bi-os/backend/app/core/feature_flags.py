import os

class FeatureFlags:
    """Simple feature flag engine for progressive rollouts."""
    
    @staticmethod
    def is_enabled(feature_name: str) -> bool:
        # For Phase 1 MVP, read from environment or default to False
        flags = {
            "use_temporal": os.getenv("FF_USE_TEMPORAL", "false").lower() == "true",
            "use_kafka": os.getenv("FF_USE_KAFKA", "false").lower() == "true",
            "enable_rlhf": os.getenv("FF_ENABLE_RLHF", "true").lower() == "true"
        }
        return flags.get(feature_name, False)

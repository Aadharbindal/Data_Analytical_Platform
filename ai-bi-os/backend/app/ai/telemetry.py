import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AI-BI-OS-Telemetry")

class TelemetryLogger:
    """
    Mocks an OpenTelemetry (OTel) integration for tracing AI execution.
    In a real production environment, this would export spans to Jaeger or Datadog.
    """
    def __init__(self):
        self.spans = {}

    def start_span(self, span_name: str) -> str:
        """Starts a timing span."""
        span_id = f"{span_name}_{time.time()}"
        self.spans[span_id] = time.time()
        logger.info(f"[OTel Trace Start] {span_name}")
        return span_id

    def end_span(self, span_id: str, metadata: dict = None):
        """Ends a timing span and logs metrics."""
        if span_id in self.spans:
            duration = time.time() - self.spans[span_id]
            meta_str = f" | Meta: {metadata}" if metadata else ""
            logger.info(f"[OTel Trace End] {span_id.split('_')[0]} | Duration: {duration:.2f}s{meta_str}")
            del self.spans[span_id]

    def log_event(self, event_name: str, details: dict):
        """Logs a specific telemetry event."""
        logger.info(f"[OTel Event] {event_name} | {details}")

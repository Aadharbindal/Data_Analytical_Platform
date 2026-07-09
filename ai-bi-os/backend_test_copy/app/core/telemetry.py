# from opentelemetry import trace
# from opentelemetry.sdk.trace import TracerProvider
# from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
import logging

logger = logging.getLogger(__name__)

def setup_telemetry(app_name: str = "ai-bi-os"):
    """
    Initializes OpenTelemetry tracing.
    """
    # provider = TracerProvider()
    # processor = BatchSpanProcessor(ConsoleSpanExporter())
    # provider.add_span_processor(processor)
    # trace.set_tracer_provider(provider)
    logger.info(f"OpenTelemetry initialized for {app_name}")

def get_tracer(module_name: str):
    # return trace.get_tracer(module_name)
    class MockTracer:
        def start_as_current_span(self, name):
            class MockSpan:
                def __enter__(self): pass
                def __exit__(self, exc_type, exc_val, exc_tb): pass
            return MockSpan()
    return MockTracer()

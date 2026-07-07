import logging
from typing import AsyncGenerator

logger = logging.getLogger("StreamManager")

class StreamManager:
    """
    Handles Server-Sent Events (SSE) streaming from providers.
    """
    async def process_stream(self, provider_stream: AsyncGenerator) -> AsyncGenerator:
        """
        Takes a raw provider async generator and yields standard SSE format.
        """
        try:
            async for chunk in provider_stream:
                # In prod, adapt provider-specific chunk to standard
                # format: data: {"chunk": "..."} \n\n
                yield f"data: {chunk}\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
        finally:
            yield "data: [DONE]\n\n"

stream_manager = StreamManager()

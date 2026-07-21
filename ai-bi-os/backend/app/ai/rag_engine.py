import logging
import re
import threading
import uuid
from sentence_transformers import SentenceTransformer, CrossEncoder
from app.core.database import get_db_connection

logger = logging.getLogger("AI-BI-OS-RAGEngine")


def chunk_text(text: str, max_chars: int = 400, overlap: int = 50) -> list:
    """
    Splits `text` into semantically coherent chunks instead of embedding an
    arbitrarily long string as a single vector (which dilutes retrieval —
    one vector trying to represent many unrelated facts matches everything
    equally poorly). Prefers sentence boundaries, falls back to comma-
    separated clauses (the shape of the schema-description text this engine
    embeds today), and finally hard character windows if neither natural
    boundary is present. Chunks after the first carry a small overlap from
    the tail of the previous one so a concept split across a boundary isn't
    entirely lost to whichever side it landed on.
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    units = [u.strip() for u in re.split(r'(?<=[.!?])\s+', text) if u.strip()]
    if len(units) <= 1:
        units = [u.strip() for u in text.split(',') if u.strip()]
    if len(units) <= 1:
        return [text[i:i + max_chars] for i in range(0, len(text), max_chars)]

    chunks = []
    current = ""
    for unit in units:
        candidate = f"{current}, {unit}" if current else unit
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = unit[:max_chars]
    if current:
        chunks.append(current)

    if overlap > 0 and len(chunks) > 1:
        overlapped = [chunks[0]]
        for i in range(1, len(chunks)):
            tail = chunks[i - 1][-overlap:]
            overlapped.append(f"{tail} {chunks[i]}".strip())
        chunks = overlapped

    return chunks


class RAGEngine:
    """
    Retrieval Augmented Generation engine using pgvector for semantic search.
    Uses all-MiniLM-L6-v2 to generate 384-dimensional embeddings, stored and
    queried via pgvector's cosine distance operator (<=>).

    Retrieval is two-stage: pgvector cosine similarity cheaply narrows the
    knowledge_base down to a wider candidate set (a bi-encoder embedding
    is a coarse, fast first pass), then a cross-encoder re-ranks those
    candidates against the raw query text for a more precise final
    ordering. If the cross-encoder can't be loaded (e.g. no network on
    first download), retrieval transparently falls back to the raw
    similarity order rather than failing.

    Both models are loaded once per process (class-level, not per
    RAGEngine() instantiation) since loading them is too slow to repeat
    on every call.
    """

    _bi_encoder = None
    _cross_encoder = None
    _cross_encoder_failed = False
    _model_lock = threading.Lock()

    CROSS_ENCODER_MODEL = 'cross-encoder/ms-marco-MiniLM-L-6-v2'

    def __init__(self):
        pass

    @classmethod
    def _get_bi_encoder(cls) -> SentenceTransformer:
        if cls._bi_encoder is None:
            with cls._model_lock:
                if cls._bi_encoder is None:
                    cls._bi_encoder = SentenceTransformer('all-MiniLM-L6-v2')
        return cls._bi_encoder

    @classmethod
    def _get_cross_encoder(cls):
        if cls._cross_encoder is None and not cls._cross_encoder_failed:
            with cls._model_lock:
                if cls._cross_encoder is None and not cls._cross_encoder_failed:
                    try:
                        cls._cross_encoder = CrossEncoder(cls.CROSS_ENCODER_MODEL)
                    except Exception as e:
                        logger.warning(
                            f"Re-ranking cross-encoder unavailable ({e}); "
                            "falling back to raw cosine-similarity ranking."
                        )
                        cls._cross_encoder_failed = True
        return cls._cross_encoder

    @property
    def model(self) -> SentenceTransformer:
        # Kept for backward compatibility with anything accessing `engine.model` directly.
        return self._get_bi_encoder()

    def embed_and_store(self, text: str, user_id: str, doc_id: str = None) -> None:
        """
        Splits `text` into chunks (see chunk_text) and stores one embedding
        per chunk, tagged with a shared `doc_id` and `chunk_index` so all
        chunks belonging to the same source document stay identifiable
        (e.g. for a future re-index-this-document or delete-this-document
        operation) even though each is retrieved independently.
        """
        chunks = chunk_text(text)
        if not chunks:
            return

        doc_id = doc_id or str(uuid.uuid4())
        model = self._get_bi_encoder()

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            for i, chunk in enumerate(chunks):
                embedding = model.encode(chunk)
                embedding_list = embedding.tolist()
                cursor.execute(
                    "INSERT INTO knowledge_base (user_id, content, embedding, doc_id, chunk_index) "
                    "VALUES (%s, %s, %s::vector, %s, %s)",
                    (user_id, chunk, str(embedding_list), doc_id, i)
                )
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def retrieve_context(self, query: str, user_id: str, top_k: int = 3, candidate_multiplier: int = 4) -> list:
        """
        Two-stage retrieval: pgvector's cosine distance narrows the knowledge
        base down to `top_k * candidate_multiplier` candidates, then (when
        the cross-encoder is available) re-ranks those candidates against
        the query for a more precise final top_k ordering.
        """
        top_k = max(1, min(int(top_k), 20))
        model = self._get_bi_encoder()
        query_embedding = model.encode(query).tolist()
        candidate_k = max(top_k * candidate_multiplier, top_k)

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # <=> is cosine distance in pgvector (lower = more similar)
            cursor.execute(
                "SELECT content FROM knowledge_base WHERE user_id = %s ORDER BY embedding <=> %s::vector LIMIT %s",
                (user_id, str(query_embedding), candidate_k)
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

        if not rows:
            return ["No relevant business knowledge found in the semantic index."]

        candidates = [row[0] for row in rows]

        cross_encoder = self._get_cross_encoder()
        if cross_encoder and len(candidates) > 1:
            try:
                pairs = [(query, c) for c in candidates]
                scores = cross_encoder.predict(pairs)
                candidates = [c for c, _ in sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)]
            except Exception as e:
                logger.warning(f"Cross-encoder re-ranking failed ({e}); using raw similarity order.")

        return candidates[:top_k]

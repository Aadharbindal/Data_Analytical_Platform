from sentence_transformers import SentenceTransformer
from app.core.database import get_db_connection

class RAGEngine:
    """
    Retrieval Augmented Generation engine using pgvector for semantic search.
    Uses all-MiniLM-L6-v2 to generate 384-dimensional embeddings, stored and
    queried via pgvector's cosine distance operator (<=>).
    """
    
    def __init__(self):
        # Load the embedding model
        # all-MiniLM-L6-v2 is fast, lightweight, and creates 384-dimensional vectors
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def embed_and_store(self, text: str, user_id: str):
        """
        Generates a 384-dim embedding for `text` and stores it in the
        knowledge_base table alongside the raw content and user_id.
        """
        embedding = self.model.encode(text)
        # pgvector expects a Python list; psycopg2 will cast it to VECTOR(384)
        embedding_list = embedding.tolist()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO knowledge_base (user_id, content, embedding) VALUES (%s, %s, %s::vector)",
                (user_id, text, str(embedding_list))
            )
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def retrieve_context(self, query: str, user_id: str, top_k: int = 3) -> list:
        """
        Uses pgvector cosine similarity (<=> operator) to find the top_k most
        semantically relevant documents for the given query.
        Returns a list of content strings.
        """
        query_embedding = self.model.encode(query).tolist()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # <=> is cosine distance in pgvector (lower = more similar)
            cursor.execute(
                "SELECT content FROM knowledge_base WHERE user_id = %s ORDER BY embedding <=> %s::vector LIMIT %s",
                (user_id, str(query_embedding), top_k)
            )
            rows = cursor.fetchall()
            
            if not rows:
                return ["No relevant business knowledge found in the semantic index."]
                
            return [row[0] for row in rows]
        finally:
            cursor.close()
            conn.close()

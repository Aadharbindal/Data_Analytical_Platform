class RAGEngine:
    """
    Retrieval Augmented Generation engine using pgvector for grounding.
    For the MVP, this acts as an in-memory knowledge base.
    """
    
    def __init__(self):
        # Simulated embedded knowledge chunks
        self.embeddings_db = [
            {"id": "doc1", "text": "The definition of an Active Customer is a user who has logged in or made a purchase within the last 30 days."},
            {"id": "doc2", "text": "Customer Acquisition Cost (CAC) is calculated by dividing total marketing spend by the number of new customers."},
            {"id": "doc3", "text": "Our primary target market is mid-sized SaaS companies in North America."},
            {"id": "doc4", "text": "Revenue is recognized on a monthly basis when the service is delivered, not when the cash is collected."}
        ]

    def embed_and_store(self, document_id: str, text: str):
        """Generates embeddings and stores them in pgvector."""
        self.embeddings_db.append({
            "id": document_id,
            "text": text,
        })

    def retrieve_context(self, query: str, top_k: int = 3) -> list:
        """
        Simulates a semantic similarity search. 
        In production, this will embed the query and use cosine similarity in pgvector.
        """
        q_lower = query.lower()
        results = []
        
        # Simple keyword matching to simulate semantic retrieval
        for doc in self.embeddings_db:
            words = [w for w in q_lower.split() if len(w) > 3]
            if any(w in doc["text"].lower() for w in words):
                results.append(doc["text"])
                
        if not results:
            return ["No relevant business knowledge found in the semantic index."]
            
        return results[:top_k]

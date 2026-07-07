from abc import ABC, abstractmethod
from typing import List, Dict, Any
import numpy as np

class BaseEmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""
    
    @abstractmethod
    def generate_embeddings(self, texts: List[str], model_name: str, **kwargs) -> List[List[float]]:
        pass
        
    @abstractmethod
    def get_dimensions(self, model_name: str) -> int:
        pass

class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """Implementation for OpenAI embeddings."""
    
    def generate_embeddings(self, texts: List[str], model_name: str, **kwargs) -> List[List[float]]:
        # In a real scenario, this would call the OpenAI API.
        # client = OpenAI(api_key=...)
        # response = client.embeddings.create(input=texts, model=model_name)
        # return [item.embedding for item in response.data]
        
        # Mocking the generation for now
        dims = self.get_dimensions(model_name)
        return [np.random.rand(dims).tolist() for _ in texts]
        
    def get_dimensions(self, model_name: str) -> int:
        if model_name == "text-embedding-3-small":
            return 1536
        elif model_name == "text-embedding-3-large":
            return 3072
        return 1536 # Default

class LocalEmbeddingProvider(BaseEmbeddingProvider):
    """Implementation for local embeddings (e.g. Sentence Transformers, Ollama)."""
    
    def generate_embeddings(self, texts: List[str], model_name: str, **kwargs) -> List[List[float]]:
        # In a real scenario, this would load a local model
        # model = SentenceTransformer(model_name)
        # return model.encode(texts).tolist()
        
        dims = self.get_dimensions(model_name)
        return [np.random.rand(dims).tolist() for _ in texts]
        
    def get_dimensions(self, model_name: str) -> int:
        if "minilm" in model_name.lower():
            return 384
        elif "bge" in model_name.lower():
            return 768
        return 384

class EmbeddingProviderFactory:
    @staticmethod
    def get_provider(provider_name: str) -> BaseEmbeddingProvider:
        if provider_name.lower() == "openai":
            return OpenAIEmbeddingProvider()
        elif provider_name.lower() in ["local", "sentence_transformers", "ollama"]:
            return LocalEmbeddingProvider()
        else:
            raise ValueError(f"Unsupported embedding provider: {provider_name}")

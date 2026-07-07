from abc import ABC, abstractmethod
from typing import Any, Dict, List
import pandas as pd
import io

class BaseConnector(ABC):
    """Base interface for all data connectors."""
    
    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def fetch_data(self) -> pd.DataFrame:
        pass

class CSVConnector(BaseConnector):
    """Connector for handling CSV file uploads."""
    
    def __init__(self, file_content: bytes):
        self.file_content = file_content

    def connect(self) -> bool:
        return True

    def fetch_data(self) -> pd.DataFrame:
        # Assuming utf-8 for now, robust implementation would detect encoding
        return pd.read_csv(io.BytesIO(self.file_content))

class ConnectorFactory:
    @staticmethod
    def get_connector(source_type: str, **kwargs) -> BaseConnector:
        if source_type == "csv":
            return CSVConnector(file_content=kwargs.get("file_content"))
        # Future: elif source_type == "snowflake": return SnowflakeConnector(...)
        raise ValueError(f"Unsupported connector type: {source_type}")

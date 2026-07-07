from app.repositories.sql_agent_repository import SQLAgentRepository
from app.schemas.sql_agent import SchemaMetadataResponse
from typing import List

class SchemaExplorer:
    def __init__(self, repo: SQLAgentRepository):
        self.repo = repo

    def get_schema(self, workspace_id: str) -> List[SchemaMetadataResponse]:
        """
        Discovers tables, views, columns, and relations.
        """
        metadata = self.repo.get_schema_metadata(workspace_id)
        return [
            SchemaMetadataResponse(
                workspace_id=m.workspace_id,
                schema_name=m.schema_name,
                table_name=m.table_name,
                columns=m.columns,
                primary_keys=m.primary_keys,
                foreign_keys=m.foreign_keys
            )
            for m in metadata
        ]

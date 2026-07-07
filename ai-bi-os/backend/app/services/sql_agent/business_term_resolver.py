from app.repositories.sql_agent_repository import SQLAgentRepository
from app.schemas.sql_agent import BusinessGlossaryEntry
from typing import List

class BusinessTermResolver:
    def __init__(self, repo: SQLAgentRepository):
        self.repo = repo

    def resolve(self, workspace_id: str, user_request: str) -> List[BusinessGlossaryEntry]:
        """
        Extracts business terms from the request and maps them to DB entities.
        """
        glossary = self.repo.get_glossary(workspace_id)
        resolved = []
        lower_req = user_request.lower()
        
        for term in glossary:
            if term.term.lower() in lower_req:
                resolved.append(
                    BusinessGlossaryEntry(
                        workspace_id=term.workspace_id,
                        term=term.term,
                        description=term.description,
                        mapped_schema=term.mapped_schema,
                        mapped_table=term.mapped_table,
                        mapped_column=term.mapped_column
                    )
                )
        return resolved

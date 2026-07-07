from typing import List
from app.schemas.evidence import EvidenceObjectResponse

class EvidenceAggregator:
    def __init__(self):
        pass

    def aggregate(self, evidence_list: List[EvidenceObjectResponse]) -> EvidenceObjectResponse:
        """
        Takes multiple pieces of evidence and groups them.
        (Implementation left as stub for MVP)
        """
        if not evidence_list:
            raise ValueError("No evidence to aggregate")
        return evidence_list[0]

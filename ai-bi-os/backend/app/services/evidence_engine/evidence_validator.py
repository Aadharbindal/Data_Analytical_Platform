from typing import Dict, Any
from app.schemas.evidence import EvidenceObjectResponse

class EvidenceValidator:
    def __init__(self):
        pass

    def validate(self, evidence: EvidenceObjectResponse) -> bool:
        """
        Validates if evidence meets the hard requirements.
        """
        if not evidence.payload.supporting_metrics and \
           not evidence.payload.supporting_statistics and \
           not evidence.payload.supporting_objects:
            # Cannot be valid evidence without supporting items
            return False
            
        if evidence.evidence_confidence < 0.3:
            return False
            
        return True

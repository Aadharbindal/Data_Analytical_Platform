import pandas as pd

class KeyDetectionService:
    """
    Detects Primary and Foreign Key candidates.
    """
    
    @staticmethod
    def detect_keys(series: pd.Series, column_name: str) -> dict:
        is_unique = series.is_unique
        is_nullable = series.isnull().any()
        
        # Primary Key Candidate: Must be unique, not null, and usually has 'id' or 'key' in name.
        # Alternatively, if it's purely unique and non-null it's a strong candidate.
        is_pk_candidate = False
        if is_unique and not is_nullable:
            if 'id' in column_name.lower() or 'key' in column_name.lower() or 'uuid' in column_name.lower():
                is_pk_candidate = True
        
        # Foreign Key Candidate: Usually has 'id' in name but is NOT unique (many-to-one).
        is_fk_candidate = False
        if 'id' in column_name.lower() and not is_unique:
            # We filter out typical PK names like `id` alone for the table.
            if column_name.lower() != 'id':
                is_fk_candidate = True
                
        return {
            "is_unique": bool(is_unique),
            "is_pk_candidate": bool(is_pk_candidate),
            "is_fk_candidate": bool(is_fk_candidate)
        }

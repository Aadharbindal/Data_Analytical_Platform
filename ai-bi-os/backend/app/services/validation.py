import pandas as pd
import re

class DataValidator:
    """Validates datasets and masks Personally Identifiable Information (PII)."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        
        # Simple regex patterns for MVP
        self.pii_patterns = {
            "email": re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"),
            "ssn": re.compile(r"^\d{3}-\d{2}-\d{4}$")
        }

    def _detect_pii_column(self, col: str) -> str:
        """Detects if a column predominantly contains PII data based on sampling."""
        # Check column name first
        col_lower = col.lower()
        if "email" in col_lower:
            return "email"
        if "ssn" in col_lower or "social security" in col_lower:
            return "ssn"
            
        # Sample data if column name isn't obvious
        sample = self.df[col].dropna().head(100).astype(str)
        if sample.empty:
            return None
            
        for pii_type, pattern in self.pii_patterns.items():
            matches = sample.str.match(pattern).sum()
            if matches > len(sample) * 0.5:  # 50% threshold
                return pii_type
                
        return None

    def mask_pii(self) -> pd.DataFrame:
        """Applies masking to detected PII columns."""
        masked_df = self.df.copy()
        
        for col in masked_df.columns:
            pii_type = self._detect_pii_column(col)
            if pii_type == "email":
                # Mask email: preserve domain, hash username
                masked_df[col] = masked_df[col].astype(str).apply(
                    lambda x: "***@" + x.split("@")[1] if "@" in x else "***"
                )
            elif pii_type == "ssn":
                masked_df[col] = "***-**-****"
                
        return masked_df

    def validate(self) -> pd.DataFrame:
        """Runs full validation pipeline (clean, drop empty, mask PII)."""
        # Basic cleaning
        df_clean = self.df.dropna(how="all", axis=1)  # Drop fully empty columns
        df_clean = df_clean.dropna(how="all", axis=0)  # Drop fully empty rows
        
        # Mask PII
        validator = DataValidator(df_clean)
        return validator.mask_pii()

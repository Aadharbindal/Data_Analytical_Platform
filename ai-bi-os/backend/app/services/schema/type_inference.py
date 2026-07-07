import re
import pandas as pd
from typing import Optional

class TypeInferenceService:
    """
    Advanced data type inference going beyond simple Pandas dtypes.
    """
    
    @staticmethod
    def infer_semantic_type(series: pd.Series) -> str:
        """Infers the business/semantic data type of a pandas Series."""
        
        # 1. Base Pandas Type Check
        dtype = str(series.dtype)
        
        # Dropna for sample checking
        sample = series.dropna()
        if sample.empty:
            return "Unknown"
            
        # 2. Check for Booleans
        if dtype == "bool" or sample.isin([True, False, 'True', 'False', 'true', 'false', 1, 0, '1', '0']).all():
            return "Boolean"
            
        # 3. Check for Dates
        if 'datetime' in dtype:
            return "Datetime"
            
        # Try attempting to convert a sample to datetime if it's an object string
        if dtype == 'object':
            # Fast check: does the string look like a date?
            # 2023-01-01, 10/12/2020
            date_regex = re.compile(r'^\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}')
            if sample.astype(str).str.match(date_regex).mean() > 0.8:
                return "Date"
        
        # 4. Check Strings for complex types
        if dtype == 'object':
            # Email Check
            email_regex = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')
            if sample.astype(str).str.match(email_regex).mean() > 0.8:
                return "Email"
                
            # URL Check
            url_regex = re.compile(r'^https?://')
            if sample.astype(str).str.match(url_regex).mean() > 0.8:
                return "URL"
                
            # UUID Check
            uuid_regex = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)
            if sample.astype(str).str.match(uuid_regex).mean() > 0.8:
                return "UUID"
                
            # IP Check
            ip_regex = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
            if sample.astype(str).str.match(ip_regex).mean() > 0.8:
                return "IP Address"
                
            # Categorical Check (Low Cardinality String)
            unique_ratio = len(sample.unique()) / len(sample)
            if unique_ratio < 0.05 and len(sample.unique()) < 50:
                return "Categorical"
                
            return "Text"
            
        # 5. Numerics
        if 'int' in dtype:
            # Check for zip codes
            if sample.astype(str).str.match(r'^\d{5}$').mean() > 0.8:
                return "ZIP Code"
            return "Integer"
            
        if 'float' in dtype:
            # Lat / Long heuristics (ranges)
            if sample.min() >= -90 and sample.max() <= 90 and 'lat' in series.name.lower():
                return "Latitude"
            if sample.min() >= -180 and sample.max() <= 180 and ('lon' in series.name.lower() or 'lng' in series.name.lower()):
                return "Longitude"
            return "Float"

        return "Unknown"

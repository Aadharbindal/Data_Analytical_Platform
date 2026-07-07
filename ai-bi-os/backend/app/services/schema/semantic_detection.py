import re

class SemanticDetectionService:
    """
    Detects business meaning and classifies columns (Dimensions/Measures).
    """
    
    # Dictionary mappings for common business terms
    SEMANTIC_MAPPINGS = {
        r'cust(?:omer)?_id': 'Customer ID',
        r'emp(?:loyee)?_id': 'Employee ID',
        r'prod(?:uct)?_id': 'Product ID',
        r'sku': 'Product SKU',
        r'rev(?:enue)?': 'Revenue',
        r'amt': 'Amount',
        r'qty|quantity': 'Quantity',
        r'gmv': 'Gross Merchandise Value',
        r'mrr': 'Monthly Recurring Revenue',
        r'arr': 'Annual Recurring Revenue',
        r'txn(?:_id)?': 'Transaction ID',
        r'margin': 'Profit Margin',
        r'desc(?:ription)?': 'Description'
    }

    @classmethod
    def infer_business_meaning(cls, column_name: str) -> str:
        col_lower = column_name.lower().replace(" ", "_")
        
        for pattern, meaning in cls.SEMANTIC_MAPPINGS.items():
            if re.search(f'^{pattern}$', col_lower):
                return meaning
                
        # Fallback: title case the normalized name
        return column_name.replace("_", " ").title()

    @classmethod
    def classify_column(cls, column_name: str, semantic_type: str, business_meaning: str) -> str:
        col_lower = column_name.lower()
        
        # 1. Identifiers
        if 'id' in col_lower or 'sku' in col_lower or semantic_type == 'UUID':
            return "Identifier"
            
        # 2. Financial / Measures
        measure_keywords = ['rev', 'amt', 'qty', 'price', 'cost', 'margin', 'gmv', 'mrr', 'arr', 'discount', 'tax']
        if any(kw in col_lower for kw in measure_keywords) or semantic_type in ['Float', 'Integer']:
            # If it's an integer but low cardinality, it might be a dimension. 
            # We assume it's a measure for keyword matches.
            return "Measure"
            
        # 3. Timestamps
        if semantic_type in ['Datetime', 'Date'] or 'time' in col_lower or 'date' in col_lower:
            return "Timestamp"
            
        # 4. Geographic
        geo_keywords = ['country', 'state', 'city', 'region', 'zip', 'lat', 'lon', 'address']
        if any(kw in col_lower for kw in geo_keywords) or semantic_type in ['Latitude', 'Longitude', 'ZIP Code']:
            return "Geographic"
            
        # 5. Dimensions
        if semantic_type in ['Categorical', 'Boolean', 'Text']:
            return "Dimension"
            
        return "Unknown"

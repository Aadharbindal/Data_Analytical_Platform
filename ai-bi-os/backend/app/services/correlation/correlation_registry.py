import logging

logger = logging.getLogger("CorrelationRegistry")

class CorrelationRegistry:
    """
    Dictates the appropriate statistical method based on variable data types.
    """
    
    def determine_method(self, dtype_x: str, dtype_y: str) -> str:
        """
        Determines the correct correlation/association method based on types.
        """
        numeric_types = {"NUMERIC", "INTEGER", "FLOAT", "DOUBLE"}
        categorical_types = {"VARCHAR", "TEXT", "STRING", "CATEGORY", "NOMINAL", "ORDINAL"}
        binary_types = {"BOOLEAN", "BOOL", "BINARY"}
        
        x_is_num = dtype_x.upper() in numeric_types
        y_is_num = dtype_y.upper() in numeric_types
        x_is_cat = dtype_x.upper() in categorical_types
        y_is_cat = dtype_y.upper() in categorical_types
        x_is_bin = dtype_x.upper() in binary_types
        y_is_bin = dtype_y.upper() in binary_types
        
        if x_is_num and y_is_num:
            return "PEARSON" # or SPEARMAN depending on distribution, default Pearson for MVP
        elif x_is_cat and y_is_cat:
            return "CRAMERS_V"
        elif (x_is_num and y_is_cat) or (y_is_num and x_is_cat):
            return "POINT_BISERIAL" # Assuming the categorical is binary. If multiclass, ANOVA/Eta-squared
        elif x_is_bin and y_is_bin:
            return "PHI_COEFFICIENT"
        elif (x_is_num and y_is_bin) or (y_is_num and x_is_bin):
            return "POINT_BISERIAL"
            
        return "UNKNOWN"

correlation_registry = CorrelationRegistry()

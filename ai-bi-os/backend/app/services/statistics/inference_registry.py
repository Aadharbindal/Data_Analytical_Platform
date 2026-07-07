import logging

logger = logging.getLogger("InferenceRegistry")

class InferenceRegistry:
    """
    Dictates the appropriate statistical tests and methods based on data assumptions.
    """
    
    def determine_hypothesis_test(self, groups_count: int, normal: bool, equal_variance: bool, paired: bool = False) -> str:
        """
        Decision tree for hypothesis testing.
        """
        if groups_count == 1:
            if normal:
                return "ONE_SAMPLE_T_TEST"
            else:
                return "WILCOXON_SIGNED_RANK"
        elif groups_count == 2:
            if paired:
                if normal:
                    return "PAIRED_T_TEST"
                else:
                    return "WILCOXON_SIGNED_RANK"
            else:
                if normal and equal_variance:
                    return "TWO_SAMPLE_T_TEST_EQUAL_VAR"
                elif normal and not equal_variance:
                    return "WELCH_T_TEST"
                else:
                    return "MANN_WHITNEY_U"
        elif groups_count > 2:
            if normal and equal_variance:
                return "ANOVA"
            else:
                return "KRUSKAL_WALLIS"
                
        return "UNKNOWN"

inference_registry = InferenceRegistry()

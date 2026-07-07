import logging
from typing import List, Dict, Optional

logger = logging.getLogger("MetricRegistry")

# Pre-seeded core operational metrics to prove the architecture
_CORE_METRICS = [
    {
        "id": "active_customers",
        "name": "Active Customers",
        "domain": "Sales",
        "description": "Number of unique customers who placed an order in the given time window.",
        "supported_dimensions": ["Region", "Store", "Date"],
        "supported_time_windows": ["Daily", "Weekly", "Monthly", "Yearly"],
        "formula": "COUNT(DISTINCT customer_id)"
    },
    {
        "id": "new_customers",
        "name": "New Customers",
        "domain": "Sales",
        "description": "Number of unique customers whose first order was in the given time window.",
        "supported_dimensions": ["Region", "Store", "Date"],
        "supported_time_windows": ["Daily", "Weekly", "Monthly", "Yearly"],
        "formula": "COUNT(DISTINCT CASE WHEN is_first_order = true THEN customer_id ELSE NULL END)"
    },
    {
        "id": "average_basket_size",
        "name": "Average Basket Size",
        "domain": "Sales",
        "description": "Average number of items per order.",
        "supported_dimensions": ["Region", "Store", "Date"],
        "supported_time_windows": ["Daily", "Weekly", "Monthly", "Yearly"],
        "formula": "AVG(items_per_order)"
    },
    {
        "id": "inventory_days",
        "name": "Inventory Days",
        "domain": "Inventory",
        "description": "Estimated number of days the current inventory will last based on run rate.",
        "supported_dimensions": ["Product", "Category", "Store", "Date"],
        "supported_time_windows": ["Daily", "Weekly"],
        "formula": "SUM(stock_level) / AVG(daily_sales)"
    },
    {
        "id": "support_response_time",
        "name": "Support Response Time",
        "domain": "Support",
        "description": "Average time to first response in hours.",
        "supported_dimensions": ["Region", "Employee", "Date"],
        "supported_time_windows": ["Daily", "Weekly", "Monthly"],
        "formula": "AVG(time_to_first_response_hours)"
    }
]

class MetricRegistry:
    """Loads and provides access to standard operational metrics across domains."""
    
    def __init__(self):
        self._metrics: Dict[str, dict] = {}
        self.initialize()
        
    def initialize(self):
        for m in _CORE_METRICS:
            self._metrics[m["id"]] = m
            
    def get_metric(self, metric_id: str) -> Optional[dict]:
        return self._metrics.get(metric_id)
        
    def get_all_metrics(self) -> List[dict]:
        return list(self._metrics.values())
        
    def get_metrics_by_domain(self, domain: str) -> List[dict]:
        return [m for m in self._metrics.values() if m["domain"].lower() == domain.lower()]

metric_registry = MetricRegistry()

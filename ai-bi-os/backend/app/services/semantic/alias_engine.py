class AliasEngine:
    """Translates technical column names to Business Glossary Terms."""
    
    DICTIONARY = {
        # Entities & Identifiers
        "cust": "Customer", "customer": "Customer", "client": "Customer", "buyer": "Customer",
        "cust_id": "Customer Identifier", "customer_number": "Customer Identifier",
        "emp": "Employee", "employee": "Employee", "staff": "Employee",
        "employee_id": "Employee Identifier",
        "prod": "Product", "product": "Product", "item": "Product",
        "sku": "Product SKU", "item_code": "Product SKU",
        "inv": "Invoice", "invoice": "Invoice", "invoice_id": "Invoice Identifier",
        "ord": "Order", "order": "Order", "order_id": "Order Identifier",
        "txn": "Transaction", "txn_id": "Transaction Identifier",
        
        # Financial Metrics
        "rev": "Revenue", "revenue": "Revenue", "sales": "Revenue", "income": "Revenue", "earning": "Revenue",
        "profit": "Profit", "margin": "Profit Margin",
        "gmv": "Gross Merchandise Value",
        "mrr": "Monthly Recurring Revenue",
        "arr": "Annual Recurring Revenue",
        "tax": "Tax", "discount": "Discount", "refund": "Refund",
        "cost": "Cost", "expense": "Expense", "salary": "Salary",
        "shipping_cost": "Shipping Cost",
        
        # Operational Metrics
        "qty": "Quantity", "quantity": "Quantity", "units": "Quantity", "count": "Quantity",
        
        # Dimensions
        "dept": "Department", "department": "Department",
        "reg": "Region", "region": "Geographic Region",
        "state": "State", "country": "Country", "city": "City",
        "zip": "Postal Code", "zipcode": "Postal Code", "postal_code": "Postal Code",
        
        # Time
        "date": "Date", "txn_date": "Transaction Date", "created_at": "Creation Timestamp", "updated_at": "Update Timestamp"
    }
    
    @staticmethod
    def resolve_alias(raw_column_name: str) -> str:
        # Normalize
        normalized = str(raw_column_name).lower().strip()
        
        # Exact match
        if normalized in AliasEngine.DICTIONARY:
            return AliasEngine.DICTIONARY[normalized]
            
        # Substring heuristics
        for key, value in AliasEngine.DICTIONARY.items():
            if key in normalized:
                return value
                
        # Fallback to Title Cased original if no match found
        return raw_column_name.replace("_", " ").title()

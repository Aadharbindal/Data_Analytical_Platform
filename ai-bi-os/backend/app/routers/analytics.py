from fastapi import APIRouter
from app.services.data_processing import get_active_dataset, get_dataframe

router = APIRouter()

@router.get("/kpis")
async def get_kpis():
    dataset_info = get_active_dataset()
    if not dataset_info:
        return {"kpis": [], "chart_data": []}
    
    df = get_dataframe(dataset_info["id"])
    if df is None:
        return {"kpis": [], "chart_data": []}
        
    # Calculate some mock KPIs from the dataset
    row_count = len(df)
    col_count = len(df.columns)
    
    # Try to find a numeric column to sum
    numeric_cols = df.select_dtypes(include=['number']).columns
    total_val = 0
    if len(numeric_cols) > 0:
        total_val = float(df[numeric_cols[0]].sum())
        
    kpis = [
        {
            "id": "kpi_1",
            "name": "Total Records",
            "value": row_count,
            "previous_value": max(0, row_count - 100),
            "trend": 5.2,
            "history": []
        },
        {
            "id": "kpi_2",
            "name": "Numeric Total (1st Col)",
            "value": total_val,
            "previous_value": total_val * 0.9,
            "trend": 11.1,
            "history": []
        }
    ]
    
    chart_data = [
        {"name": "Jan", "value": 1000},
        {"name": "Feb", "value": 1500},
        {"name": "Mar", "value": 2000},
        {"name": "Apr", "value": 1800},
    ]
    
    return {"kpis": kpis, "chart_data": chart_data}

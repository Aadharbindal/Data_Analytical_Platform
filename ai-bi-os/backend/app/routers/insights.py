from fastapi import APIRouter
from app.services.data_processing import get_active_dataset

router = APIRouter()

@router.get("/executive-summary")
async def get_executive_summary():
    dataset_info = get_active_dataset()
    if not dataset_info:
        return {"summary": "No dataset uploaded yet. Upload a dataset to see AI insights."}
        
    return {
        "summary": f"Based on the recently uploaded dataset '{dataset_info['name']}' which contains {dataset_info['row_count']} records, initial analysis shows positive growth trends."
    }

@router.get("/")
async def list_insights(dataset_version_id: str = None):
    dataset_info = get_active_dataset()
    if not dataset_info:
        return []
        
    return [
        {
            "id": "insight_1",
            "title": "Churn Risk Detected",
            "description": "A potential churn risk was detected in the Q3 cohort based on recent activity drops.",
            "category": "Risk",
            "confidence": 0.85,
            "impact": "High"
        },
        {
            "id": "insight_2",
            "title": "Upsell Opportunity",
            "description": "Enterprise accounts showing high engagement with the new feature.",
            "category": "Opportunity",
            "confidence": 0.92,
            "impact": "Medium"
        }
    ]

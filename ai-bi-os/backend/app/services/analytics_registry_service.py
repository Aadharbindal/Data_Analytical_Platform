from sqlalchemy.orm import Session
from typing import List, Optional, Tuple, Dict, Any
from app.repositories.analytics_registry_repository import AnalyticsRegistryRepository
from app.schemas.analytics_registry import (
    AnalyticsObjectCreate, AnalyticsObjectUpdate, ObjectSearchRequest,
    AnalyticsObjectResponse, LineageResponse, LineageNode, ObjectStatus
)
from app.services.analytics_registry_cache import analytics_cache

class AnalyticsRegistryService:
    def __init__(self, db: Session):
        self.repo = AnalyticsRegistryRepository(db)

    def register_object(self, obj_in: AnalyticsObjectCreate) -> AnalyticsObjectResponse:
        db_obj = self.repo.create(obj_in)
        response_obj = AnalyticsObjectResponse.model_validate(db_obj)
        analytics_cache.set_object(response_obj)
        return response_obj

    def bulk_register(self, objects_in: List[AnalyticsObjectCreate]) -> List[AnalyticsObjectResponse]:
        responses = []
        for obj_in in objects_in:
            db_obj = self.repo.create(obj_in)
            response_obj = AnalyticsObjectResponse.model_validate(db_obj)
            analytics_cache.set_object(response_obj)
            responses.append(response_obj)
        return responses

    def get_object(self, object_id: str) -> Optional[AnalyticsObjectResponse]:
        # Try Cache First
        cached_obj = analytics_cache.get_object(object_id)
        if cached_obj:
            return cached_obj

        db_obj = self.repo.get_by_id(object_id)
        if db_obj:
            response_obj = AnalyticsObjectResponse.model_validate(db_obj)
            analytics_cache.set_object(response_obj)
            return response_obj
        return None

    def search_objects(self, search_req: ObjectSearchRequest) -> Tuple[List[AnalyticsObjectResponse], int]:
        objects, total = self.repo.search(search_req)
        return [AnalyticsObjectResponse.model_validate(obj) for obj in objects], total

    def update_object(self, object_id: str, obj_in: AnalyticsObjectUpdate, actor_id: str) -> Optional[AnalyticsObjectResponse]:
        db_obj = self.repo.get_by_id(object_id)
        if not db_obj:
            return None
        updated_obj = self.repo.update(db_obj, obj_in, actor_id=actor_id)
        response_obj = AnalyticsObjectResponse.model_validate(updated_obj)
        
        # Invalidate/Update Cache
        analytics_cache.set_object(response_obj)
        return response_obj

    def get_lineage(self, object_id: str) -> Optional[LineageResponse]:
        db_obj = self.repo.get_by_id(object_id)
        if not db_obj:
            return None
            
        lineage_data = self.repo.get_lineage(object_id)
        
        def _to_node(obj) -> LineageNode:
            return LineageNode(
                object_id=obj.id,
                object_type=obj.object_type,
                status=obj.status.value
            )
            
        return LineageResponse(
            object_id=object_id,
            parents=[_to_node(p) for p in lineage_data["parents"]],
            children=[_to_node(c) for c in lineage_data["children"]],
            dependencies=[_to_node(d) for d in lineage_data["dependencies"]],
            dependents=[_to_node(d) for d in lineage_data["dependents"]]
        )

    def archive_object(self, object_id: str, actor_id: str) -> bool:
        db_obj = self.repo.get_by_id(object_id)
        if not db_obj:
            return False
            
        update_data = AnalyticsObjectUpdate(status=ObjectStatus.ARCHIVED)
        self.repo.update(db_obj, update_data, actor_id=actor_id)
        analytics_cache.invalidate_object(object_id)
        return True

    def restore_object(self, object_id: str, actor_id: str) -> bool:
        db_obj = self.repo.get_by_id(object_id)
        if not db_obj:
            return False
            
        update_data = AnalyticsObjectUpdate(status=ObjectStatus.ACTIVE)
        self.repo.update(db_obj, update_data, actor_id=actor_id)
        analytics_cache.invalidate_object(object_id)
        return True

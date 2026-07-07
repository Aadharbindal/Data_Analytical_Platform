from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, desc
from app.models.analytics_registry import (
    AnalyticsObject, ObjectMetadata, ObjectDependency, 
    ObjectVersion, ObjectHistory, ObjectRelationship, 
    ObjectTag, ObjectStatus, ValidationStatus
)
from app.schemas.analytics_registry import AnalyticsObjectCreate, AnalyticsObjectUpdate, ObjectSearchRequest

class AnalyticsRegistryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, object_id: str) -> Optional[AnalyticsObject]:
        return self.db.query(AnalyticsObject).options(
            joinedload(AnalyticsObject.tags),
            joinedload(AnalyticsObject.versions),
            joinedload(AnalyticsObject.metadata_info)
        ).filter(AnalyticsObject.id == object_id).first()

    def create(self, obj_in: AnalyticsObjectCreate) -> AnalyticsObject:
        db_obj = AnalyticsObject(
            object_type=obj_in.object_type,
            workspace_id=obj_in.workspace_id,
            dataset_id=obj_in.dataset_id,
            dataset_version_id=obj_in.dataset_version_id,
            pipeline_run_id=obj_in.pipeline_run_id,
            engine_name=obj_in.engine_name,
            engine_version=obj_in.engine_version,
            created_by=obj_in.created_by,
            confidence_score=obj_in.confidence_score,
            quality_score=obj_in.quality_score,
            business_domain=obj_in.business_domain,
            payload=obj_in.payload
        )
        self.db.add(db_obj)
        self.db.flush()

        # Add tags
        for tag_name in obj_in.tags:
            tag = ObjectTag(object_id=db_obj.id, tag_name=tag_name)
            self.db.add(tag)

        # Add metadata
        if obj_in.metadata_json:
            meta = ObjectMetadata(object_id=db_obj.id, metadata_json=obj_in.metadata_json)
            self.db.add(meta)

        # Add dependencies
        for dep in obj_in.dependencies:
            db_dep = ObjectDependency(
                source_object_id=db_obj.id,
                target_object_id=dep.target_object_id,
                dependency_type=dep.dependency_type
            )
            self.db.add(db_dep)

        # Add parent relationships
        for parent_id in obj_in.parent_ids:
            rel = ObjectRelationship(
                parent_id=parent_id,
                child_id=db_obj.id,
                relationship_type="derived_from"
            )
            self.db.add(rel)

        # Initial Version
        initial_version = ObjectVersion(
            object_id=db_obj.id,
            major_version=1,
            minor_version=0,
            payload_snapshot=obj_in.payload
        )
        self.db.add(initial_version)

        # Initial History
        history = ObjectHistory(
            object_id=db_obj.id,
            action="CREATED",
            actor_id=obj_in.created_by,
            details={"message": "Object registered"}
        )
        self.db.add(history)

        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: AnalyticsObject, obj_in: AnalyticsObjectUpdate, actor_id: str) -> AnalyticsObject:
        update_data = obj_in.model_dump(exclude_unset=True)
        
        create_new_version = False
        if "payload" in update_data and update_data["payload"] != db_obj.payload:
            create_new_version = True

        for field, value in update_data.items():
            if field == "tags":
                self.db.query(ObjectTag).filter(ObjectTag.object_id == db_obj.id).delete()
                for tag_name in value:
                    self.db.add(ObjectTag(object_id=db_obj.id, tag_name=tag_name))
            else:
                setattr(db_obj, field, value)

        if create_new_version:
            latest_version = self.db.query(ObjectVersion).filter(
                ObjectVersion.object_id == db_obj.id
            ).order_by(desc(ObjectVersion.major_version), desc(ObjectVersion.minor_version)).first()
            
            new_minor = (latest_version.minor_version + 1) if latest_version else 1
            major = latest_version.major_version if latest_version else 1
            
            new_version = ObjectVersion(
                object_id=db_obj.id,
                major_version=major,
                minor_version=new_minor,
                payload_snapshot=update_data["payload"]
            )
            self.db.add(new_version)

        history = ObjectHistory(
            object_id=db_obj.id,
            action="UPDATED",
            actor_id=actor_id,
            details={"fields_updated": list(update_data.keys())}
        )
        self.db.add(history)

        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def search(self, search_req: ObjectSearchRequest) -> Tuple[List[AnalyticsObject], int]:
        query = self.db.query(AnalyticsObject)
        
        if search_req.workspace_id:
            query = query.filter(AnalyticsObject.workspace_id == search_req.workspace_id)
        if search_req.dataset_id:
            query = query.filter(AnalyticsObject.dataset_id == search_req.dataset_id)
        if search_req.object_type:
            query = query.filter(AnalyticsObject.object_type == search_req.object_type)
        if search_req.engine_name:
            query = query.filter(AnalyticsObject.engine_name == search_req.engine_name)
        if search_req.status:
            query = query.filter(AnalyticsObject.status == search_req.status)
        if search_req.business_domain:
            query = query.filter(AnalyticsObject.business_domain == search_req.business_domain)
        if search_req.min_confidence is not None:
            query = query.filter(AnalyticsObject.confidence_score >= search_req.min_confidence)
        if search_req.min_quality is not None:
            query = query.filter(AnalyticsObject.quality_score >= search_req.min_quality)
            
        if search_req.tags:
            query = query.join(AnalyticsObject.tags).filter(ObjectTag.tag_name.in_(search_req.tags))
            
        total = query.count()
        
        objects = query.order_by(desc(AnalyticsObject.created_at)).offset(search_req.offset).limit(search_req.limit).all()
        return objects, total

    def get_lineage(self, object_id: str) -> Dict[str, List[Any]]:
        # Fetch parents
        parents = self.db.query(AnalyticsObject).join(
            ObjectRelationship, ObjectRelationship.parent_id == AnalyticsObject.id
        ).filter(ObjectRelationship.child_id == object_id).all()
        
        # Fetch children
        children = self.db.query(AnalyticsObject).join(
            ObjectRelationship, ObjectRelationship.child_id == AnalyticsObject.id
        ).filter(ObjectRelationship.parent_id == object_id).all()
        
        # Fetch dependencies
        dependencies = self.db.query(AnalyticsObject).join(
            ObjectDependency, ObjectDependency.target_object_id == AnalyticsObject.id
        ).filter(ObjectDependency.source_object_id == object_id).all()
        
        # Fetch dependents
        dependents = self.db.query(AnalyticsObject).join(
            ObjectDependency, ObjectDependency.source_object_id == AnalyticsObject.id
        ).filter(ObjectDependency.target_object_id == object_id).all()
        
        return {
            "parents": parents,
            "children": children,
            "dependencies": dependencies,
            "dependents": dependents
        }

from sqlalchemy.orm import Session
from typing import List
import time
from app.models.kpi import KPIDefinition, KPIVersion, KPIExecution
from app.services.kpis.kpi_validator import KPIValidator
from app.services.kpis.kpi_calculator import KPICalculator
from app.services.kpis.kpi_cache_manager import KPICacheManager

class KPIOrchestrator:
    """Coordinates the KPI calculation pipeline."""
    
    @staticmethod
    def execute_kpi(db: Session, workspace_id: str, dataset_version_id: str, definition_id: str, dimension: str = None) -> None:
        start_time = time.time()
        
        try:
            definition = db.query(KPIDefinition).filter(KPIDefinition.id == definition_id).first()
            if not definition:
                raise ValueError(f"KPI Definition {definition_id} not found.")
                
            active_version = db.query(KPIVersion).filter(
                KPIVersion.definition_id == definition_id,
                KPIVersion.status == "ACTIVE"
            ).first()
            
            if not active_version:
                raise ValueError(f"No active version found for KPI {definition_id}.")
                
            cache_key = KPICacheManager.generate_cache_key(definition_id, dataset_version_id, dimension)
            
            if KPICacheManager.get_cached_result(db, cache_key):
                # Log cache hit
                execution = KPIExecution(
                    dataset_version_id=dataset_version_id,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    cache_hits=1,
                    status="SUCCESS_CACHED"
                )
                db.add(execution)
                db.commit()
                return
                
            # Execute
            calculations = KPICalculator.calculate(workspace_id, dataset_version_id, definition, active_version, dimension)
            db.add_all(calculations)
            db.flush()
            
            # Cache the result (using the first one as proxy for the batch in this skeleton)
            if calculations:
                KPICacheManager.cache_result(db, cache_key, calculations[0].id)
                
            # Log execution
            execution = KPIExecution(
                dataset_version_id=dataset_version_id,
                execution_time_ms=(time.time() - start_time) * 1000,
                cache_hits=0,
                status="SUCCESS"
            )
            db.add(execution)
            db.commit()
            
        except Exception as e:
            db.rollback()
            execution = KPIExecution(
                dataset_version_id=dataset_version_id,
                execution_time_ms=(time.time() - start_time) * 1000,
                errors={"error": str(e)},
                status="FAILED"
            )
            db.add(execution)
            db.commit()
            raise e

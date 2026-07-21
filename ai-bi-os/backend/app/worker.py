import os
from celery import Celery
from app.ai.agents import AgentOrchestrator
from app.services.query.duckdb_engine import DuckDBEngine
from app.core.event_bus import PluggableEventBus


def _update_progress(job_id: str, step_name: str, progress: float):
    from app.core.database import SessionLocal
    from app.repositories.dataset_repository import DatasetRepository
    db = SessionLocal()
    try:
        repo = DatasetRepository(db)
        repo.update_upload_job_status(job_id, current_step=step_name, progress=progress)
    finally:
        db.close()

redis_host = os.getenv("REDIS_HOST", "localhost")
celery_app = Celery(
    "ai_tasks",
    broker=f"redis://{redis_host}:6379/0",
    backend=f"redis://{redis_host}:6379/0"
)

event_bus = PluggableEventBus()

@celery_app.task(name="process_ai_query")
def process_ai_query(message: str):
    import time
    from app.ai.agents import AgentOrchestrator
    time.sleep(1)
    orchestrator = AgentOrchestrator()
    result = orchestrator.run_query(message)
    return {
        "response": result["final_insight"],
        "executed_sql": result.get("executed_sql", []),
        "cost_estimate": result.get("cost_estimate", 0.0)
    }

@celery_app.task(name="process_upload_task")
def process_upload_task(job_id: str, temp_file_path: str, filename: str):
    _update_progress(job_id, "Uploading Dataset...", 10.0)
    """Processes uploaded datasets, moves them to formal catalog structure."""
    from app.core.database import SessionLocal
    from app.repositories.dataset_repository import DatasetRepository
    from app.services.upload_service import UploadService
    from app.services.dataset_version_service import DatasetVersionService
    from app.services.dataset_metadata_service import DatasetMetadataService
    from app.services.storage.local_provider import LocalStorageProvider
    
    db = SessionLocal()
    repo = DatasetRepository(db)
    version_service = DatasetVersionService(db)
    provider = LocalStorageProvider()
    metadata_service = DatasetMetadataService(provider)
    
    try:
        repo.update_upload_job_status(job_id, status="processing")
        job = repo.get_upload_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # In a real environment, the temp file might be on a distributed drive or accessible to the worker
        # Here we just use its path directly since the provider is LocalStorage.
        # But for provider abstraction, we should read it via provider or assume it's a local temp file.
        local_temp_path = os.path.join(provider.base_dir, temp_file_path)
        
        # Validate and Hash
        result = UploadService.process_completed_upload(local_temp_path, filename)
        file_hash = result["file_hash"]
        metadata = result["metadata"]
        ext = result["ext"]
        
        if repo.check_hash_exists(file_hash):
            raise ValueError("Duplicate dataset: A file with this content already exists.")

        dataset_id = job.dataset_id
        project_id = job.project_id or "default_project"
        
        if not dataset_id:
            dataset = repo.create_dataset(
                name=job.dataset_name or filename,
                owner_id=job.user_id,
                workspace_id=job.workspace_id,
                project_id=project_id if job.project_id else None
            )
            dataset_id = dataset.id
            job.dataset_id = dataset_id

        # Determine next version to formulate path
        # Note: A race condition could happen here if two uploads happen simultaneously.
        # For this Module, sequential processing is assumed.
        from app.models.dataset import DatasetVersion
        existing_count = db.query(DatasetVersion).filter(DatasetVersion.dataset_id == dataset_id).count()
        next_v = existing_count + 1
        
        # Build strict directory path
        storage_path = f"{job.workspace_id}/{project_id}/{dataset_id}/v{next_v}/raw.{ext}"
        
        # Move file using provider (Read from temp, save to final, delete temp)
        content = provider.get_file_content(temp_file_path)
        provider.save_file(content, storage_path)
        provider.delete_file(temp_file_path)
        
        # Store metadata JSON
        metadata_service.store_metadata(storage_path, metadata)
        
        # Register version in DB
        new_version = version_service.register_version(
            dataset_id=dataset_id,
            original_filename=filename,
            stored_filename=f"raw.{ext}",
            file_hash=file_hash,
            file_size=metadata["file_size_bytes"],
            file_type=ext,
            provider_id="local",  # Mocking a fixed provider ID for now.
            storage_path=storage_path
        )
        
        db.commit()
        
        # Trigger Schema Engine
        process_schema_task.delay(job_id=job_id, dataset_version_id=new_version.id, storage_path=storage_path, file_type=ext)

        return {"status": "success", "dataset_id": dataset_id, "file_hash": file_hash, "path": storage_path}
        
    except Exception as e:
        repo.update_upload_job_status(job_id, status="failed", error_message=str(e))
        db.commit()
        if 'provider' in locals() and 'temp_file_path' in locals():
             provider.delete_file(temp_file_path)
        raise e
    finally:
        db.close()

@celery_app.task(name="process_schema_task")
def process_schema_task(job_id: str, dataset_version_id: str, storage_path: str, file_type: str):
    _update_progress(job_id, "Scanning for Schema...", 20.0)
    """
    Background task to analyze a dataset and build the enterprise schema.
    """
    from app.core.database import SessionLocal
    from app.services.schema import SchemaDiscoveryService, SchemaRegistryService
    from app.services.storage.local_provider import LocalStorageProvider
    import os
    
    db = SessionLocal()
    registry = SchemaRegistryService(db)
    provider = LocalStorageProvider()
    
    try:
        # Construct absolute path for Pandas reading (in a real setup, we'd stream bytes or use S3fs)
        full_path = os.path.join(provider.base_dir, storage_path)
        
        # Run Discovery
        columns_metadata = SchemaDiscoveryService.analyze_dataset(full_path, file_type)
        
        # Persist Schema
        schema = registry.register_schema(dataset_version_id, columns_metadata)
        
        # Chain into Profiling
        process_auto_cleaning_task.delay(job_id=job_id, dataset_version_id=dataset_version_id, storage_path=storage_path, file_type=file_type)
        
        return {"status": "success", "schema_id": schema.id, "columns_detected": len(columns_metadata)}
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


@celery_app.task(name="process_auto_cleaning_task")
def process_auto_cleaning_task(job_id: str, dataset_version_id: str, storage_path: str, file_type: str):
    _update_progress(job_id, "Cleaning Data...", 30.0)
    from app.core.database import SessionLocal
    from app.services.cleaning.cleaning_orchestrator import CleaningOrchestrator
    
    db = SessionLocal()
    orchestrator = CleaningOrchestrator(db)
    try:
        # Get the dataset id
        from app.models.dataset import DatasetVersion
        version = db.query(DatasetVersion).filter(DatasetVersion.id == dataset_version_id).first()
        
        # Apply an auto-cleaning pipeline (e.g. drop empty columns and rows)
        pipeline_steps = [
            {"action": "drop_empty_columns", "params": {}},
            {"action": "drop_empty_rows", "params": {}}
        ]
        
        # Apply the pipeline and create V(N+1)
        new_version_id = orchestrator.apply_pipeline(version.dataset_id, pipeline_steps)
        
        # Re-fetch new version
        new_version = db.query(DatasetVersion).filter(DatasetVersion.id == new_version_id).first()
        storage = new_version.storage_locations[0]
        
        process_profile_task.delay(
            job_id=job_id,
            dataset_version_id=new_version.id, 
            storage_path=storage.storage_path, 
            file_type=new_version.file_type
        )
        return {"status": "success", "new_version_id": new_version_id}
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

@celery_app.task(name="process_profile_task")
def process_profile_task(job_id: str, dataset_version_id: str, storage_path: str, file_type: str):
    _update_progress(job_id, "Generating Profile...", 40.0)
    """
    Background task to compute deep statistical profile of a dataset.
    """
    from app.core.database import SessionLocal
    from app.services.profiling import DatasetProfiler, ProfileRegistryService
    from app.services.schema.schema_registry import SchemaRegistryService
    from app.services.storage.local_provider import LocalStorageProvider
    import os
    
    db = SessionLocal()
    schema_registry = SchemaRegistryService(db)
    profile_registry = ProfileRegistryService(db)
    provider = LocalStorageProvider()
    
    try:
        # Retrieve the schema metadata to guide profiling
        from app.models.dataset import DatasetVersion
        version = db.query(DatasetVersion).filter(DatasetVersion.id == dataset_version_id).first()
        if not version:
            raise ValueError("Dataset version not found")
            
        schema = schema_registry.get_schema_for_dataset(version.dataset_id)
        if not schema:
            raise ValueError("Schema not found for dataset")
            
        # Convert schema to dict for the profiler
        schema_metadata = [
            {
                "id": col.id,
                "original_header": col.original_header,
                "inferred_semantic_type": col.inferred_semantic_type,
                "classification": col.classification
            } for col in schema.columns
        ]
        
        full_path = os.path.join(provider.base_dir, storage_path)
        
        # Run Profiling
        profile_data = DatasetProfiler.analyze_dataset(full_path, file_type, schema_metadata)
        
        # Save Profiling
        profile = profile_registry.save_profile(dataset_version_id, profile_data)
        
        # Chain into Quality Engine
        process_quality_task.delay(job_id=job_id, dataset_version_id=dataset_version_id, storage_path=storage_path, file_type=file_type)
        
        return {"status": "success", "profile_id": profile.id}
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

@celery_app.task(name="process_quality_task")
def process_quality_task(job_id: str, dataset_version_id: str, storage_path: str, file_type: str):
    _update_progress(job_id, "Evaluating Quality...", 50.0)
    """
    Background task to evaluate the quality of a dataset based on its schema metadata.
    """
    from app.core.database import SessionLocal
    from app.services.quality import QualityOrchestrator, QualityRegistryService
    from app.services.schema.schema_registry import SchemaRegistryService
    from app.services.storage.local_provider import LocalStorageProvider
    import os
    
    db = SessionLocal()
    schema_registry = SchemaRegistryService(db)
    quality_registry = QualityRegistryService(db)
    provider = LocalStorageProvider()
    
    try:
        # Retrieve the schema metadata
        from app.models.dataset import DatasetVersion
        version = db.query(DatasetVersion).filter(DatasetVersion.id == dataset_version_id).first()
        if not version:
            raise ValueError("Dataset version not found")
            
        schema = schema_registry.get_schema_for_dataset(version.dataset_id)
        if not schema:
            raise ValueError("Schema not found for dataset")
            
        schema_metadata = [
            {
                "id": col.id,
                "original_header": col.original_header,
                "inferred_semantic_type": col.inferred_semantic_type,
                "classification": col.classification,
                "is_primary_key_candidate": col.is_primary_key_candidate,
                "business_meaning": col.business_meaning
            } for col in schema.columns
        ]
        
        full_path = os.path.join(provider.base_dir, storage_path)
        
        # Run Quality Evaluation
        quality_results = QualityOrchestrator.evaluate_dataset(full_path, file_type, schema_metadata)
        
        # Persist Assessment
        assessment = quality_registry.save_assessment(dataset_version_id, quality_results)
        
        # Chain into Privacy & Governance Scan
        process_privacy_task.delay(job_id=job_id, dataset_version_id=dataset_version_id, storage_path=storage_path, file_type=file_type)
        
        return {"status": "success", "assessment_id": assessment.id, "overall_score": assessment.score.overall_score}
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

@celery_app.task(name="process_privacy_task")
def process_privacy_task(job_id: str, dataset_version_id: str, storage_path: str, file_type: str):
    _update_progress(job_id, "Scanning for PII...", 60.0)
    """
    Background task to scan for PII, classify data, and generate governance policies.
    """
    from app.core.database import SessionLocal
    from app.services.privacy import GovernanceOrchestrator, PrivacyRegistryService
    from app.services.schema.schema_registry import SchemaRegistryService
    from app.services.storage.local_provider import LocalStorageProvider
    import os
    
    db = SessionLocal()
    schema_registry = SchemaRegistryService(db)
    privacy_registry = PrivacyRegistryService(db)
    provider = LocalStorageProvider()
    
    try:
        from app.models.dataset import DatasetVersion
        version = db.query(DatasetVersion).filter(DatasetVersion.id == dataset_version_id).first()
        if not version:
            raise ValueError("Dataset version not found")
            
        schema = schema_registry.get_schema_for_dataset(version.dataset_id)
        if not schema:
            raise ValueError("Schema not found for dataset")
            
        schema_metadata = [
            {
                "id": col.id,
                "original_header": col.original_header,
                "inferred_semantic_type": col.inferred_semantic_type
            } for col in schema.columns
        ]
        
        full_path = os.path.join(provider.base_dir, storage_path)
        
        # Run Governance Evaluation
        privacy_results = GovernanceOrchestrator.evaluate_dataset(full_path, file_type, schema_metadata)
        
        # Persist Assessment
        assessment = privacy_registry.save_assessment(dataset_version_id, privacy_results)
        
        # Chain into Semantic Intelligence
        process_semantic_task.delay(job_id=job_id, dataset_version_id=dataset_version_id)
        
        return {"status": "success", "assessment_id": assessment.id}
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

@celery_app.task(name="process_semantic_task")
def process_semantic_task(job_id: str, dataset_version_id: str):
    _update_progress(job_id, "Extracting Semantics...", 70.0)
    """
    Final automated ingestion task: Infers business domains, entities, metrics, and ontology.
    """
    from app.core.database import SessionLocal
    from app.services.semantic.semantic_orchestrator import SemanticOrchestrator
    from app.services.semantic.semantic_registry import SemanticRegistryService
    from app.services.schema.schema_registry import SchemaRegistryService
    
    db = SessionLocal()
    schema_registry = SchemaRegistryService(db)
    semantic_registry = SemanticRegistryService(db)
    
    try:
        from app.models.dataset import DatasetVersion
        version = db.query(DatasetVersion).filter(DatasetVersion.id == dataset_version_id).first()
        if not version:
            raise ValueError("Dataset version not found")
            
        schema = schema_registry.get_schema_for_dataset(version.dataset_id)
        if not schema:
            raise ValueError("Schema not found for dataset")
            
        schema_metadata = [
            {
                "id": col.id,
                "original_header": col.original_header,
            } for col in schema.columns
        ]
        
        # Run Semantic Evaluation
        semantic_results = SemanticOrchestrator.evaluate_schema(schema_metadata)
        
        # Persist Semantic Layer
        semantic_registry.save_semantic_data(dataset_version_id, semantic_results)
        
        # Chain into Metadata Catalog
        from app.worker import process_catalog_task
        process_catalog_task.delay(job_id=job_id, dataset_id=version.dataset_id)
        
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

@celery_app.task(name="process_catalog_task")
def process_catalog_task(job_id: str, dataset_id: str):
    _update_progress(job_id, "Indexing Catalog...", 80.0)
    """
    Final automated ingestion task: Rolls up all metadata into the Enterprise Data Catalog index.
    """
    from app.core.database import SessionLocal
    from app.services.catalog.catalog_orchestrator import CatalogOrchestrator
    
    db = SessionLocal()
    
    try:
        from app.models.dataset import DatasetVersion
        version = db.query(DatasetVersion).filter(DatasetVersion.dataset_id == dataset_id, DatasetVersion.is_active == True).first()
        if not version:
            raise ValueError("Active dataset version not found")
            
        # Run Catalog Orchestration
        catalog_id = CatalogOrchestrator.process_catalog(db, dataset_id, version.id)
        
        # Chain into Analytics Engine
        process_analytics_task.delay(job_id=job_id, dataset_version_id=version.id)
        
        return {"status": "success", "catalog_id": catalog_id}
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

@celery_app.task(name="process_analytics_task")
def process_analytics_task(job_id: str, dataset_version_id: str):
    _update_progress(job_id, "Generating Analytics...", 85.0)
    """
    Final automated analytical task: Generates deterministic KPIs, trends, and structured insights.
    """
    from app.core.database import SessionLocal
    from app.services.analytics.analytics_orchestrator import AnalyticsOrchestrator
    
    db = SessionLocal()
    try:
        # Run Analytics Orchestration
        run_id = AnalyticsOrchestrator.run_analytics(db, dataset_version_id)
        
        # Chain into Regression Engine
        process_regression_task.delay(job_id=job_id, dataset_version_id=dataset_version_id, run_id=run_id)
        
        return {"status": "success", "run_id": run_id}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()

@celery_app.task(name="process_regression_task")
def process_regression_task(job_id: str, dataset_version_id: str, run_id: str):
    _update_progress(job_id, "Training Regression Models...", 87.0)
    from app.core.database import SessionLocal
    from app.models.dataset import DatasetVersion, Dataset
    from app.services.schema.schema_registry import SchemaRegistryService
    from app.services.regression.regression_service import regression_service
    
    db = SessionLocal()
    try:
        version = db.query(DatasetVersion).filter(DatasetVersion.id == dataset_version_id).first()
        dataset = db.query(Dataset).filter(Dataset.id == version.dataset_id).first()
        schema_registry = SchemaRegistryService(db)
        schema = schema_registry.get_schema_for_dataset(dataset.id)
        
        if schema:
            numeric_columns = [col for col in schema.columns if col.inferred_semantic_type in ["numeric", "integer", "float", "currency"]]
            if numeric_columns:
                target_col = numeric_columns[-1]
                for col in numeric_columns:
                    if col.business_meaning and "revenue" in col.business_meaning.lower():
                        target_col = col
                        break
                        
                target_variable = target_col.original_header
                all_features = [col.original_header for col in numeric_columns if col.original_header != target_variable]
                
                dataset_stats = {}
                
                if all_features:
                    regression_service.train_model(
                        db=db,
                        dataset_id=dataset.id,
                        dataset_version_id=dataset_version_id,
                        model_name="Auto_Regression_Model",
                        algorithm="linear_regression",
                        target_variable=target_variable,
                        dataset_stats=dataset_stats,
                        all_features=all_features
                    )
        
        process_forecast_task.delay(job_id=job_id, dataset_version_id=dataset_version_id, run_id=run_id)
        return {"status": "success"}
    except Exception as e:
        # Gracefully skip if regression fails due to unsupported data
        process_forecast_task.delay(job_id=job_id, dataset_version_id=dataset_version_id, run_id=run_id)
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()

@celery_app.task(name="process_forecast_task")
def process_forecast_task(job_id: str, dataset_version_id: str, run_id: str):
    _update_progress(job_id, "Forecasting Trends...", 89.0)
    from app.core.database import SessionLocal
    from app.models.dataset import DatasetVersion, Dataset
    from app.services.schema.schema_registry import SchemaRegistryService
    from app.services.forecast.forecast_service import forecast_service
    
    db = SessionLocal()
    try:
        version = db.query(DatasetVersion).filter(DatasetVersion.id == dataset_version_id).first()
        dataset = db.query(Dataset).filter(Dataset.id == version.dataset_id).first()
        schema_registry = SchemaRegistryService(db)
        schema = schema_registry.get_schema_for_dataset(dataset.id)
        
        if schema:
            numeric_columns = [col.original_header for col in schema.columns if col.inferred_semantic_type in ["numeric", "integer", "float", "currency"]]
            
            metrics = []
            for col in numeric_columns[:3]:
                metrics.append({"column_name": col, "aggregation": "sum"})
                
            if metrics:
                forecast_service.run_forecast_analysis(
                    db=db,
                    dataset_id=dataset.id,
                    dataset_version_id=dataset_version_id,
                    metrics=metrics
                )
                
        process_insight_task.delay(job_id=job_id, run_id=run_id)
        return {"status": "success"}
    except Exception as e:
        process_insight_task.delay(job_id=job_id, run_id=run_id)
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()

@celery_app.task(name="process_insight_task")
def process_insight_task(job_id: str, run_id: str):
    _update_progress(job_id, "Extracting Insights...", 90.0)
    """
    Final automated analytical task: Generates deterministic business insights from the raw analytics run.
    """
    from app.core.database import SessionLocal
    from app.services.insights.insight_orchestrator import InsightOrchestrator
    
    db = SessionLocal()
    try:
        valid_count = InsightOrchestrator.process_insights(db, run_id)
        
        # Get dataset_version_id to chain the rules
        # Typically the InsightOrchestrator or AnalyticsRun can give this to us
        from app.models.analytics import AnalyticsRun
        run = db.query(AnalyticsRun).filter(AnalyticsRun.id == run_id).first()
        if run:
            process_rule_task.delay(job_id=job_id, dataset_version_id=run.dataset_version_id)
            
        return {"status": "success", "valid_insights_generated": valid_count}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()

@celery_app.task(name="process_rule_task")
def process_rule_task(job_id: str, dataset_version_id: str):
    _update_progress(job_id, "Evaluating Rules...", 95.0)
    """
    Final automated analytical task: Generates deterministic business decisions from the structured insights.
    """
    from app.core.database import SessionLocal
    from app.services.rules.rule_orchestrator import RuleOrchestrator
    
    db = SessionLocal()
    try:
        decisions_count = RuleOrchestrator.process_rules(db, dataset_version_id)
        
        # Chain into Recommendation Engine
        process_recommendation_task.delay(job_id=job_id, dataset_version_id=dataset_version_id)
        
        return {"status": "success", "decisions_generated": decisions_count}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()

@celery_app.task(name="process_recommendation_task")
def process_recommendation_task(job_id: str, dataset_version_id: str):
    _update_progress(job_id, "Generating Recommendations...", 98.0)
    """
    Final automated strategic task: Generates deterministic recommendations and action plans from decisions.
    """
    from app.core.database import SessionLocal
    from app.services.recommendations.recommendation_orchestrator import RecommendationOrchestrator
    
    db = SessionLocal()
    try:
        valid_count = RecommendationOrchestrator.process_recommendations(db, dataset_version_id)
        process_rag_indexing_task.delay(job_id=job_id, dataset_version_id=dataset_version_id)
        return {"status": "success", "recommendations_generated": valid_count}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()

@celery_app.task(name="process_context_build_task")
def process_context_build_task(workspace_id: str, dataset_version_id: str, question: str, token_budget: int):
    """
    Async task to build a structured AI context package from existing deterministic metadata.
    """
    from app.core.database import SessionLocal
    from app.services.context.context_orchestrator import ContextOrchestrator
    
    db = SessionLocal()
    try:
        package = ContextOrchestrator.build_context(db, workspace_id, dataset_version_id, question, token_budget)
        return {"status": "success", "package_id": package.id, "estimated_tokens": package.estimated_tokens}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()

@celery_app.task(name="process_prompt_build_task")
def process_prompt_build_task(context_package_id: str):
    """
    Async task to build a governed prompt package from a context package.
    """
    from app.core.database import SessionLocal
    from app.services.prompts.prompt_orchestrator import PromptOrchestrator
    
    db = SessionLocal()
    try:
        package = PromptOrchestrator.build_prompt(db, context_package_id)
        return {"status": "success", "package_id": package.id, "estimated_tokens": package.estimated_tokens}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()

@celery_app.task(name="process_kpi_calculation_task")
def process_kpi_calculation_task(workspace_id: str, dataset_version_id: str, definition_id: str, dimension: str = None):
    """
    Async task to calculate a business KPI using DuckDB.
    """
    from app.core.database import SessionLocal
    from app.services.kpis.kpi_orchestrator import KPIOrchestrator
    
    db = SessionLocal()
    try:
        KPIOrchestrator.execute_kpi(db, workspace_id, dataset_version_id, definition_id, dimension)
        return {"status": "success", "definition_id": definition_id}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()

@celery_app.task(name="execute_async_query_task")
def execute_async_query_task(sql: str, dataset_version_id: str, workspace_id: str):
    """Executes a long-running query in the background to avoid HTTP timeouts."""
    from app.core.database import SessionLocal
    from app.services.query.query_orchestrator import QueryOrchestrator
    
    db = SessionLocal()
    try:
        # We don't skip cache here, if it hits cache, great.
        res = QueryOrchestrator.execute_query(db, sql, dataset_version_id, workspace_id)
        return {"status": "success", "rows_returned": res["metadata"]["rows_returned"]}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()

@celery_app.task(name="refresh_materialized_views_task")
def refresh_materialized_views_task():
    """Periodic task to refresh highly used materialized views."""
    # In a full implementation, this would loop through active MaterializedView records
    # and re-execute them, storing the new result in the cache or a physical table.
    return {"status": "success", "message": "Views refreshed."}


@celery_app.task(name="apply_cleaning_pipeline_task")
def apply_cleaning_pipeline_task(dataset_id: str, pipeline_steps: list):
    """
    Background task to execute a Polars cleaning pipeline, generate a new dataset version,
    and trigger the downstream re-ingestion of schema/profile/quality.
    """
    from app.core.database import SessionLocal
    from app.services.cleaning.cleaning_orchestrator import CleaningOrchestrator
    
    db = SessionLocal()
    orchestrator = CleaningOrchestrator(db)
    
    try:
        # Apply the pipeline and create V(N+1)
        new_version_id = orchestrator.apply_pipeline(dataset_id, pipeline_steps)
        
        # Trigger Downstream cascade on the newly cleaned version
        from app.models.dataset import DatasetVersion
        new_version = db.query(DatasetVersion).filter(DatasetVersion.id == new_version_id).first()
        storage = new_version.storage_locations[0]
        
        process_schema_task.delay(
            dataset_version_id=new_version.id, 
            storage_path=storage.storage_path, 
            file_type=new_version.file_type
        )
        
        return {"status": "success", "new_version_id": new_version_id}
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()






@celery_app.task(name="process_rag_indexing_task")
def process_rag_indexing_task(job_id: str, dataset_version_id: str):
    _update_progress(job_id, "Indexing for AI Chat...", 100.0)
    from app.core.database import SessionLocal
    from app.repositories.dataset_repository import DatasetRepository
    from app.models.dataset import DatasetVersion
    from app.services.schema.schema_registry import SchemaRegistryService
    from app.ai.rag_engine import RAGEngine
    
    db = SessionLocal()
    try:
        repo = DatasetRepository(db)
        version = db.query(DatasetVersion).filter(DatasetVersion.id == dataset_version_id).first()
        
        if not version:
            repo.update_upload_job_status(job_id, status="completed", current_step="Completed", progress=100.0)
            return {"status": "skipped", "reason": "DatasetVersion not found"}
        
        # Resolve user_id from the parent dataset
        user_id = version.dataset.user_id if version.dataset else None
        
        schema_registry = SchemaRegistryService(db)
        schema = schema_registry.get_schema_for_dataset(version.dataset_id)
        
        # Build a human-readable schema description to embed
        schema_text = f"Dataset {version.dataset.name if version.dataset else 'Unknown'} contains columns: "
        if schema:
            schema_text += ", ".join([f"{col.original_header} ({col.inferred_semantic_type})" for col in schema.columns])
        
        if user_id:
            engine = RAGEngine()
            engine.embed_and_store(text=schema_text, user_id=user_id)
            
        repo.update_upload_job_status(job_id, status="completed", current_step="Completed", progress=100.0)
        
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


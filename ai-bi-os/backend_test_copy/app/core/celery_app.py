import os
# from celery import Celery

# REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# celery_app = Celery(
#     "ai_bi_os_tasks",
#     broker=REDIS_URL,
#     backend=REDIS_URL
# )

# celery_app.conf.update(
#     task_serializer='json',
#     accept_content=['json'],
#     result_serializer='json',
#     timezone='UTC',
#     enable_utc=True,
# )

class MockCeleryApp:
    def task(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator

celery_app = MockCeleryApp()

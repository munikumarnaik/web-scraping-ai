"""
Utility functions for task execution
Provides fallback to synchronous execution when Celery/Redis is unavailable
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def execute_task(task_func, *args, **kwargs):
    """
    Execute a task either async (Celery) or sync (direct call)

    In production without Redis, tasks run synchronously.
    In development with Redis, tasks run via Celery.
    """
    try:
        # Try to execute via Celery
        return task_func.delay(*args, **kwargs)
    except Exception as e:
        logger.warning(f"Celery unavailable ({str(e)}), running task synchronously")
        # Fallback to synchronous execution
        return task_func(*args, **kwargs)

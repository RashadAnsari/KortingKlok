import celery
from celery.utils.log import get_task_logger

logger = get_task_logger("baseapi.tasks")


# Reference: https://docs.celeryq.dev/en/stable/userguide/tasks.html
class BaseTaskWithRetry(celery.Task):
    autoretry_for = (Exception,)
    max_retries = 5
    retry_backoff = True
    retry_backoff_max = 300
    default_retry_delay = 10
    retry_jitter = True

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        logger.warning("Task %s[%s] retry #%s: %s", self.name, task_id, self.request.retries, exc)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error("Task %s[%s] failed: %s", self.name, task_id, exc)

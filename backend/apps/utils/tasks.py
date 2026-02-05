import celery


# Reference: https://docs.celeryq.dev/en/stable/userguide/tasks.html
class BaseTaskWithRetry(celery.Task):
    autoretry_for = (Exception,)
    max_retries = 10
    retry_backoff = True
    retry_backoff_max = 300
    default_retry_delay = 10
    retry_jitter = True

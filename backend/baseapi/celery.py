import os
from logging.config import dictConfig

from django.conf import settings

from celery import Celery
from celery.signals import after_setup_logger, after_setup_task_logger, setup_logging

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "baseapi.settings")

app = Celery("baseapi")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@setup_logging.connect
@after_setup_logger.connect
@after_setup_task_logger.connect
def setup_celery_loggers(**_kwargs):
    dictConfig(settings.LOGGING)

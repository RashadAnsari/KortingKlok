import multiprocessing
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from environ import Env

load_dotenv()
env = Env()

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, os.path.join(BASE_DIR, "apps"))

DEBUG = False
USE_TZ = True
TIME_ZONE = "UTC"
APPEND_SLASH = False
ALLOWED_HOSTS = ["*"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SECRET_KEY = env.str("DJANGO_SECRET_KEY", default="secret")
LANGUAGE_CODE = "nl"
LANGUAGES = [
    ("nl", "Nederlands"),
    ("en", "English"),
]
LOCALE_PATHS = (os.path.join(BASE_DIR, "baseapi", "local"),)

INSTALLED_APPS = [
    # Django apps
    "apis",
    "products",
    "users",
    "utils",
    "baseapi",
    # Third party apps
    "rest_framework",
    "drf_spectacular",
    "drf_standardized_errors",
]

REST_FRAMEWORK = {
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_METADATA_CLASS": "apis.metadata.MinimalMetadata",
    "DEFAULT_THROTTLE_RATES": {"rate_limiter": "5/second"},
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "DEFAULT_AUTHENTICATION_CLASSES": ["users.auths.UserTokenAuthentication"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "drf_standardized_errors.handler.exception_handler",
}

DRF_STANDARDIZED_ERRORS = {
    "EXCEPTION_HANDLER_CLASS": "apis.exceptions.CustomExceptionHandler",
    "EXCEPTION_FORMATTER_CLASS": "apis.exceptions.CustomExceptionFormatter",
}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "baseapi.urls"
WSGI_APPLICATION = "baseapi.wsgi.application"

DATABASES = {
    "default": env.db_url("DATABASE_URL", default="postgres://baseapi:secret@localhost:5432/baseapi"),
}

CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_COMPRESSION = "gzip"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_DEFAULT_QUEUE = "default"
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 100
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_WORKER_CONCURRENCY = multiprocessing.cpu_count() * 2 + 1
CELERY_BROKER_URL = env.str("CELERY_BROKER_URL", default="redis://localhost:6379")

# With CELERY_TASK_ACKS_LATE=True and a Redis broker, a task message becomes
# visible again (re-queued) if it hasn't been acknowledged within visibility_timeout.
# This must exceed the longest expected task duration to prevent a running scrape
# from being re-delivered to a second worker.
# Expected scrape time: ~14 min (BFS ~12 min + parallel products ~2 min).
# Set to 1 hour to give ample headroom while staying tight enough to catch hangs.
CELERY_BROKER_TRANSPORT_OPTIONS = {"visibility_timeout": 3600}

# Soft limit raises SoftTimeLimitExceeded inside the task so it can clean up.
# Hard limit forcibly kills the worker process if it still hasn't stopped.
# Both must stay below visibility_timeout so an overdue task is killed before
# Redis re-queues it.
CELERY_TASK_SOFT_TIME_LIMIT = 1800  # 30 min — graceful shutdown signal (~2× expected)
CELERY_TASK_TIME_LIMIT = 2700  # 45 min — hard kill (~3× expected)

TEMPLATE_DIR = os.path.join(BASE_DIR, "apps", "tmpls")

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [TEMPLATE_DIR],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ]
        },
    },
]

SPECTACULAR_SETTINGS = {
    "TITLE": "KortingKlok API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVE_AUTHENTICATION": [],
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
    },
}

# References
# https://docs.python.org/3/library/logging.html#logrecord-attributes

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json_verbose": {
            "format": '{"asctime":"%(asctime)s","filename":"%(filename)s","funcName":"%(funcName)s",'
            + '"levelname":"%(levelname)s","lineno":"%(lineno)d","message":"%(message)s",'
            + '"module":"%(module)s","name":"%(name)s"}',
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json_verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "celery": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

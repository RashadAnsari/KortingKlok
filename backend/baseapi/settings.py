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
ADMIN_USER_ID = env.str("ADMIN_USER_ID", default="")
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
CELERY_WORKER_MAX_TASKS_PER_CHILD = 100
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_URL = env.str("CELERY_BROKER_URL", default="redis://localhost:6379")
CELERY_BROKER_TRANSPORT_OPTIONS = {"visibility_timeout": 5400}  # 1.5 hours (covers Lidl scraper)

SPECTACULAR_SETTINGS = {
    "TITLE": "KortingKlok API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVE_AUTHENTICATION": [],
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
    },
}

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

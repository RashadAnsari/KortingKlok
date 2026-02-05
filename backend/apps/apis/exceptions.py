from django.utils.translation import gettext as _

from drf_standardized_errors.formatter import ExceptionFormatter
from drf_standardized_errors.handler import ExceptionHandler
from rest_framework import status
from rest_framework.exceptions import APIException

from apis.serializers import ErrorResponseSerializer


class ConflictError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = _("Request conflicts with current state.")
    default_code = "conflict"


class CustomExceptionHandler(ExceptionHandler):
    def convert_unhandled_exceptions(self, exc: Exception) -> APIException:
        return exc if isinstance(exc, APIException) else APIException()


class CustomExceptionFormatter(ExceptionFormatter):
    def run(self):
        errors = [{"code": e.code, "detail": e.detail, "attr": e.attr} for e in self.get_errors()]
        return ErrorResponseSerializer({"errors": errors}).data

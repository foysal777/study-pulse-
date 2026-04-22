from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler
from .responses import error_response


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    if response is not None:
        # Use our standard error_response helper
        # We can extract the message and errors from the response.data
        message = "An error occurred"
        errors = response.data

        if isinstance(errors, dict):
            if "detail" in errors:
                message = errors.pop("detail")
            elif "non_field_errors" in errors:
                message = "Validation error"
            elif errors:
                message = "Validation error"

        # Special handling for status codes to match error_name
        return error_response(
            message=message,
            errors=errors if errors else None,
            status_code=response.status_code
        )

    return response


class APIBusinessException(APIException):
    status_code = 400
    default_detail = "Business rule violation"
    default_code = "business_error"


class NotFoundException(APIBusinessException):
    status_code = 404
    default_detail = "Not found"
    default_code = "not_found"


class ConflictException(APIBusinessException):
    status_code = 409
    default_detail = "Conflict"
    default_code = "conflict"

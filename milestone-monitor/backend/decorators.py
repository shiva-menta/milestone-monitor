from django.http import HttpResponseForbidden
from functools import wraps
from twilio.request_validator import RequestValidator
from backend.settings import twilio_auth

def validate_twilio_request(f):
    """Validates that incoming requests genuinely originated from Twilio"""
    @wraps(f)
    def decorated_function(request, *args, **kwargs):
        validator = RequestValidator(twilio_auth)

        request_valid = validator.validate(
            request.build_absolute_uri(),
            request.POST,
            request.META.get('HTTP_X_TWILIO_SIGNATURE', ''))

        if request_valid:
            return f(request, *args, **kwargs)
        else:
            return HttpResponseForbidden()
    return decorated_function

from django.conf import settings
from django.core.mail import send_mail

from accounts.models import OneTimePassword


def send_otp_email(otp: OneTimePassword):
    subject = f"Your {otp.get_purpose_display()} OTP Code"
    message = (
        f"Hello {otp.user.full_name},\n\n"
        f"Your 4 digit OTP is {otp.code}.\n"
        "It will expire in 10 minutes.\n\n"
        "If you did not request this code, please ignore this email."
    )
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or getattr(settings, "EMAIL_HOST_USER", None)
    send_mail(subject, message, from_email, [otp.user.email], fail_silently=False)


def issue_and_send_otp(user, purpose):
    otp = OneTimePassword.issue_for_user(user=user, purpose=purpose)
    send_otp_email(otp)
    return otp

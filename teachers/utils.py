import secrets
import string

from django.conf import settings
from django.core.mail import send_mail


def generate_temp_password(length=12):
    """Generate a secure random temporary password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    # Ensure at least one of each required char type
    password = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^&*"),
    ]
    password += [secrets.choice(alphabet) for _ in range(length - 4)]
    secrets.SystemRandom().shuffle(password)
    return "".join(password)


def send_teacher_welcome_email(teacher_name: str, email: str, temp_password: str):
    """Send welcome email to a newly added teacher with their temporary password."""
    subject = "Welcome to Study Pulse – Your Login Credentials"
    message = (
        f"Hello {teacher_name},\n\n"
        f"You have been added as a teacher on Study Pulse.\n\n"
        f"Your login credentials are:\n"
        f"  Email:    {email}\n"
        f"  Password: {temp_password}\n\n"
        f"Please log in and set a new password as soon as possible.\n\n"
        f"If you did not expect this email, please contact the admin immediately.\n\n"
        f"Best regards,\n"
        f"Study Pulse Team"
    )
    from_email = (
        getattr(settings, "DEFAULT_FROM_EMAIL", None)
        or getattr(settings, "EMAIL_HOST_USER", None)
    )
    send_mail(subject, message, from_email, [email], fail_silently=False)

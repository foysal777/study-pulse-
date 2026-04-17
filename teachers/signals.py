from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import UserRole
from teachers.models import Teacher
from teachers.utils import generate_temp_password, send_teacher_welcome_email

User = get_user_model()


@receiver(post_save, sender=Teacher)
def create_teacher_user_account(sender, instance, created, **kwargs):
    """
    When a new Teacher is saved by admin:
      - Create a User account (role=teacher) if not already exists
      - Generate a random temporary password
      - Send a welcome email with credentials
    """
    if not created:
        return  # Only run on first creation

    # If a user account already exists for this email, skip
    if User.objects.filter(email=instance.email.lower()).exists():
        return

    temp_password = generate_temp_password()

    user = User.objects.create_user(
        email=instance.email,
        full_name=instance.name,
        password=temp_password,
        role=UserRole.TEACHER,
        is_active=True,
        is_email_verified=True,
    )

    try:
        send_teacher_welcome_email(
            teacher_name=instance.name,
            email=instance.email,
            temp_password=temp_password,
        )
    except Exception as exc:
        # Don't crash the admin save; just log it
        import logging
        logger = logging.getLogger(__name__)
        logger.error(
            "Failed to send welcome email to teacher %s (%s): %s",
            instance.name,
            instance.email,
            exc,
        )

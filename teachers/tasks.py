from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from common.utils import send_expo_push_notification
from teachers.models import TeacherSlot
from accounts.models import User
from students.models import StudentNotification

@shared_task
def send_class_reminder_push_notification(student_id, slot_id):
    try:
        student = User.objects.get(id=student_id)
        slot = TeacherSlot.objects.get(id=slot_id)
        
        if getattr(student, 'expo_push_token', None) and getattr(student, 'is_push_notification', True):
            title = "Upcoming Class Reminder"
            body = f"Your class '{slot.title or 'General Class'}' starts in 30 minutes!"
            
            # Save to database
            StudentNotification.objects.create(
                student=student,
                title=title,
                body=body
            )
            
            # Send push
            send_expo_push_notification(
                push_tokens=[student.expo_push_token],
                title=title,
                body=body,
                data={"slot_id": slot_id, "screen": "session_details"}
            )
    except Exception as e:
        print(f"Failed to send push notification: {str(e)}")

@shared_task
def send_teacher_booking_email(teacher_email, student_name, slot_date, slot_time):
    try:
        subject = "New Student Booking Confirmation"
        message = f"Hello,\n\nA new student ({student_name}) has booked your session on {slot_date} at {slot_time}.\n\nBest regards,\nStudy Pulse Team"
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@studypulse.com')
        send_mail(
            subject,
            message,
            from_email,
            [teacher_email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send email to teacher: {str(e)}")

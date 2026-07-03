from django.urls import path
from teachers import views

app_name = "teachers"

urlpatterns = [
    path("set-password/", views.teacher_set_password, name="teacher_set_password"),
    path("profile/", views.teacher_profile, name="teacher_profile"),
    path("location/", views.teacher_location, name="teacher_location"),
    path("availability/", views.teacher_availability, name="teacher_availability"),
    path("available-slots/", views.student_available_slots, name="student_available_slots"),
    path("book-slot/", views.student_book_slot, name="student_book_slot"),
    path("cancel-booking/<int:booking_id>/", views.student_cancel_booking, name="student_cancel_booking"),
    path("booked-sessions/", views.teacher_booked_sessions, name="teacher_booked_sessions"),
    path("slots/students_list/", views.teacher_pending_students, name="teacher_pending_students"),
    path("students/<int:student_id>/feedback/", views.teacher_student_feedback, name="teacher_student_feedback"),
    path("students/<int:student_id>/remove/", views.teacher_remove_student, name="teacher_remove_student"),
    path("request-cancellation/", views.teacher_request_cancellation, name="teacher_request_cancellation"),
    path("pending-requests/", views.teacher_pending_requests, name="teacher_pending_requests"),
    path("admin-notification-count/", views.admin_notification_count, name="admin_notification_count"),
    path("slots/<int:slot_id>/send-notice/", views.teacher_send_session_notice, name="teacher_send_session_notice"),
    path("dashboard/", views.teacher_dashboard, name="teacher_dashboard"),
    path("students/<int:student_id>/progress/", views.teacher_student_progress, name="teacher_student_progress"),
    path("assessments/<int:attempt_id>/result/", views.teacher_student_assessment_result, name="teacher_student_assessment_result"),
    path("course-sessions/<int:course_id>/", views.get_course_sessions, name="get_course_sessions"),
    path("sessions/<int:session_id>/dates/<int:teacher_id>/", views.get_session_dates, name="get_session_dates"),
]




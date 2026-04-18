from django.urls import path
from teachers import views

app_name = "teachers"

urlpatterns = [
    path("set-password/", views.teacher_set_password, name="teacher_set_password"),
    path("profile/", views.teacher_profile, name="teacher_profile"),
    path("location/", views.teacher_location, name="teacher_location"),
    path("availability/", views.teacher_add_availability, name="teacher_add_availability"),
    path("available-slots/", views.student_available_slots, name="student_available_slots"),
    path("book-slot/", views.student_book_slot, name="student_book_slot"),
    path("cancel-booking/<int:booking_id>/", views.student_cancel_booking, name="student_cancel_booking"),
]

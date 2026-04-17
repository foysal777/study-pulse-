from django.urls import path
from teachers import views

app_name = "teachers"

urlpatterns = [
    path("set-password/", views.teacher_set_password, name="teacher_set_password"),
    path("profile/", views.teacher_profile, name="teacher_profile"),
]

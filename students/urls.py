from django.urls import path
from students import views

app_name = "students"

urlpatterns = [
    path("profile-setup/", views.profile_setup, name="profile_setup"),
    path("interests/", views.interest_options, name="interest_options"),
]

from django.urls import path

from accounts import views

app_name = "accounts"

urlpatterns = [
    path("sign-up/", views.sign_up, name="sign_up"),
    path("verify-sign-up-otp/", views.verify_sign_up_otp, name="verify_sign_up_otp"),
    path("sign-in/", views.sign_in, name="sign_in"),
    path("resend-otp/", views.resend_otp, name="resend_otp"),
    path("refresh-token/", views.refresh_token, name="refresh_token"),
    path("me/", views.me, name="me"),
]

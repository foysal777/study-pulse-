from django.urls import path
from support import views

app_name = "support"

urlpatterns = [
    path("policies/", views.policy_view, name="policy_view"),
    path("help-support/", views.help_support_view, name="help_support_view"),
    path("play-store-qr/", views.play_store_qr_view, name="play_store_qr_view"),
]


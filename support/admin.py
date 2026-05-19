from django.contrib import admin
from unfold.admin import ModelAdmin
from support.models import Policy, HelpSupport, PlayStoreQRCode



@admin.register(Policy)
class PolicyAdmin(ModelAdmin):
    list_display = ("title", "updated_at")


@admin.register(HelpSupport)
class HelpSupportAdmin(ModelAdmin):
    list_display = ("email", "phone_number", "updated_at")


@admin.register(PlayStoreQRCode)
class PlayStoreQRCodeAdmin(ModelAdmin):
    list_display = ("id", "uploaded_at", "updated_at")


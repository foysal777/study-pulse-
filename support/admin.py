from django.contrib import admin
from unfold.admin import ModelAdmin
from support.models import Policy, HelpSupport


@admin.register(Policy)
class PolicyAdmin(ModelAdmin):
    list_display = ("title", "updated_at")


@admin.register(HelpSupport)
class HelpSupportAdmin(ModelAdmin):
    list_display = ("email", "phone_number", "updated_at")

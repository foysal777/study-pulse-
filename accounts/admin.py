from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm

from accounts.forms import UserAdminChangeForm, UserAdminCreationForm
from accounts.models import AppLanguage, OneTimePassword, User


admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    change_password_form = AdminPasswordChangeForm
    model = User
    ordering = ("id",)
    list_display = ("id", "full_name", "email", "role", "is_active", "is_email_verified", "is_staff")
    readonly_fields=("is_active", "is_staff", "is_email_verified")
    list_filter = ("role", "is_active", "is_email_verified", "is_staff", "is_superuser")
    search_fields = ("full_name", "email")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("full_name", "role")}),
        ("Permissions", {"fields": ("is_active", "is_email_verified", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important Dates", {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "full_name", "role", "password1", "password2", "is_active", "is_email_verified", "is_staff"),
            },
        ),
    )




# @admin.register(Group)
# class GroupAdmin(BaseGroupAdmin, ModelAdmin):
#     pass


@admin.register(OneTimePassword)
class OneTimePasswordAdmin(ModelAdmin):
    list_display = ("id", "user", "purpose", "code", "expires_at", "is_used", "created_at")
    list_filter = ("purpose", "is_used")
    search_fields = ("user__email", "user__full_name", "code")


@admin.register(AppLanguage)
class AppLanguageAdmin(ModelAdmin):
    list_display = ("id", "name", "code", "created_at")
    search_fields = ("name", "code")

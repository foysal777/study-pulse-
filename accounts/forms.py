from django import forms
from unfold.forms import UserChangeForm as UnfoldUserChangeForm
from unfold.forms import UserCreationForm as UnfoldUserCreationForm

from accounts.models import User


class UserAdminCreationForm(UnfoldUserCreationForm):
    class Meta:
        model = User
        fields = ("email", "full_name", "role", "is_active", "is_email_verified", "is_staff")


class UserAdminChangeForm(UnfoldUserChangeForm):
    class Meta:
        model = User
        fields = (
            "email",
            "full_name",
            "password",
            "role",
            "is_active",
            "is_email_verified",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        )

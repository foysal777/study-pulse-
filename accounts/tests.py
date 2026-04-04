from django.core import mail
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import OneTimePassword, OtpPurpose, User, UserRole


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AuthenticationFlowTests(APITestCase):
    def test_student_signup_creates_inactive_user_and_sends_otp(self):
        response = self.client.post(
            "/api/accounts/sign-up/",
            {
                "full_name": "John Student",
                "email": "john@example.com",
                "password": "StrongPass123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="john@example.com")
        self.assertEqual(user.role, UserRole.STUDENT)
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_email_verified)
        self.assertEqual(OneTimePassword.objects.filter(user=user, purpose=OtpPurpose.SIGNUP).count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_signup_otp_verification_returns_jwt_tokens(self):
        user = User.objects.create_user(
            email="verify@example.com",
            full_name="Verify Student",
            password="StrongPass123",
            role=UserRole.STUDENT,
            is_active=False,
            is_email_verified=False,
        )
        otp = OneTimePassword.issue_for_user(user, OtpPurpose.SIGNUP)

        response = self.client.post(
            "/api/accounts/verify-sign-up-otp/",
            {"email": user.email, "otp": otp.code},
            format="json",
        )

        user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_email_verified)
        self.assertIn("access", response.data["data"]["tokens"])
        self.assertIn("refresh", response.data["data"]["tokens"])

    def test_sign_in_returns_jwt_tokens_for_verified_user(self):
        user = User.objects.create_user(
            email="teacher@example.com",
            full_name="Teacher User",
            password="StrongPass123",
            role=UserRole.TEACHER,
            is_active=True,
            is_email_verified=True,
        )

        sign_in_response = self.client.post(
            "/api/accounts/sign-in/",
            {"email": user.email, "password": "StrongPass123"},
            format="json",
        )

        self.assertEqual(sign_in_response.status_code, status.HTTP_200_OK)
        self.assertEqual(sign_in_response.data["data"]["user"]["role"], UserRole.TEACHER)
        self.assertIn("access", sign_in_response.data["data"]["tokens"])
        self.assertIn("refresh", sign_in_response.data["data"]["tokens"])
        self.assertFalse(OneTimePassword.objects.filter(user=user, purpose=OtpPurpose.LOGIN).exists())

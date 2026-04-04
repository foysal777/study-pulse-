from django.contrib.auth import get_user_model
from django.db import transaction
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import OneTimePassword, OtpPurpose, UserRole
from accounts.serializers import (
    OtpVerificationSerializer,
    ErrorResponseSerializer,
    ResendOtpSerializer,
    SignInSerializer,
    SignInSuccessResponseSerializer,
    SignUpSerializer,
    SignUpSuccessResponseSerializer,
    SuccessMessageResponseSerializer,
    TokenRefreshRequestSerializer,
    TokenRefreshSuccessResponseSerializer,
    UserSerializer,
    MeSuccessResponseSerializer,
    OtpVerifiedSuccessResponseSerializer,
)
from accounts.utils import issue_and_send_otp
from common.responses import created_response, error_response, success_response

User = get_user_model()


def _get_user_by_email(email):
    return User.objects.filter(email=email.lower()).first()


def _build_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


def _get_valid_otp(user, purpose, code):
    otp = (
        OneTimePassword.objects.filter(
            user=user,
            purpose=purpose,
            code=code,
            is_used=False,
        )
        .order_by("-created_at")
        .first()
    )
    if otp is None or otp.is_expired:
        return None
    return otp


@extend_schema(
    tags=["Accounts Authentication"],
    operation_id="accounts_sign_up",
    request=SignUpSerializer,
    responses={
        201: SignUpSuccessResponseSerializer,
        400: OpenApiResponse(response=ErrorResponseSerializer, description="Validation error."),
        409: OpenApiResponse(response=ErrorResponseSerializer, description="Email already exists."),
        500: OpenApiResponse(response=ErrorResponseSerializer, description="OTP email sending failed."),
    },
    description="Create a student account using full name, email, and password. A 4 digit OTP is sent by email for verification.",
)
@api_view(["POST"])
@permission_classes([AllowAny])
def sign_up(request):
    serializer = SignUpSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response("Validation error", serializer.errors, status.HTTP_400_BAD_REQUEST)

    validated_data = serializer.validated_data
    email = validated_data["email"]

    with transaction.atomic():
        user = _get_user_by_email(email)
        if user and user.is_email_verified:
            return error_response("An account with this email already exists.", status_code=status.HTTP_409_CONFLICT)

        if user is None:
            user = User.objects.create_user(
                email=email,
                full_name=validated_data["full_name"],
                password=validated_data["password"],
                role=UserRole.STUDENT,
                is_active=False,
                is_email_verified=False,
            )
        else:
            user.full_name = validated_data["full_name"]
            user.role = UserRole.STUDENT
            user.is_active = False
            user.is_email_verified = False
            user.set_password(validated_data["password"])
            user.save(
                update_fields=["full_name", "role", "is_active", "is_email_verified", "password", "updated_at"]
            )

    try:
        issue_and_send_otp(user, OtpPurpose.SIGNUP)
    except Exception as exc:
        return error_response("Failed to send OTP email.", {"detail": str(exc)}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    return created_response(
        {
            "user": UserSerializer(user).data,
            "next_step": "Verify the 4 digit OTP sent to your email to activate your account.",
        },
        message="Student account created. OTP sent to email.",
    )


@extend_schema(
    tags=["Accounts Authentication"],
    operation_id="accounts_verify_sign_up_otp",
    request=OtpVerificationSerializer,
    responses={
        200: OtpVerifiedSuccessResponseSerializer,
        400: OpenApiResponse(response=ErrorResponseSerializer, description="OTP is invalid or expired."),
        404: OpenApiResponse(response=ErrorResponseSerializer, description="User not found."),
    },
    description="Verify the sign-up OTP and receive JWT access and refresh tokens.",
)
@api_view(["POST"])
@permission_classes([AllowAny])
def verify_sign_up_otp(request):
    serializer = OtpVerificationSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response("Validation error", serializer.errors, status.HTTP_400_BAD_REQUEST)

    user = _get_user_by_email(serializer.validated_data["email"])
    if user is None:
        return error_response("User not found.", status_code=status.HTTP_404_NOT_FOUND)

    otp = _get_valid_otp(user, OtpPurpose.SIGNUP, serializer.validated_data["otp"])
    if otp is None:
        return error_response("Invalid or expired OTP.", status_code=status.HTTP_400_BAD_REQUEST)

    otp.mark_used()
    user.is_active = True
    user.is_email_verified = True
    user.save(update_fields=["is_active", "is_email_verified", "updated_at"])

    return success_response(
        {
            "user": UserSerializer(user).data,
            "tokens": _build_tokens_for_user(user),
        },
        message="Account verified successfully.",
    )


@extend_schema(
    tags=["Accounts Authentication"],
    operation_id="accounts_sign_in",
    request=SignInSerializer,
    responses={
        200: SignInSuccessResponseSerializer,
        400: OpenApiResponse(response=ErrorResponseSerializer, description="Invalid credentials or validation error."),
        403: OpenApiResponse(response=ErrorResponseSerializer, description="Account is not verified yet."),
    },
    description="Sign in a verified user with email and password and return JWT access and refresh tokens.",
)
@api_view(["POST"])
@permission_classes([AllowAny])
def sign_in(request):
    serializer = SignInSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response("Validation error", serializer.errors, status.HTTP_400_BAD_REQUEST)

    email = serializer.validated_data["email"]
    password = serializer.validated_data["password"]
    user = _get_user_by_email(email)

    if user is None or not user.check_password(password):
        return error_response("Invalid email or password.", status_code=status.HTTP_400_BAD_REQUEST)

    if not user.is_active or not user.is_email_verified:
        return error_response(
            "Account is not verified yet. Please verify your email OTP first.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    return success_response(
        {
            "user": UserSerializer(user).data,
            "tokens": _build_tokens_for_user(user),
        },
        message="Sign in completed successfully.",
    )


@extend_schema(
    tags=["Accounts Authentication"],
    operation_id="accounts_resend_otp",
    request=ResendOtpSerializer,
    responses={
        200: SuccessMessageResponseSerializer,
        400: OpenApiResponse(response=ErrorResponseSerializer, description="OTP resend is not allowed for the current user state."),
        404: OpenApiResponse(response=ErrorResponseSerializer, description="User not found."),
        500: OpenApiResponse(response=ErrorResponseSerializer, description="OTP email sending failed."),
    },
    description="Resend a 4 digit OTP for sign-up verification.",
)
@api_view(["POST"])
@permission_classes([AllowAny])
def resend_otp(request):
    serializer = ResendOtpSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response("Validation error", serializer.errors, status.HTTP_400_BAD_REQUEST)

    user = _get_user_by_email(serializer.validated_data["email"])
    if user is None:
        return error_response("User not found.", status_code=status.HTTP_404_NOT_FOUND)

    purpose = serializer.validated_data["purpose"]
    if purpose == OtpPurpose.SIGNUP and user.is_email_verified:
        return error_response("This account is already verified.", status_code=status.HTTP_400_BAD_REQUEST)

    try:
        issue_and_send_otp(user, purpose)
    except Exception as exc:
        return error_response("Failed to send OTP email.", {"detail": str(exc)}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    return success_response(message="OTP sent successfully.")


@extend_schema(
    tags=["Accounts Authentication"],
    operation_id="accounts_refresh_token",
    request=TokenRefreshRequestSerializer,
    responses={
        200: TokenRefreshSuccessResponseSerializer,
        400: OpenApiResponse(response=ErrorResponseSerializer, description="Refresh token is invalid."),
    },
    description="Exchange a valid refresh token for a new access token.",
)
@api_view(["POST"])
@permission_classes([AllowAny])
def refresh_token(request):
    serializer = TokenRefreshRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response("Validation error", serializer.errors, status.HTTP_400_BAD_REQUEST)

    token_serializer = TokenRefreshSerializer(data=serializer.validated_data)
    if not token_serializer.is_valid():
        return error_response("Invalid refresh token.", token_serializer.errors, status.HTTP_400_BAD_REQUEST)

    return success_response(token_serializer.validated_data, message="Token refreshed successfully.")


@extend_schema(
    tags=["Accounts Authentication"],
    operation_id="accounts_me",
    responses={
        200: MeSuccessResponseSerializer,
        401: OpenApiResponse(response=ErrorResponseSerializer, description="Authentication credentials were not provided or are invalid."),
    },
    description="Return the currently authenticated user's profile.",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    return success_response(UserSerializer(request.user).data, message="User profile fetched successfully.")

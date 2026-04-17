from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated

from common.responses import error_response, success_response
from accounts.models import UserRole
from teachers.models import TeacherProfile
from teachers.serializers import (
    TeacherSetPasswordSerializer,
    TeacherSetPasswordSuccessResponseSerializer,
    TeacherErrorResponseSerializer,
    TeacherProfileSerializer,
)


@extend_schema(
    methods=["GET"],
    tags=["Teachers Profile"],
    operation_id="teachers_profile_get",
    responses={200: TeacherProfileSerializer},
    description="Fetch the teacher's profile.",
)
@extend_schema(
    methods=["POST"],
    tags=["Teachers Profile"],
    operation_id="teachers_profile_create",
    request={
        "multipart/form-data": TeacherProfileSerializer,
    },
    responses={
        201: TeacherProfileSerializer,
        400: OpenApiResponse(response=TeacherErrorResponseSerializer, description="Validation error or profile already exists."),
    },
    description="Create a new teacher profile. Supports multipart/form-data for profile_picture.",
)
@extend_schema(
    methods=["PATCH"],
    tags=["Teachers Profile"],
    operation_id="teachers_profile_update",
    request={
        "multipart/form-data": TeacherProfileSerializer,
    },
    responses={
        200: TeacherProfileSerializer,
        400: OpenApiResponse(response=TeacherErrorResponseSerializer, description="Validation error."),
        404: OpenApiResponse(response=TeacherErrorResponseSerializer, description="Profile not found."),
    },
    description="Update an existing teacher profile. Supports multipart/form-data for profile_picture.",
)
@api_view(["GET", "POST", "PATCH"])
@parser_classes([MultiPartParser, FormParser, JSONParser])
@permission_classes([IsAuthenticated])
def teacher_profile(request):
    if request.user.role != UserRole.TEACHER:
        return error_response(
            "Only teacher users can access this endpoint.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    try:
        profile = TeacherProfile.objects.get(user=request.user)
    except TeacherProfile.DoesNotExist:
        profile = None

    if request.method == "GET":
        if not profile:
            return error_response("Profile not found.", status_code=status.HTTP_404_NOT_FOUND)
        serializer = TeacherProfileSerializer(profile, context={"request": request})
        return success_response(serializer.data, message="Profile fetched successfully.")

    if request.method == "POST":
        if profile:
            return error_response("Profile already exists. Use PATCH to update.", status_code=status.HTTP_400_BAD_REQUEST)
        serializer = TeacherProfileSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save(user=request.user)
            return success_response(serializer.data, message="Profile created successfully.", status_code=status.HTTP_201_CREATED)
        return error_response("Validation error", serializer.errors, status.HTTP_400_BAD_REQUEST)

    if request.method == "PATCH":
        if not profile:
            return error_response("Profile not found. Use POST to create.", status_code=status.HTTP_404_NOT_FOUND)
        serializer = TeacherProfileSerializer(profile, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return success_response(serializer.data, message="Profile updated successfully.")
        return error_response("Validation error", serializer.errors, status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["Teachers Authentication"],
    operation_id="teachers_set_password",
    request=TeacherSetPasswordSerializer,
    responses={
        200: TeacherSetPasswordSuccessResponseSerializer,
        400: OpenApiResponse(response=TeacherErrorResponseSerializer, description="Validation error."),
        403: OpenApiResponse(response=TeacherErrorResponseSerializer, description="Only teacher users can access this endpoint."),
    },
    description="Allows a teacher to set a new password. Usually used after the first login with a temporary password.",
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def teacher_set_password(request):
    if request.user.role != UserRole.TEACHER:
        return error_response(
            "Only teacher users can access this endpoint.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    serializer = TeacherSetPasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response(
            "Validation error",
            serializer.errors,
            status.HTTP_400_BAD_REQUEST,
        )

    user = request.user
    user.set_password(serializer.validated_data["new_password"])
    user.save()

    return success_response(
        message="Password updated successfully.",
    )

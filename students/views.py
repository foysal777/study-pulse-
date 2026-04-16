from django.db import transaction
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from accounts.models import UserRole
from common.responses import error_response, success_response
from students.models import Intterest, StudentProfile, AssessmentTemplate
from students.serializers import (
    StudentErrorResponseSerializer,
    StudentInterestOptionsSuccessResponseSerializer,
    StudentProfileSetupSuccessResponseSerializer,
    StudentProfileSetupUpsertSerializer,
    AssessmentTemplateDisplaySerializer,
    AssessmentTemplateListSerializer,
    AssessmentTemplateSuccessResponseSerializer,
    AssessmentTemplateListSuccessResponseSerializer
)


def _get_core_reasons_options():
    return list(
        Intterest.objects.order_by("interest_name")
        .values_list("interest_name", flat=True)
        .distinct()
    )


def _build_profile_setup_payload(user, profile):
    interest_options = _get_core_reasons_options()
    selected_reasons = list(
        Intterest.objects.filter(student=user)
        .order_by("interest_name")
        .values_list("interest_name", flat=True)
    )
    return {
        "name": user.full_name,
        "phone_number": profile.phone_number,
        "age": profile.age,
        "gender": profile.gender,
        "last_achieved_degree": profile.last_achieved_degree,
        "parents_name": profile.parents_name,
        "parents_phone_number": profile.parents_phone_number,
        "core_reasons_of_learning": selected_reasons,
        "preferred_study_time": profile.preferred_study_time or [],
        "preferred_study_mode": profile.preferred_study_mode or [],
        "preferred_study_language": profile.preferred_study_language or [],
        "core_reasons_options": interest_options,
        "interest_options": interest_options,
    }


@extend_schema(
    tags=["Students Profile"],
    operation_id="students_interest_options",
    responses={
        200: StudentInterestOptionsSuccessResponseSerializer,
        401: OpenApiResponse(response=StudentErrorResponseSerializer, description="Authentication required."),
        403: OpenApiResponse(response=StudentErrorResponseSerializer, description="Only student users can access this endpoint."),
    },
    description="Return interest options from Intterest model for profile setup dropdowns.",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def interest_options(request):
    if request.user.role != UserRole.STUDENT:
        return error_response(
            "Only student users can access this endpoint.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    return success_response(
        {"interests": _get_core_reasons_options()},
        message="Interest options fetched successfully.",
    )


@extend_schema(
    tags=["Students Profile"],
    operation_id="students_profile_setup",
    request=StudentProfileSetupUpsertSerializer,
    responses={
        200: StudentProfileSetupSuccessResponseSerializer,
        201: StudentProfileSetupSuccessResponseSerializer,
        400: OpenApiResponse(response=StudentErrorResponseSerializer, description="Validation error."),
        401: OpenApiResponse(response=StudentErrorResponseSerializer, description="Authentication required."),
        403: OpenApiResponse(response=StudentErrorResponseSerializer, description="Only student users can access this endpoint."),
    },
    description=(
        "Single endpoint for both profile setup pages. "
        "GET returns all profile setup data, POST/PUT/PATCH updates it. "
        "core_reasons_of_learning is stored in Intterest model (interest_name)."
    ),
)
@api_view(["GET", "POST", "PUT", "PATCH"])
@permission_classes([IsAuthenticated])
def profile_setup(request):
    if request.user.role != UserRole.STUDENT:
        return error_response(
            "Only student users can access this endpoint.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    profile, created = StudentProfile.objects.get_or_create(student=request.user)

    if request.method == "GET":
        return success_response(
            _build_profile_setup_payload(request.user, profile),
            message="Profile setup data fetched successfully.",
        )

    serializer = StudentProfileSetupUpsertSerializer(
        data=request.data,
        partial=request.method == "PATCH",
    )
    if not serializer.is_valid():
        return error_response(
            "Validation error",
            serializer.errors,
            status.HTTP_400_BAD_REQUEST,
        )

    data = serializer.validated_data
    if "core_reasons_of_learning" in data:
        available_options = set(_get_core_reasons_options())
        selected_reasons = data["core_reasons_of_learning"]
        invalid_reasons = [reason for reason in selected_reasons if reason not in available_options]
        if invalid_reasons:
            return error_response(
                "Invalid core reasons of learning. Pass exact values from backend options (case-sensitive).",
                {
                    "invalid_core_reasons_of_learning": invalid_reasons,
                    "allowed_core_reasons_options": sorted(available_options),
                },
                status.HTTP_400_BAD_REQUEST,
            )

    with transaction.atomic():
        if "name" in data:
            request.user.full_name = data["name"].strip()
            request.user.save(update_fields=["full_name", "updated_at"])

        profile_fields = (
            "phone_number",
            "age",
            "gender",
            "last_achieved_degree",
            "parents_name",
            "parents_phone_number",
            "preferred_study_time",
            "preferred_study_mode",
            "preferred_study_language",
        )
        for field_name in profile_fields:
            if field_name in data:
                setattr(profile, field_name, data[field_name])
        profile.save()

        if "core_reasons_of_learning" in data:
            selected_reasons = data["core_reasons_of_learning"]
            Intterest.objects.filter(student=request.user).exclude(
                interest_name__in=selected_reasons
            ).delete()
            for reason in selected_reasons:
                Intterest.objects.get_or_create(
                    student=request.user,
                    interest_name=reason,
                )

    if request.method == "POST" and created:
        return success_response(
            _build_profile_setup_payload(request.user, profile),
            message="Profile setup created successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    return success_response(
        _build_profile_setup_payload(request.user, profile),
        message="Profile setup updated successfully.",
    )


@extend_schema(
    tags=["Students Assessment"],
    operation_id="students_assessment_levels",
    responses={
        200: AssessmentTemplateListSuccessResponseSerializer,
    },
    description="Get list of all available assessment levels.",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def assessment_levels(request):
    if request.user.role != UserRole.STUDENT:
        return error_response(
            "Only student users can access this endpoint.",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    templates = AssessmentTemplate.objects.filter(is_active=True).order_by("created_at")
    serializer = AssessmentTemplateListSerializer(templates, many=True)
    return success_response(serializer.data, message="Assessment levels fetched successfully.")


@extend_schema(
    tags=["Students Assessment"],
    operation_id="students_assessment_detail",
    responses={
        200: AssessmentTemplateSuccessResponseSerializer,
        404: OpenApiResponse(description="Assessment level not found."),
    },
    description="Get detailed questions and sections for a specific level.",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def assessment_detail(request, template_id):
    if request.user.role != UserRole.STUDENT:
        return error_response(
            "Only student users can access this endpoint.",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    
    try:
        template = AssessmentTemplate.objects.get(id=template_id, is_active=True)
    except AssessmentTemplate.DoesNotExist:
        return error_response("Assessment level not found.", status_code=status.HTTP_404_NOT_FOUND)

    serializer = AssessmentTemplateDisplaySerializer(template)
    return success_response(serializer.data, message="Assessment questions fetched successfully.")

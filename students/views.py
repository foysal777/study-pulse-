from django.db import transaction
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from accounts.models import UserRole
from common.responses import error_response, success_response
from students.models import (
    Intterest, StudentProfile, AssessmentTemplate,
    AssessmentQuestion, AssessmentOption,
    StudentAssessmentAttempt, StudentAssessmentAnswer,
    AssessmentAttemptStatus, AssessmentLevelBand
)
from students.serializers import (
    StudentErrorResponseSerializer,
    StudentInterestOptionsSuccessResponseSerializer,
    StudentProfileSetupSuccessResponseSerializer,
    StudentProfileSetupUpsertSerializer,
    AssessmentTemplateDisplaySerializer,
    AssessmentTemplateListSerializer,
    AssessmentTemplateSuccessResponseSerializer,
    AssessmentTemplateListSuccessResponseSerializer,
    ExamSubmitRequestSerializer,
    AssessmentResultSuccessResponseSerializer,
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


@extend_schema(
    tags=["Students Assessment"],
    operation_id="students_assessment_submit",
    request=ExamSubmitRequestSerializer,
    responses={
        200: AssessmentResultSuccessResponseSerializer,
        400: OpenApiResponse(response=StudentErrorResponseSerializer, description="Validation error."),
        403: OpenApiResponse(response=StudentErrorResponseSerializer, description="Only students allowed."),
        404: OpenApiResponse(description="Assessment level not found."),
    },
    description=(
        "Submit answers for an assessment level. "
        "Returns skill-wise scores, overall percentage, pass/fail result, and mapped level."
    ),
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def assessment_submit(request, template_id):
    if request.user.role != UserRole.STUDENT:
        return error_response(
            "Only student users can access this endpoint.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    try:
        template = AssessmentTemplate.objects.prefetch_related(
            "sections__questions__options"
        ).get(id=template_id, is_active=True)
    except AssessmentTemplate.DoesNotExist:
        return error_response("Assessment level not found.", status_code=status.HTTP_404_NOT_FOUND)

    serializer = ExamSubmitRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response("Validation error", serializer.errors, status.HTTP_400_BAD_REQUEST)

    submitted_answers = serializer.validated_data["answers"]

    # Build lookup maps
    all_questions = {}
    all_options = {}
    for section in template.sections.all():
        for question in section.questions.all():
            all_questions[question.id] = question
            for option in question.options.all():
                all_options[option.id] = option

    if not all_questions:
        return error_response(
            "This assessment has no questions yet.",
            status_code=status.HTTP_400_BAD_REQUEST
        )

    with transaction.atomic():
        # Create attempt record
        attempt = StudentAssessmentAttempt.objects.create(
            student=request.user,
            template=template,
            status=AssessmentAttemptStatus.SUBMITTED,
            submitted_at=timezone.now(),
        )

        skill_earned = {}   # skill -> earned marks
        skill_max = {}      # skill -> total max marks
        answer_objects = []

        for ans in submitted_answers:
            q_id = ans["question_id"]
            if q_id not in all_questions:
                continue  # skip unknown question ids

            question = all_questions[q_id]
            skill = question.section.skill
            skill_max[skill] = skill_max.get(skill, Decimal("0")) + question.marks

            selected_option = None
            is_correct = None
            auto_score = Decimal("0")

            opt_id = ans.get("selected_option_id")
            if opt_id and opt_id in all_options:
                selected_option = all_options[opt_id]
                # Validate option belongs to the question
                if selected_option.question_id == question.id:
                    is_correct = selected_option.is_correct
                    auto_score = question.marks if is_correct else Decimal("0")
                else:
                    selected_option = None  # invalid pairing

            skill_earned[skill] = skill_earned.get(skill, Decimal("0")) + auto_score

            answer_objects.append(StudentAssessmentAnswer(
                attempt=attempt,
                question=question,
                selected_option=selected_option,
                text_answer=ans.get("text_answer", ""),
                is_correct=is_correct,
                auto_score=auto_score,
            ))

        StudentAssessmentAnswer.objects.bulk_create(answer_objects, ignore_conflicts=True)

        # Aggregate scores
        total_earned = sum(skill_earned.values(), Decimal("0"))
        total_max = sum(skill_max.values(), Decimal("0"))

        overall_pct = (
            (total_earned * Decimal("100") / total_max).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if total_max > 0 else Decimal("0")
        )
        is_passed = overall_pct >= template.pass_percentage

        # Per-skill score fields on attempt
        skill_field_map = {
            "reading": "reading_score",
            "listening": "listening_score",
            "writing": "writing_score",
            "grammar": "grammar_score",
            "vocabulary": "vocabulary_score",
        }
        for skill, field in skill_field_map.items():
            setattr(attempt, field, skill_earned.get(skill, None))

        attempt.total_score = total_earned
        attempt.is_passed = is_passed
        attempt.status = AssessmentAttemptStatus.EVALUATED
        attempt.evaluated_at = timezone.now()
        attempt.save()

        # Find mapped level
        mapped_level = None
        level_band = (
            AssessmentLevelBand.objects
            .filter(template=template, min_score__lte=overall_pct, max_score__gte=overall_pct)
            .first()
        )
        if level_band:
            mapped_level = level_band.get_label_display()

        # Build skill_scores list
        skill_scores = []
        for section in template.sections.all():
            skill = section.skill
            earned = skill_earned.get(skill, Decimal("0"))
            max_s = skill_max.get(skill, Decimal("0"))
            pct = (
                (earned * Decimal("100") / max_s).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                if max_s > 0 else Decimal("0")
            )
            skill_scores.append({
                "skill": skill,
                "score": earned,
                "max_score": max_s,
                "percentage": pct,
            })

    result = {
        "attempt_id": attempt.id,
        "template_name": template.name,
        "total_score": total_earned,
        "max_total_score": total_max,
        "overall_percentage": overall_pct,
        "is_passed": is_passed,
        "pass_percentage": template.pass_percentage,
        "mapped_level": mapped_level,
        "skill_scores": skill_scores,
    }
    return success_response(result, message="Exam submitted and evaluated successfully.")

from django.db import transaction
from django.db.models import F
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
from drf_spectacular.utils import OpenApiResponse, extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated

from accounts.models import UserRole
from common.responses import error_response, success_response
from common.utils import send_expo_push_notification
from students.models import (
    Intterest, InterestSummary, StudentProfile, StudentLocation, AssessmentTemplate,
    AssessmentQuestion, AssessmentOption,
    StudentAssessmentAttempt, StudentAssessmentAnswer,
    AssessmentAttemptStatus, AssessmentLevelBand, RecommendedCourse
)
from teachers.models import (
    StudentBooking, TeacherSlot
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
    StudentDashboardSuccessResponseSerializer,
    StudentLocationUpsertSerializer,
    StudentLocationSuccessResponseSerializer,
    RecommendedCourseSuccessResponseSerializer,
    RecommendedCourseDataSerializer,
    GeneralInfoDataSerializer,
    GeneralInfoSuccessResponseSerializer,
    StudentNotificationSerializer,
    StudentNotificationSuccessResponseSerializer,
    RandomQuizSuccessResponseSerializer,
    RandomQuizQuestionSerializer,
    RandomQuizSubmitResponseSerializer,
    RandomQuizScoresListResponseSerializer,
)
from teachers.models import StudentBooking, GeneralInfo
from students.models import StudentNotification


def _get_core_reasons_options():
    return list(
        InterestSummary.objects.order_by("interest_name")
        .values_list("interest_name", flat=True)
    )


def _compute_profile_completion(user):
    """is_profile_completed=True when required second-page fields are all filled."""
    try:
        profile = user.student_profile
    except Exception:
        return False

    has_study_time = bool(profile.preferred_study_time)
    has_study_mode = bool(profile.preferred_study_mode)
    has_study_language = bool(profile.preferred_study_language)

    return (
        has_study_time and has_study_mode and has_study_language
    )


def _build_profile_setup_payload(request, user, profile):
    interest_options = _get_core_reasons_options()
    selected_reasons = list(
        Intterest.objects.filter(student=user)
        .order_by("interest_name")
        .values_list("interest_name", flat=True)
    )
    has_location = StudentLocation.objects.filter(student=user).exists()
    return {
        "last_achieved_degree": profile.last_achieved_degree,
        "profile_picture": request.build_absolute_uri(profile.profile_picture.url) if profile.profile_picture else None,
        "parents_name": profile.parents_name,
        "parents_phone_number": profile.parents_phone_number,
        "is_location": has_location,
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
    request={
        "multipart/form-data": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "phone": {"type": "string"},
                "age": {"type": "integer"},
                "gender": {"type": "string"},
                "last_achieved_degree": {"type": "string"},
                "profile_picture": {"type": "string", "format": "binary"},
                "parents_name": {"type": "string"},
                "parents_phone_number": {"type": "string"},
                "core_reasons_of_learning": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "preferred_study_time": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "preferred_study_mode": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "preferred_study_language": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
        },
    },
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
        "Use multipart/form-data to upload profile_picture. "
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
            _build_profile_setup_payload(request, request.user, profile),
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


    with transaction.atomic():
        if "name" in data:
            request.user.full_name = data["name"].strip()
            request.user.save(update_fields=["full_name", "updated_at"])

        if "phone" in data:
            profile.phone_number = data["phone"]

        if "profile_picture" in data and data["profile_picture"] is not None:
            profile.profile_picture = data["profile_picture"]

        profile_fields = (
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
        
        request.user.is_profile_completed = _compute_profile_completion(request.user)
        request.user.save(update_fields=["is_profile_completed", "updated_at"])

    if request.method == "POST" and created:
        return success_response(
            _build_profile_setup_payload(request, request.user, profile),
            message="Profile setup created successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    return success_response(
        _build_profile_setup_payload(request, request.user, profile),
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

    serializer = AssessmentTemplateDisplaySerializer(template, context={"request": request})
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

        if not request.user.is_first_assement_completed:
            request.user.is_first_assement_completed = True
            request.user.save(update_fields=["is_first_assement_completed", "updated_at"])

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

    if request.user.expo_push_token and request.user.is_push_notification:
        status_msg = "Passed 🎉" if is_passed else "Keep practicing 💪"
        level_msg = f" (Level: {mapped_level})" if mapped_level else ""
        
        send_expo_push_notification(
            push_tokens=request.user.expo_push_token,
            title="Assessment Result Available",
            body=f"You scored {overall_pct}% in {template.name}. {status_msg}{level_msg}"
        )

    return success_response(result, message="Exam submitted and evaluated successfully.")


@extend_schema(
    tags=["Students Dashboard"],
    operation_id="students_dashboard",
    responses={200: StudentDashboardSuccessResponseSerializer},
    description="Fetch student dashboard data: profile, upcoming session, and progress.",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def student_dashboard(request):
    if request.user.role != UserRole.STUDENT:
        return error_response(
            "Only student users can access this endpoint.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    profile, _ = StudentProfile.objects.get_or_create(student=request.user)
    
    # 1. Student Info
    student_name = profile.student_name if profile.student_name else request.user.full_name
    
    # 2. Upcoming Session
    now = timezone.now()
    upcoming_booking = StudentBooking.objects.filter(
        student=request.user,
        slot__date__gte=now.date()
    ).order_by("slot__date", "slot__start_time").first()
    
    upcoming_session = None
    if upcoming_booking:
        slot = upcoming_booking.slot
        upcoming_session = {
            "title": "English Lesson",
            "date": slot.date.strftime("%a, %b %d"),
            "time": slot.start_time.strftime("%I:%M %p"),
            "mode": slot.mode,
            "meeting_link": slot.accessible_meeting_link,
        }

    # 3. My Progress (Bookings with marks)
    bookings_with_marks = StudentBooking.objects.filter(
        student=request.user,
        marks__isnull=False
    ).order_by("booked_at")
    
    my_progress = []
    for i, b in enumerate(bookings_with_marks):
        my_progress.append({
            "id": b.id,
            "test_name": f"Progress test {i + 1}",
            "percentage": f"{b.marks}%",
            "feedback": b.feedback if b.feedback else "Good progress!",
        })



    payload = {
        "student_name": student_name,
        "profile_picture": request.build_absolute_uri(profile.profile_picture.url) if profile.profile_picture else None,
        "upcoming_session": upcoming_session,
        "my_progress": my_progress,
    }
    
    return success_response(payload, message="Dashboard data fetched successfully.")


@extend_schema(
    methods=["POST"],
    tags=["Students Booking"],
    operation_id="students_cancel_booking",
    responses={200: OpenApiResponse(description="Booking cancelled successfully.")},
    description="Cancel a student booking. Atomically decrements the booked_students count.",
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cancel_booking(request, booking_id):
    try:
        with transaction.atomic():
            booking = StudentBooking.objects.select_related("slot").get(id=booking_id, student=request.user)
            slot = booking.slot
            
            # Decrement booked_students
            TeacherSlot.objects.filter(pk=slot.pk).update(booked_students=F("booked_students") - 1)
            
            # Delete booking
            booking.delete()
            
            return success_response(message="Booking cancelled successfully.")
    except StudentBooking.DoesNotExist:
        return error_response("Booking not found.", status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return error_response(f"Cancellation failed: {str(e)}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=["Students Location"],
    operation_id="students_update_location",
    request=StudentLocationUpsertSerializer,
    responses={
        200: StudentLocationSuccessResponseSerializer,
        400: OpenApiResponse(response=StudentErrorResponseSerializer, description="Validation error."),
        401: OpenApiResponse(response=StudentErrorResponseSerializer, description="Authentication required."),
        403: OpenApiResponse(response=StudentErrorResponseSerializer, description="Only students allowed."),
    },
    description="Save or update the authenticated student's current location (latitude & longitude).",
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_student_location(request):
    if request.user.role != UserRole.STUDENT:
        return error_response(
            "Only student users can access this endpoint.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    serializer = StudentLocationUpsertSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response(
            "Validation error",
            serializer.errors,
            status.HTTP_400_BAD_REQUEST,
        )

    location, _ = StudentLocation.objects.update_or_create(
        student=request.user,
        defaults={
            "latitude": serializer.validated_data["latitude"],
            "longitude": serializer.validated_data["longitude"],
        },
    )

    return success_response(
        {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "updated_at": location.updated_at,
        },
        message="Location updated successfully.",
    )


@extend_schema(
    summary="Get Recommended Course based on latest assessment",
    responses={
        200: OpenApiResponse(
            response=RecommendedCourseSuccessResponseSerializer,
            description="Recommended course retrieved successfully.",
        ),
        400: OpenApiResponse(
            response=StudentErrorResponseSerializer,
            description="No assessment found.",
        ),
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_recommended_course(request):
    """
    Returns the recommended course based on the student's latest assessment score.
    """
    if request.user.role != UserRole.STUDENT:
        return error_response(
            "Access denied",
            "Only students can access recommended courses.",
            status.HTTP_403_FORBIDDEN,
        )

    # Get latest evaluated assessment attempt
    latest_attempt = StudentAssessmentAttempt.objects.filter(
        student=request.user,
        status=AssessmentAttemptStatus.EVALUATED
    ).order_by("-evaluated_at").first()

    if not latest_attempt:
        return error_response(
            "No assessment found",
            "You have not completed any assessments yet.",
            status.HTTP_400_BAD_REQUEST,
        )

    template_name = latest_attempt.template.name.lower()
    total_max = sum(q.marks for s in latest_attempt.template.sections.all() for q in s.questions.all())
    overall_percentage = (latest_attempt.total_score * Decimal("100") / total_max) if total_max > 0 else Decimal("0")

    recommended_name = None
    if "upper-intermediate" in template_name or "upper intermediate" in template_name:
        recommended_name = "Intermediate" if overall_percentage < 70 else "Upper-Intermediate"
    elif "pre-intermediate" in template_name or "pre intermediate" in template_name:
        recommended_name = "Elementary" if overall_percentage < 70 else "Pre-Intermediate"
    elif "intermediate" in template_name:
        recommended_name = "Pre-Intermediate" if overall_percentage < 70 else "Intermediate"
    elif "elementary" in template_name:
        if overall_percentage < 50:
            recommended_name = "Starter"
        elif overall_percentage < 70:
            recommended_name = "Elementary"
        else:
            recommended_name = "Pre-Intermediate"

    if not recommended_name:
        return error_response(
            "Recommendation failed",
            "Could not determine recommended course based on template name.",
            status.HTTP_400_BAD_REQUEST,
        )

    course = RecommendedCourse.objects.filter(course_name__icontains=recommended_name).first()
    if not course:
        return error_response(
            "Course not found",
            f"Recommended course '{recommended_name}' is not currently available.",
            status.HTTP_404_NOT_FOUND,
        )

    serializer = RecommendedCourseDataSerializer(course, context={"request": request})
    return success_response(
        serializer.data,
        message=f"Recommended course for {recommended_name} retrieved successfully."
    )


@extend_schema(
    summary="Get General Info and Course Calendar",
    responses={
        200: OpenApiResponse(
            response=GeneralInfoSuccessResponseSerializer,
            description="General info retrieved successfully.",
        ),
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_general_info(request):
    """
    Returns general info (social links) and the specific calendar based on the student's latest assessment score.
    """
    if request.user.role != UserRole.STUDENT:
        return error_response(
            "Access denied",
            "Only students can access this info.",
            status.HTTP_403_FORBIDDEN,
        )

    # Base general info
    general_info = GeneralInfo.objects.filter(is_deleted=False)

    latest_attempt = StudentAssessmentAttempt.objects.filter(
        student=request.user,
        status=AssessmentAttemptStatus.EVALUATED
    ).order_by("-evaluated_at").first()

    info_obj = None

    if latest_attempt:
        template_name = latest_attempt.template.name.lower()
        total_max = sum(q.marks for s in latest_attempt.template.sections.all() for q in s.questions.all())
        overall_percentage = (latest_attempt.total_score * Decimal("100") / total_max) if total_max > 0 else Decimal("0")

        recommended_name = None
        if "upper-intermediate" in template_name or "upper intermediate" in template_name:
            recommended_name = "Intermediate" if overall_percentage < 70 else "Upper-Intermediate"
        elif "pre-intermediate" in template_name or "pre intermediate" in template_name:
            recommended_name = "Elementary" if overall_percentage < 70 else "Pre-Intermediate"
        elif "intermediate" in template_name:
            recommended_name = "Pre-Intermediate" if overall_percentage < 70 else "Intermediate"
        elif "elementary" in template_name:
            if overall_percentage < 50:
                recommended_name = "Starter"
            elif overall_percentage < 70:
                recommended_name = "Elementary"
            else:
                recommended_name = "Pre-Intermediate"

        if recommended_name:
            info_obj = general_info.filter(calender_type__icontains=recommended_name).first()

    if not info_obj:
        # Fallback to the latest available general info if no match found
        info_obj = general_info.order_by("-created_at").first()

    if not info_obj:
        return error_response(
            "Not found",
            "No general information is currently available.",
            status.HTTP_404_NOT_FOUND,
        )

    serializer = GeneralInfoDataSerializer(info_obj, context={"request": request})
    return success_response(
        serializer.data,
        message="General info retrieved successfully."
    )


@extend_schema(
    methods=["GET"],
    summary="Get Student Notifications",
    responses={
        200: OpenApiResponse(
            response=StudentNotificationSuccessResponseSerializer,
            description="Notifications retrieved successfully.",
        ),
    },
)
@extend_schema(
    methods=["DELETE"],
    summary="Delete Student Notifications",
    parameters=[
        OpenApiParameter(name="id", description="Optional ID of a specific notification to delete. If not provided, all notifications are deleted.", required=False, type=int),
    ],
    responses={
        200: OpenApiResponse(description="Notification(s) deleted successfully."),
    },
)
@api_view(["GET", "DELETE"])
@permission_classes([IsAuthenticated])
def get_student_notifications(request):
    if request.user.role != UserRole.STUDENT:
        return error_response(
            "Access denied",
            "Only students can access this info.",
            status.HTTP_403_FORBIDDEN,
        )

    if request.method == "DELETE":
        notification_id = request.query_params.get("id")
        if notification_id:
            StudentNotification.objects.filter(student=request.user, id=notification_id).delete()
            return success_response(message="Notification deleted successfully.")
        else:
            StudentNotification.objects.filter(student=request.user).delete()
            return success_response(message="All notifications deleted successfully.")

    notifications = StudentNotification.objects.filter(student=request.user)
    serializer = StudentNotificationSerializer(notifications, many=True)
    
    # Mark as read
    notifications.filter(is_read=False).update(is_read=True)

    return success_response(
        serializer.data,
        message="Notifications retrieved successfully."
    )


@extend_schema(
    methods=["GET"],
    tags=["Students Assessment"],
    operation_id="students_assessment_result",
    responses={200: AssessmentResultSuccessResponseSerializer},
    description="Get the detailed result (score breakdown) of a specific assessment attempt.",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def assessment_result(request, attempt_id):
    if request.user.role != UserRole.STUDENT:
        return error_response(
            "Only student users can access this endpoint.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    try:
        attempt = StudentAssessmentAttempt.objects.select_related("template").get(
            id=attempt_id,
            student=request.user,
            status=AssessmentAttemptStatus.EVALUATED
        )
    except StudentAssessmentAttempt.DoesNotExist:
        return error_response("Assessment attempt not found or not yet evaluated.", status_code=status.HTTP_404_NOT_FOUND)

    template = attempt.template

    # Calculate max scores per skill
    skill_max = {}
    for section in template.sections.all():
        skill = section.skill
        # Need to sum marks of all active questions in this section
        section_max = sum(q.marks for q in section.questions.all())
        skill_max[skill] = skill_max.get(skill, Decimal("0")) + section_max

    total_max = sum(skill_max.values(), Decimal("0"))
    overall_pct = (attempt.total_score * Decimal("100") / total_max).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if total_max > 0 else Decimal("0")

    # Find mapped level
    mapped_level = None
    level_band = AssessmentLevelBand.objects.filter(
        template=template,
        min_score__lte=overall_pct,
        max_score__gte=overall_pct
    ).first()
    
    if level_band:
        mapped_level = level_band.get_label_display()

    skill_field_map = {
        "reading": attempt.reading_score,
        "listening": attempt.listening_score,
        "writing": attempt.writing_score,
        "grammar": attempt.grammar_score,
        "vocabulary": attempt.vocabulary_score,
    }

    skill_scores = []
    for skill, max_s in skill_max.items():
        earned = skill_field_map.get(skill) or Decimal("0")
        pct = (earned * Decimal("100") / max_s).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if max_s > 0 else Decimal("0")
        skill_scores.append({
            "skill": skill,
            "score": earned,
            "max_score": max_s,
            "percentage": pct,
        })

    try:
        profile = request.user.student_profile
        student_name = profile.student_name if profile.student_name else request.user.full_name
        profile_picture = request.build_absolute_uri(profile.profile_picture.url) if profile.profile_picture else None
    except Exception:
        student_name = request.user.full_name
        profile_picture = None

    result = {
        "student_name": student_name,
        "profile_picture": profile_picture,
        "attempt_id": attempt.id,
        "template_name": template.name,
        "total_score": attempt.total_score,
        "max_total_score": total_max,
        "overall_percentage": overall_pct,
        "is_passed": attempt.is_passed,
        "pass_percentage": template.pass_percentage,
        "mapped_level": mapped_level,
        "skill_scores": skill_scores,
    }

    return success_response(result, message="Assessment result fetched successfully.")


@extend_schema(
    tags=["Students Assessment"],
    operation_id="students_random_quiz",
    responses={200: RandomQuizSuccessResponseSerializer},
    description="Generate a random quiz consisting of 20 questions distributed across the active assessment levels.",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def random_quiz(request):
    if request.user.role != UserRole.STUDENT:
        return error_response(
            "Only student users can access this endpoint.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    import random
    templates = list(AssessmentTemplate.objects.filter(is_active=True))
    questions = []

    if templates:
        target_per_template = max(1, 20 // len(templates))
        extra_needed = 20 - (target_per_template * len(templates))

        for i, t in enumerate(templates):
            count_needed = target_per_template + (1 if i < extra_needed else 0)
            t_questions = list(
                AssessmentQuestion.objects.filter(section__template=t, is_active=True)
                .prefetch_related("options")
            )
            if len(t_questions) >= count_needed:
                selected = random.sample(t_questions, count_needed)
            else:
                selected = t_questions
            questions.extend(selected)

        # Fallback to fill up to 20 questions if some templates had too few questions
        if len(questions) < 20:
            selected_ids = [q.id for q in questions]
            all_active_qs = list(
                AssessmentQuestion.objects.filter(section__template__is_active=True, is_active=True)
                .exclude(id__in=selected_ids)
                .prefetch_related("options")
            )
            needed = 20 - len(questions)
            if all_active_qs:
                extra_selected = random.sample(all_active_qs, min(len(all_active_qs), needed))
                questions.extend(extra_selected)
    else:
        # Ultimate fallback: fetch any active questions if templates are not configured
        all_qs = list(
            AssessmentQuestion.objects.filter(is_active=True)
            .prefetch_related("options")
        )
        questions = random.sample(all_qs, min(len(all_qs), 20))

    # Shuffle the final set of questions to mix the levels
    random.shuffle(questions)

    serializer = RandomQuizQuestionSerializer(questions, many=True, context={"request": request})
    return success_response(serializer.data, message="Random quiz questions fetched successfully.")


@extend_schema(
    tags=["Students Assessment"],
    operation_id="students_random_quiz_submit",
    request=ExamSubmitRequestSerializer,
    responses={200: RandomQuizSubmitResponseSerializer},
    description="Submit and instantly evaluate answers for the random quiz.",
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def random_quiz_submit(request):
    if request.user.role != UserRole.STUDENT:
        return error_response(
            "Only student users can access this endpoint.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    serializer = ExamSubmitRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response("Validation error", serializer.errors, status.HTTP_400_BAD_REQUEST)

    submitted_answers = serializer.validated_data["answers"]
    submitted_q_ids = [ans["question_id"] for ans in submitted_answers]

    # Pre-fetch questions and options to minimize DB queries
    questions_qs = AssessmentQuestion.objects.filter(
        id__in=submitted_q_ids, is_active=True
    ).select_related("section__template").prefetch_related("options")

    questions_map = {q.id: q for q in questions_qs}

    total_questions = len(submitted_answers)
    total_correct = 0
    overall_score = Decimal("0")
    max_score = Decimal("0")

    # Group by levels/templates
    level_breakdown_dict = {}
    detailed_results = []

    for ans in submitted_answers:
        q_id = ans["question_id"]
        question = questions_map.get(q_id)

        if not question:
            continue

        template = question.section.template
        t_id = template.id
        level_name = template.name

        if t_id not in level_breakdown_dict:
            level_breakdown_dict[t_id] = {
                "level_name": level_name,
                "total": 0,
                "correct": 0,
                "score": Decimal("0"),
                "max_score": Decimal("0"),
            }

        level_data = level_breakdown_dict[t_id]
        level_data["total"] += 1
        level_data["max_score"] += question.marks
        max_score += question.marks

        selected_option = None
        is_correct = False
        correct_option = None

        # Find the correct option for this question
        for opt in question.options.all():
            if opt.is_correct:
                correct_option = opt
                break

        opt_id = ans.get("selected_option_id")
        if opt_id:
            for opt in question.options.all():
                if opt.id == opt_id:
                    selected_option = opt
                    break

        if selected_option and selected_option.is_correct:
            is_correct = True
            total_correct += 1
            overall_score += question.marks
            level_data["correct"] += 1
            level_data["score"] += question.marks

        detailed_results.append({
            "question_id": question.id,
            "prompt": question.prompt,
            "level_name": level_name,
            "submitted_option_id": opt_id,
            "is_correct": is_correct,
            "correct_option_id": correct_option.id if correct_option else None,
            "correct_option_text": correct_option.text if correct_option else "",
        })

    # Convert level breakdowns to list and calculate percentages
    level_breakdown = []
    for t_id, item in level_breakdown_dict.items():
        max_s = item["max_score"]
        pct = (
            (item["score"] * Decimal("100") / max_s).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if max_s > 0 else Decimal("0")
        )
        level_breakdown.append({
            "level_name": item["level_name"],
            "total": item["total"],
            "correct": item["correct"],
            "score": item["score"],
            "max_score": max_s,
            "percentage": pct,
        })

    overall_percentage = (
        (overall_score * Decimal("100") / max_score).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if max_score > 0 else Decimal("0")
    )

    # Smart Suggested Level logic
    templates_sorted = sorted(list(AssessmentTemplate.objects.filter(is_active=True)), key=lambda x: x.id)
    suggested_level = "Elementary (A1)"

    achieved_pct = {}
    for item in level_breakdown_dict.keys():
        lbl_data = level_breakdown_dict[item]
        max_s = lbl_data["max_score"]
        achieved_pct[item] = (lbl_data["score"] / max_s) if max_s > 0 else 0

    for t in templates_sorted:
        pct = achieved_pct.get(t.id, 0)
        if pct < 0.60:
            suggested_level = t.name
            break
    else:
        if templates_sorted:
            suggested_level = templates_sorted[-1].name

    # Dynamic sequence score mapping
    score_fields = ["reading_score", "listening_score", "writing_score", "grammar_score"]
    scores_mapping = {field: Decimal("0") for field in score_fields}
    for i, t in enumerate(templates_sorted):
        if i < len(score_fields):
            scores_mapping[score_fields[i]] = level_breakdown_dict.get(t.id, {}).get("score", Decimal("0"))

    with transaction.atomic():
        random_template, _ = AssessmentTemplate.objects.get_or_create(
            name="Random Quiz",
            defaults={
                "description": "Template for random placement quizzes.",
                "pass_percentage": 60.0,
                "is_active": False,
            }
        )

        attempt = StudentAssessmentAttempt.objects.create(
            student=request.user,
            template=random_template,
            status=AssessmentAttemptStatus.EVALUATED,
            total_score=overall_score,
            is_passed=overall_percentage >= 60,
            reading_score=scores_mapping["reading_score"],
            listening_score=scores_mapping["listening_score"],
            writing_score=scores_mapping["writing_score"],
            grammar_score=scores_mapping["grammar_score"],
            evaluated_at=timezone.now(),
            submitted_at=timezone.now(),
        )

        answer_objects = []
        for ans in submitted_answers:
            q_id = ans["question_id"]
            question = questions_map.get(q_id)
            if not question:
                continue

            selected_option = None
            opt_id = ans.get("selected_option_id")
            if opt_id:
                for opt in question.options.all():
                    if opt.id == opt_id:
                        selected_option = opt
                        break

            is_correct = selected_option.is_correct if selected_option else False

            answer_objects.append(StudentAssessmentAnswer(
                attempt=attempt,
                question=question,
                selected_option=selected_option,
                text_answer=ans.get("text_answer", ""),
                is_correct=is_correct,
                auto_score=question.marks if is_correct else Decimal("0"),
            ))

        StudentAssessmentAnswer.objects.bulk_create(answer_objects, ignore_conflicts=True)

    result_payload = {
        "total_questions": total_questions,
        "total_correct": total_correct,
        "overall_score": overall_score,
        "max_score": max_score,
        "overall_percentage": overall_percentage,
        "suggested_level": suggested_level,
        "level_breakdown": level_breakdown,
        "detailed_results": detailed_results,
    }

    return success_response(result_payload, message="Quiz evaluated successfully.")


@extend_schema(
    tags=["Students Assessment"],
    operation_id="students_quiz_scores",
    responses={200: RandomQuizScoresListResponseSerializer},
    description="Retrieve a list of quiz attempts and marks. Students get their own scores; Teachers/Admins get scores for all students.",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def student_quiz_scores(request):
    if request.user.role in [UserRole.TEACHER, UserRole.ADMIN]:
        # Teacher/Admin wants to see all student scores for "Random Quiz"
        attempts = StudentAssessmentAttempt.objects.filter(
            template__name="Random Quiz",
            status=AssessmentAttemptStatus.EVALUATED
        ).select_related("student", "template").order_by("-evaluated_at")
    else:
        # Student wants to see their own scores for "Random Quiz"
        attempts = StudentAssessmentAttempt.objects.filter(
            student=request.user,
            template__name="Random Quiz",
            status=AssessmentAttemptStatus.EVALUATED
        ).select_related("student", "template").order_by("-evaluated_at")

    templates_sorted = sorted(list(AssessmentTemplate.objects.filter(is_active=True)), key=lambda x: x.id)

    scores_list = []
    for attempt in attempts:
        achieved_pct = {
            "reading_score": attempt.reading_score or Decimal("0"),
            "listening_score": attempt.listening_score or Decimal("0"),
            "writing_score": attempt.writing_score or Decimal("0"),
            "grammar_score": attempt.grammar_score or Decimal("0"),
        }

        score_fields = ["reading_score", "listening_score", "writing_score", "grammar_score"]
        suggested_level = "Elementary (A1)"

        for i, t in enumerate(templates_sorted):
            if i < len(score_fields):
                drawn_count = attempt.answers.filter(question__section__template=t).count() or 5
                earned = achieved_pct[score_fields[i]]
                pct = earned / Decimal(drawn_count) if drawn_count > 0 else 0
                if pct < 0.60:
                    suggested_level = t.name
                    break
        else:
            if templates_sorted:
                suggested_level = templates_sorted[-1].name

        scores_list.append({
            "attempt_id": attempt.id,
            "student_id": attempt.student.id,
            "student_name": attempt.student.full_name,
            "student_email": attempt.student.email,
            "overall_score": attempt.total_score,
            "max_score": Decimal("20.00"),
            "overall_percentage": (attempt.total_score * Decimal("100") / Decimal("20")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "suggested_level": suggested_level,
            "evaluated_at": attempt.evaluated_at,
        })

    return success_response(scores_list, message="Student quiz scores retrieved successfully.")



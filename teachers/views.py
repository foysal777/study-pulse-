from drf_spectacular.utils import OpenApiResponse, extend_schema, OpenApiParameter, OpenApiTypes
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
    TeachersLocationSerializer,
    TeacherAvailabilitySerializer,
    AvailableSlotSerializer,
    StudentBookingSerializer,
    SessionListSerializer,
    TeacherBookedSlotSerializer,
    TeacherStudentListSerializer,
    TeacherFeedbackSerializer,
    PendingRequestSerializer,
    CancellationRequestSubmitSerializer,
    SessionNoticeSerializer,
    TeacherDashboardSerializer,
)
from common.utils import send_expo_push_notification
from teachers.models import (
    TeacherAvailability,
    TeacherSlot,
    StudentBooking,
    SlotMode,
    PendingRequest,
    RequestStatus,
    RequestType,
)
from django.db import transaction
from django.db.models import F, Sum, Min
from datetime import datetime, timedelta


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
            request.user.is_profile_completed = True
            request.user.save(update_fields=["is_profile_completed", "updated_at"])
            return success_response(serializer.data, message="Profile created successfully.", status_code=status.HTTP_201_CREATED)
        return error_response("Validation error", serializer.errors, status.HTTP_400_BAD_REQUEST)

    if request.method == "PATCH":
        if not profile:
            return error_response("Profile not found. Use POST to create.", status_code=status.HTTP_404_NOT_FOUND)
        serializer = TeacherProfileSerializer(profile, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            request.user.is_profile_completed = True
            request.user.save(update_fields=["is_profile_completed", "updated_at"])
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


@extend_schema(
    methods=["POST"],
    tags=["Teachers Location"],
    operation_id="teachers_location_create",
    request=TeachersLocationSerializer,
    responses={
        201: TeachersLocationSerializer,
        400: OpenApiResponse(response=TeacherErrorResponseSerializer, description="Validation error."),
        403: OpenApiResponse(response=TeacherErrorResponseSerializer, description="Only teacher users can access this endpoint."),
        404: OpenApiResponse(response=TeacherErrorResponseSerializer, description="Profile not found."),
    },
    description="Store the teacher's current location (latitude and longitude).",
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def teacher_location(request):
    if request.user.role != UserRole.TEACHER:
        return error_response(
            "Only teacher users can access this endpoint.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    try:
        profile = TeacherProfile.objects.get(user=request.user)
    except TeacherProfile.DoesNotExist:
        return error_response("Teacher profile not found.", status_code=status.HTTP_404_NOT_FOUND)

    serializer = TeachersLocationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(teacher=profile)
        return success_response(serializer.data, message="Location saved successfully.", status_code=status.HTTP_201_CREATED)
    return error_response("Validation error", serializer.errors, status.HTTP_400_BAD_REQUEST)


@extend_schema(
    methods=["GET"],
    tags=["Teachers Availability"],
    operation_id="teachers_availability_list",
    responses={200: TeacherAvailabilitySerializer(many=True)},
    description="Fetch current teacher's weekly availability.",
)
@extend_schema(
    methods=["POST"],
    tags=["Teachers Availability"],
    operation_id="teachers_availability_create",
    request=TeacherAvailabilitySerializer,
    responses={201: TeacherAvailabilitySerializer},
    description="Teacher sets their weekly availability. Example: Monday 09:00:00 to 10:00:00 ONLINE.",
)
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def teacher_availability(request):
    if request.user.role != UserRole.TEACHER:
        return error_response("Only teachers can access availability.", status_code=status.HTTP_403_FORBIDDEN)

    try:
        profile = TeacherProfile.objects.get(user=request.user)
    except TeacherProfile.DoesNotExist:
        return error_response("Teacher profile not found.", status_code=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        availabilities = TeacherAvailability.objects.filter(teacher=profile)
        serializer = TeacherAvailabilitySerializer(availabilities, many=True)
        return success_response(serializer.data, message="Availability fetched successfully.")

    if request.method == "POST":
        serializer = TeacherAvailabilitySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(teacher=profile)
            return success_response(serializer.data, message="Availability added successfully.", status_code=status.HTTP_201_CREATED)
        return error_response("Validation error", serializer.errors, status.HTTP_400_BAD_REQUEST)


@extend_schema(
    methods=["GET"],
    tags=["Student Booking"],
    operation_id="student_available_slots",
    responses={200: AvailableSlotSerializer(many=True)},
    parameters=[
        OpenApiParameter(name="date", description="Date in YYYY-MM-DD format", required=True, type=OpenApiTypes.DATE),
        OpenApiParameter(name="mode", description="Filter by mode: online or offline", required=False, type=OpenApiTypes.STR),
    ],
    description="Fetch available slots for students. Query params: date (YYYY-MM-DD), mode (online/offline).",
)
@api_view(["GET"])
def student_available_slots(request):
    date_str = request.query_params.get("date")
    mode = request.query_params.get("mode")

    if not date_str:
        return error_response("Date is required (YYYY-MM-DD).", status_code=status.HTTP_400_BAD_REQUEST)

    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return error_response("Invalid date format. Use YYYY-MM-DD.", status_code=status.HTTP_400_BAD_REQUEST)

    day_name = target_date.strftime("%A")  # Monday, Tuesday, etc.

    availabilities = TeacherAvailability.objects.filter(day_of_week=day_name).select_related("teacher")
    if mode:
        availabilities = availabilities.filter(mode=mode)

    # Group by time, mode and location
    slots_map = {}
    for avail in availabilities:
        location = avail.teacher.offline_location if avail.mode == SlotMode.OFFLINE else None
        key = (avail.start_time, avail.end_time, avail.mode, location)
        if key not in slots_map:
            slots_map[key] = {"total_capacity": 0, "total_booked": 0}
        slots_map[key]["total_capacity"] += 40

    # Subtract current bookings
    # We need to find TeacherSlot records for this date
    booked_slots = TeacherSlot.objects.filter(date=target_date).select_related("teacher")
    for bs in booked_slots:
        location = bs.teacher.offline_location if bs.mode == SlotMode.OFFLINE else None
        key = (bs.start_time, bs.end_time, bs.mode, location)
        if key in slots_map:
            slots_map[key]["total_booked"] += bs.booked_students

    available_slots = []
    for (start, end, smode, sloc), counts in slots_map.items():
        capacity_left = counts["total_capacity"] - counts["total_booked"]
        if capacity_left > 0:
            available_slots.append({
                "date": target_date,
                "start_time": start,
                "end_time": end,
                "mode": smode,
                "available_capacity": capacity_left,
                "offline_location": sloc
            })

    # Sort by start time
    available_slots.sort(key=lambda x: x["start_time"])

    serializer = AvailableSlotSerializer(available_slots, many=True)
    return success_response(serializer.data, message="Available slots fetched successfully.")


@extend_schema(
    methods=["POST"],
    tags=["Student Booking"],
    operation_id="student_book_slot",
    request=StudentBookingSerializer,
    responses={201: StudentBookingSerializer},
    description="Book a slot as a student. The system automatically assigns the least booked available teacher.",
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def student_book_slot(request):
    if request.user.role != UserRole.STUDENT:
        return error_response("Only students can book slots.", status_code=status.HTTP_403_FORBIDDEN)
    
    serializer = StudentBookingSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response("Validation error", serializer.errors, status.HTTP_400_BAD_REQUEST)

    date = serializer.validated_data["date"]
    start_time = serializer.validated_data["start_time"]
    mode = serializer.validated_data["mode"]
    offline_location = serializer.validated_data.get("offline_location")
    day_name = date.strftime("%A")

    try:
        with transaction.atomic():
            # 1. Find all teachers available at this time/mode/location
            avail_filters = {
                "day_of_week": day_name,
                "start_time": start_time,
                "mode": mode
            }
            if mode == SlotMode.OFFLINE and offline_location:
                avail_filters["teacher__offline_location"] = offline_location

            available_teachers = TeacherAvailability.objects.filter(**avail_filters).values_list("teacher_id", flat=True)

            if not available_teachers:
                return error_response("No teachers available for this slot.", status_code=status.HTTP_404_NOT_FOUND)

            # 2. Find/Pick the least booked teacher
            # We need to look at TeacherSlot for this date
            # Optimization: Get all existing slots for these teachers on this date
            existing_slots = TeacherSlot.objects.select_for_update().filter(
                teacher_id__in=available_teachers,
                date=date,
                start_time=start_time,
                mode=mode
            )

            slots_by_teacher = {s.teacher_id: s for s in existing_slots}
            
            chosen_teacher_id = None
            min_booked = 41 # max is 40

            for t_id in available_teachers:
                booked = slots_by_teacher[t_id].booked_students if t_id in slots_by_teacher else 0
                if booked < 40 and booked < min_booked:
                    min_booked = booked
                    chosen_teacher_id = t_id

            if chosen_teacher_id is None:
                return error_response("All slots are full for this time.", status_code=status.HTTP_400_BAD_REQUEST)

            # 3. Get or create the slot instance and increment
            slot_instance, created = TeacherSlot.objects.get_or_create(
                teacher_id=chosen_teacher_id,
                date=date,
                start_time=start_time,
                mode=mode,
                defaults={
                    "end_time": (datetime.combine(date, start_time) + timedelta(hours=1)).time() if "end_time" not in request.data else request.data.get("end_time")
                }
            )
            # If created, end_time logic above is a bit messy, let's fix it.
            if created:
                # Find end_time from availability
                avail = TeacherAvailability.objects.get(teacher_id=chosen_teacher_id, day_of_week=day_name, start_time=start_time, mode=mode)
                slot_instance.end_time = avail.end_time
                slot_instance.save()

            if slot_instance.booked_students >= slot_instance.max_students:
                return error_response("Slot just became full. Please try another.", status_code=status.HTTP_400_BAD_REQUEST)

            # Increment atomically
            TeacherSlot.objects.filter(pk=slot_instance.pk).update(booked_students=F("booked_students") + 1)
            slot_instance.refresh_from_db()

            # 4. Create Booking
            booking = StudentBooking.objects.create(
                student=request.user,
                slot=slot_instance
            )
            
            res_serializer = StudentBookingSerializer(booking)
            return success_response(res_serializer.data, message="Slot booked successfully.", status_code=status.HTTP_201_CREATED)

    except Exception as e:
        return error_response(f"Booking failed: {str(e)}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    methods=["POST"],
    tags=["Student Booking"],
    operation_id="student_cancel_booking",
    responses={200: OpenApiResponse(description="Booking cancelled successfully.")},
    description="Cancel a student booking. Atomically decrements the booked_students count.",
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def student_cancel_booking(request, booking_id):
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
    methods=["GET"],
    tags=["Teachers Sessions"],
    operation_id="teachers_booked_sessions_list",
    responses={200: TeacherBookedSlotSerializer(many=True)},
    description="Fetch the list of sessions (slots) that have at least one booking for the logged-in teacher.",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def teacher_booked_sessions(request):
    if request.user.role != UserRole.TEACHER:
        return error_response("Only teachers can access this endpoint.", status_code=status.HTTP_403_FORBIDDEN)

    try:
        profile = TeacherProfile.objects.get(user=request.user)
    except TeacherProfile.DoesNotExist:
        return error_response("Teacher profile not found.", status_code=status.HTTP_404_NOT_FOUND)

    # Filter slots that have at least one booking without feedback
    slots = TeacherSlot.objects.filter(
        teacher=profile,
        bookings__marks__isnull=True,
        bookings__feedback__isnull=True
    ).distinct().order_by("-date", "-start_time")
    
    serializer = TeacherBookedSlotSerializer(slots, many=True)
    return success_response(serializer.data, message="Booked sessions fetched successfully.")


@extend_schema(
    methods=["GET"],
    tags=["Teachers Sessions"],
    operation_id="teachers_slot_students_list",
    responses={200: TeacherStudentListSerializer(many=True)},
    description="Fetch the list of students who booked a specific slot.",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def teacher_slot_students(request, slot_id):
    if request.user.role != UserRole.TEACHER:
        return error_response("Only teachers can access this endpoint.", status_code=status.HTTP_403_FORBIDDEN)

    try:
        slot = TeacherSlot.objects.get(id=slot_id, teacher__user=request.user)
    except TeacherSlot.DoesNotExist:
        return error_response("Slot not found or you don't have access to it.", status_code=status.HTTP_404_NOT_FOUND)

    # Show only students who haven't received feedback yet
    bookings = slot.bookings.filter(marks__isnull=True, feedback__isnull=True).select_related("student")
    serializer = TeacherStudentListSerializer(bookings, many=True)
    return success_response(serializer.data, message="Student list fetched successfully.")


@extend_schema(
    methods=["POST"],
    tags=["Teachers Sessions"],
    operation_id="teachers_student_feedback",
    request=TeacherFeedbackSerializer,
    responses={200: TeacherStudentListSerializer},
    description="Provide feedback and marks for a specific student booking.",
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def teacher_student_feedback(request, booking_id):
    if request.user.role != UserRole.TEACHER:
        return error_response("Only teachers can access this endpoint.", status_code=status.HTTP_403_FORBIDDEN)

    try:
        booking = StudentBooking.objects.get(id=booking_id, slot__teacher__user=request.user)
    except StudentBooking.DoesNotExist:
        return error_response("Booking not found or you don't have access to it.", status_code=status.HTTP_404_NOT_FOUND)

    serializer = TeacherFeedbackSerializer(booking, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return success_response(TeacherStudentListSerializer(booking).data, message="Feedback submitted successfully.")
    return error_response("Invalid data.", errors=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    methods=["POST"],
    tags=["Teachers Requests"],
    operation_id="teachers_request_cancellation",
    request=CancellationRequestSubmitSerializer,
    responses={201: PendingRequestSerializer},
    description="Teacher submits a cancellation request (Session or Availability).",
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def teacher_request_cancellation(request):
    if request.user.role != UserRole.TEACHER:
        return error_response("Only teachers can submit requests.", status_code=status.HTTP_403_FORBIDDEN)

    try:
        profile = TeacherProfile.objects.get(user=request.user)
    except TeacherProfile.DoesNotExist:
        return error_response("Teacher profile not found.", status_code=status.HTTP_404_NOT_FOUND)

    serializer = CancellationRequestSubmitSerializer(data=request.data)
    if serializer.is_valid():
        request_type = serializer.validated_data["request_type"]
        details = serializer.validated_data.get("details", "")
        slot_id = serializer.validated_data.get("slot_id")
        availability_id = serializer.validated_data.get("availability_id")
        
        slot_obj = None
        avail_obj = None

        # 1. Handle Session Cancellation
        if request_type == RequestType.SESSION_CANCELLATION:
            if slot_id:
                try:
                    slot_obj = TeacherSlot.objects.get(id=slot_id, teacher=profile)
                    date_str = slot_obj.date.strftime("%Y-%m-%d")
                    start_time_str = slot_obj.start_time.strftime("%I:%M %p")
                    details = f"Session: {slot_obj.title} on {date_str} at {start_time_str}"
                except TeacherSlot.DoesNotExist:
                    return error_response("Slot not found or does not belong to you.", status_code=status.HTTP_404_NOT_FOUND)
            elif not details:
                return error_response("Slot ID or specific details are required for session cancellation.", status_code=status.HTTP_400_BAD_REQUEST)

        # 2. Handle Availability Withdrawal
        elif request_type == RequestType.AVAILABILITY_WITHDRAWAL:
            if availability_id:
                try:
                    avail_obj = TeacherAvailability.objects.get(id=availability_id, teacher=profile)
                    start_str = avail_obj.start_time.strftime("%I:%M %p")
                    end_str = avail_obj.end_time.strftime("%I:%M %p")
                    details = f"Availability: {avail_obj.day_of_week} ({start_str} - {end_str}) {avail_obj.mode.upper()}"
                except TeacherAvailability.DoesNotExist:
                    return error_response("Availability record not found or does not belong to you.", status_code=status.HTTP_404_NOT_FOUND)
            elif not details:
                return error_response("Availability ID or specific details are required for withdrawal.", status_code=status.HTTP_400_BAD_REQUEST)

        pending_request = PendingRequest.objects.create(
            teacher=profile,
            request_type=request_type,
            details=details,
            slot=slot_obj,
            availability=avail_obj,
            status=RequestStatus.PENDING
        )
        return success_response(
            PendingRequestSerializer(pending_request).data,
            message="Request submitted successfully.",
            status_code=status.HTTP_201_CREATED
        )
    return error_response("Validation error", serializer.errors, status.HTTP_400_BAD_REQUEST)


@extend_schema(
    methods=["GET"],
    tags=["Teachers Requests"],
    operation_id="teachers_pending_requests_list",
    responses={200: PendingRequestSerializer(many=True)},
    description="Fetch the list of cancellation requests for the logged-in teacher.",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def teacher_pending_requests(request):
    if request.user.role != UserRole.TEACHER:
        return error_response("Only teachers can access this endpoint.", status_code=status.HTTP_403_FORBIDDEN)

    try:
        profile = TeacherProfile.objects.get(user=request.user)
    except TeacherProfile.DoesNotExist:
        return error_response("Teacher profile not found.", status_code=status.HTTP_404_NOT_FOUND)

    requests = PendingRequest.objects.filter(teacher=profile).order_by("-created_at")
    serializer = PendingRequestSerializer(requests, many=True)
    return success_response(serializer.data, message="Pending requests fetched successfully.")


@extend_schema(
    methods=["GET"],
    tags=["Admin Notification"],
    operation_id="admin_notification_count",
    responses={200: OpenApiResponse(description="Count of pending requests.")},
    description="Fetch the count of pending requests for the admin notification icon.",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_notification_count(request):
    if request.user.role != UserRole.ADMIN:
        return error_response("Only admins can access this endpoint.", status_code=status.HTTP_403_FORBIDDEN)

    count = PendingRequest.objects.filter(status=RequestStatus.PENDING).count()
    return success_response({"count": count}, message="Notification count fetched successfully.")


@extend_schema(
    tags=["Teachers Sessions"],
    operation_id="teachers_send_session_notice",
    request=SessionNoticeSerializer,
    responses={
        200: OpenApiResponse(description="Notice sent successfully."),
        400: OpenApiResponse(description="Validation error."),
        403: OpenApiResponse(description="Permission denied."),
        404: OpenApiResponse(description="Slot not found."),
    },
    description="Teacher sends a push notification to all students who have booked a specific slot.",
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def teacher_send_session_notice(request, slot_id):
    if request.user.role != UserRole.TEACHER:
        return error_response("Only teachers can send notices.", status_code=status.HTTP_403_FORBIDDEN)

    try:
        slot = TeacherSlot.objects.get(id=slot_id, teacher__user=request.user)
    except TeacherSlot.DoesNotExist:
        return error_response("Slot not found or you don't have access to it.", status_code=status.HTTP_404_NOT_FOUND)

    serializer = SessionNoticeSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response("Validation error", serializer.errors, status.HTTP_400_BAD_REQUEST)

    # Get all students who have booked this slot and have an expo_push_token
    bookings = slot.bookings.select_related("student").filter(student__expo_push_token__isnull=False).exclude(student__expo_push_token="")
    
    push_tokens = [booking.student.expo_push_token for booking in bookings]
    
    if not push_tokens:
        return success_response(message="No students with valid push tokens found for this session.")

    title = serializer.validated_data["title"]
    body = serializer.validated_data["body"]
    
    # Save notifications to database
    from students.models import StudentNotification
    notifications_to_create = []
    for booking in bookings:
        notifications_to_create.append(
            StudentNotification(
                student=booking.student,
                title=title,
                body=body
            )
        )
    if notifications_to_create:
        StudentNotification.objects.bulk_create(notifications_to_create)

    # Send push notifications
    result = send_expo_push_notification(
        push_tokens=push_tokens,
        title=title,
        body=body,
        data={"slot_id": slot_id, "screen": "session_details"}
    )

    return success_response(
        data={"expo_result": result},
        message=f"Notice sent and saved for {len(push_tokens)} students."
    )


@extend_schema(
    tags=["Teachers Dashboard"],
    operation_id="teachers_dashboard",
    responses={200: TeacherDashboardSerializer},
    description="Fetch teacher dashboard data: stats, curriculum, and upcoming sessions.",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def teacher_dashboard(request):
    if request.user.role != UserRole.TEACHER:
        return error_response("Only teachers can access the dashboard.", status_code=status.HTTP_403_FORBIDDEN)

    try:
        profile = TeacherProfile.objects.get(user=request.user)
    except TeacherProfile.DoesNotExist:
        return error_response("Teacher profile not found.", status_code=status.HTTP_404_NOT_FOUND)

    now = timezone.now()
    today = now.date()
    seven_days_ago = today - timedelta(days=7)

    # 1. Today's sessions count
    today_sessions_count = TeacherSlot.objects.filter(teacher=profile, date=today).count()

    # 2. Last 7 days sessions count
    week_sessions_count = TeacherSlot.objects.filter(
        teacher=profile, 
        date__gte=seven_days_ago, 
        date__lt=today
    ).count()

    # 3. Total students (unique students booked in their slots)
    total_students = StudentBooking.objects.filter(slot__teacher=profile).values("student").distinct().count()

    # 4. Curriculum list (Sessions with curriculum)
    # Showing slots that have a curriculum uploaded
    curriculum_slots = TeacherSlot.objects.filter(teacher=profile, curriculum__isnull=False).exclude(curriculum="").order_by("-date")

    # 5. Upcoming sessions
    upcoming_sessions = TeacherSlot.objects.filter(
        teacher=profile, 
        date__gte=today
    ).order_by("date", "start_time")[:5]

    payload = {
        "teacher_name": profile.name,
        "profile_picture": request.build_absolute_uri(profile.profile_picture.url) if profile.profile_picture else None,
        "stats": {
            "today": today_sessions_count,
            "week": week_sessions_count,
            "students": total_students,
        },
        "teacher_room": profile.whatsapp_link,
        "curriculum": TeacherBookedSlotSerializer(curriculum_slots, many=True, context={"request": request}).data,
        "upcoming_sessions": TeacherBookedSlotSerializer(upcoming_sessions, many=True, context={"request": request}).data,
    }

    return success_response(payload, message="Teacher dashboard data fetched successfully.")

from teachers.models import PendingRequest, RequestStatus

def pending_requests_count(request):
    if request.user.is_authenticated and request.user.is_staff:
        count = PendingRequest.objects.filter(status=RequestStatus.PENDING).count()
        return {'pending_requests_count': count}
    return {'pending_requests_count': 0}

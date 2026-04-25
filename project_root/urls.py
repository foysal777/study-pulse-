import mimetypes

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

# Force correct MIME types for audio files so browsers play instead of download
mimetypes.add_type("audio/mpeg", ".mpeg")
mimetypes.add_type("audio/mpeg", ".mp3")
mimetypes.add_type("audio/mp4", ".m4a")
mimetypes.add_type("audio/ogg", ".ogg")
mimetypes.add_type("audio/wav", ".wav")


urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/accounts/", include("accounts.urls")),
    path("api/students/", include("students.urls")),
    path("api/teachers/", include("teachers.urls")),
    path("api/support/", include("support.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

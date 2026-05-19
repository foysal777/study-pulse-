from django.db import models
from django.core.validators import FileExtensionValidator



class Policy(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Policies"

    def __str__(self):
        return self.title


class HelpSupport(models.Model):
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Help & Support"
        verbose_name_plural = "Help & Support"

    def __str__(self):
        return f"Support: {self.email}"


class PlayStoreQRCode(models.Model):
    pdf_file = models.FileField(
        upload_to='play_store_qr/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        help_text="Only PDF files are allowed."
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Play Store QR Code"
        verbose_name_plural = "Play Store QR Codes"

    def __str__(self):
        return f"QR Code PDF uploaded on {self.uploaded_at.strftime('%Y-%m-%d')}"


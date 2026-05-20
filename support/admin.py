from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.decorators import display
from support.models import Policy, HelpSupport, PlayStoreQRCode



@admin.register(Policy)
class PolicyAdmin(ModelAdmin):
    list_display = ("title", "updated_at")


@admin.register(HelpSupport)
class HelpSupportAdmin(ModelAdmin):
    list_display = ("email", "phone_number", "updated_at")


@admin.register(PlayStoreQRCode)
class PlayStoreQRCodeAdmin(ModelAdmin):
    list_display = ("id", "uploaded_at", "updated_at", "download_pdf")

    @display(description="Download")
    def download_pdf(self, obj):
        if not obj.pdf_file:
            return "-"

        return format_html(
            '<a href="{}" download style="display:inline-flex;align-items:center;justify-content:center;'
            'width:32px;height:32px;border:1px solid #e5e7eb;border-radius:10px;text-decoration:none;color:#2563eb;"'
            ' title="Download QR code PDF">'
            '<span class="material-symbols-outlined" style="font-size:18px;">download</span>'
            '</a>',
            obj.pdf_file.url,
        )

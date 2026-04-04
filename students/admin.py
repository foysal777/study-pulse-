from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.widgets import UnfoldAdminCheckboxSelectMultipleWidget

from students.models import InterestSummary, Intterest, RecommendedCourse


@admin.register(Intterest)
class IntterestAdmin(ModelAdmin):
    change_list_template = "admin/students/intterest/change_list.html"
    change_form_template = "admin/students/intterest/change_form.html"
    show_add_link = False
    list_display = ("id", "interest_name", "student", "created_at")
    search_fields = ("interest_name", "student__full_name", "student__email")


@admin.register(InterestSummary)
class InterestSummaryAdmin(ModelAdmin):
    show_add_link = False
    list_display = ("id", "interest_name", "student_count", "percentage", "updated_at")
    search_fields = ("interest_name",)
    readonly_fields = ("interest_name", "student_count", "percentage", "updated_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RecommendedCourse)
class RecommendedCourseAdmin(ModelAdmin):
    list_display = ("id", "teachers_list", "interest_type_list", "banner_preview", "created_at")
    list_filter = ("teachers", "interest_type")
    readonly_fields = ("banner_preview",)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "teachers":
            kwargs["widget"] = UnfoldAdminCheckboxSelectMultipleWidget()
            kwargs["queryset"] = db_field.remote_field.model.objects.order_by("name")
        if db_field.name == "interest_type":
            kwargs["widget"] = UnfoldAdminCheckboxSelectMultipleWidget()
            kwargs["queryset"] = Intterest.objects.order_by("interest_name", "id").distinct("interest_name")
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def teachers_list(self, obj):
        return obj.teachers_display or "-"

    teachers_list.short_description = "Teachers"

    def interest_type_list(self, obj):
        return obj.interest_type_display or "-"

    interest_type_list.short_description = "Interest Type"

    def banner_preview(self, obj):
        if not obj or not obj.banner:
            return "-"
        return format_html(
            '<img src="{}" alt="{}" style="height: 56px; width: 96px; object-fit: cover; border-radius: 8px;" />',
            obj.banner.url,
            obj.interest_type_display or "Recommended Course",
        )

    banner_preview.short_description = "Banner Preview"

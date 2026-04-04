from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.widgets import UnfoldAdminCheckboxSelectMultipleWidget

from teachers.models import Teacher, TeacherLevel


@admin.register(TeacherLevel)
class TeacherLevelAdmin(ModelAdmin):
    list_display = ("id", "name", "code")
    search_fields = ("name", "code")


@admin.register(Teacher)
class TeacherAdmin(ModelAdmin):
    change_list_template = "admin/teachers/teacher/change_list.html"
    change_form_template = "admin/teachers/teacher/change_form.html"
    show_add_link = False
    list_display = (
        "id",
        "name",
        "levels_list",
        "recommended_courses_list",
        "email",
        "created_at",
    )
    list_filter = ("levels",)
    search_fields = ("name", "email")

    def levels_list(self, obj):
        return obj.levels_display or "-"

    levels_list.short_description = "Levels"

    def recommended_courses_list(self, obj):
        return obj.recommended_courses_display or "-"

    recommended_courses_list.short_description = "Recommended Courses"

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "levels":
            kwargs["widget"] = UnfoldAdminCheckboxSelectMultipleWidget()
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("email",)
        return ()

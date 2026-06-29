from django import forms
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils import timezone
from html import escape
from unfold.admin import ModelAdmin

from students.models import (
    AssessmentLevelBand,
    AssessmentOption,
    AssessmentQuestion,
    AssessmentSection,
    AssessmentTemplate,
    InterestSummary,
    Intterest,
    RecommendedCourse,
    StudentAssessmentAnswer,
    StudentAssessmentAttempt,
    StudentProfile,
    StudentLocation,
    # AssessmentTemplateImporter,
)


class MultiCheckboxDropdownWidget(forms.CheckboxSelectMultiple):
    template_name = "students/widgets/multi_checkbox_dropdown.html"


class PlaceholderAdminMixin:
    placeholder_exclude_fields = ()

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change=change, **kwargs)

        for field_name, field in form.base_fields.items():
            if field_name in self.placeholder_exclude_fields:
                continue

            widget = field.widget
            if isinstance(
                widget,
                (
                    forms.CheckboxInput,
                    forms.CheckboxSelectMultiple,
                    forms.Select,
                    forms.SelectMultiple,
                    forms.RadioSelect,
                    forms.FileInput,
                    forms.ClearableFileInput,
                    forms.HiddenInput,
                ),
            ):
                continue

            if widget.attrs.get("placeholder"):
                continue

            label = (field.label or field_name.replace("_", " ")).strip()
            if isinstance(widget, forms.DateTimeInput):
                placeholder = "YYYY-MM-DD HH:MM"
            elif isinstance(widget, forms.DateInput):
                placeholder = "YYYY-MM-DD"
            elif isinstance(widget, forms.TimeInput):
                placeholder = "HH:MM"
            elif isinstance(widget, forms.NumberInput):
                placeholder = f"Enter {label.lower()}"
            else:
                placeholder = f"Enter {label.lower()}"

            widget.attrs["placeholder"] = placeholder

        return form


@admin.register(Intterest)
class IntterestAdmin(ModelAdmin):
    change_list_template = "admin/students/intterest/change_list.html"
    change_form_template = "admin/students/intterest/change_form.html"
    show_add_link = False
    list_display = ("id", "interest_name", "student", "created_at")
    search_fields = ("interest_name", "student__full_name", "student__email")


@admin.register(InterestSummary)
class InterestSummaryAdmin(PlaceholderAdminMixin, ModelAdmin):
    change_list_template = "admin/students/interestsummary/change_list.html"
    change_form_template = "admin/students/interestsummary/change_form.html"
    show_add_link = False
    list_display = ("id", "interest_name", "percentage", "updated_at", "actions_menu")
    search_fields = ("interest_name",)
    fields = ("interest_name",)

    def actions_menu(self, obj):
        edit_url = reverse("admin:students_interestsummary_change", args=[obj.pk])
        delete_url = reverse("admin:students_interestsummary_delete", args=[obj.pk])
        button_id = f"interest-summary-action-button-{obj.pk}"
        menu_id = f"interest-summary-action-menu-{obj.pk}"
        return format_html(
            """
            <button
                type="button"
                id="{}"
                onclick="window.studyPulseToggleInterestSummaryMenu && window.studyPulseToggleInterestSummaryMenu(event, '{}', '{}')"
                style="cursor:pointer;display:inline-flex;align-items:center;justify-content:center;
                    width:32px;height:32px;border:1px solid #e5e7eb;border-radius:10px;background:#fff;font-size:20px;">
                &#8942;
            </button>
            <div
                id="{}"
                style="display:none;position:fixed;z-index:9999;min-width:160px;background:#fff;border:1px solid #e5e7eb;
                    border-radius:12px;box-shadow:0 10px 25px rgba(0,0,0,.12);padding:8px;">
                <a href="{}" style="display:block;padding:8px 10px;border-radius:8px;text-decoration:none;color:#111827;">
                    Edit
                </a>
                <a href="{}" style="display:block;padding:8px 10px;border-radius:8px;text-decoration:none;color:#dc2626;"
                    onclick="return confirm('Are you sure you want to delete this interest?')">
                    Delete
                </a>
            </div>
            <script>
            (function() {{
                if (window.studyPulseInterestSummaryMenuBound) {{
                    return;
                }}
                window.studyPulseInterestSummaryMenuBound = true;
                window.studyPulseActiveInterestSummaryMenu = null;

                window.studyPulseCloseInterestSummaryMenu = function() {{
                    if (!window.studyPulseActiveInterestSummaryMenu) {{
                        return;
                    }}
                    window.studyPulseActiveInterestSummaryMenu.style.display = "none";
                    window.studyPulseActiveInterestSummaryMenu = null;
                }};

                window.studyPulseToggleInterestSummaryMenu = function(event, buttonId, menuId) {{
                    event.preventDefault();
                    event.stopPropagation();

                    const button = document.getElementById(buttonId);
                    const menu = document.getElementById(menuId);
                    if (!button || !menu) {{
                        return;
                    }}

                    const isOpen = menu.style.display === "block";
                    window.studyPulseCloseInterestSummaryMenu();
                    if (isOpen) {{
                        return;
                    }}

                    const rect = button.getBoundingClientRect();
                    menu.style.display = "block";
                    menu.style.top = (rect.bottom + 6) + "px";
                    menu.style.left = Math.max(8, rect.right - menu.offsetWidth) + "px";
                    window.studyPulseActiveInterestSummaryMenu = menu;
                }};

                document.addEventListener("click", function(event) {{
                    if (!window.studyPulseActiveInterestSummaryMenu) {{
                        return;
                    }}
                    if (window.studyPulseActiveInterestSummaryMenu.contains(event.target)) {{
                        return;
                    }}
                    window.studyPulseCloseInterestSummaryMenu();
                }});

                window.addEventListener("scroll", window.studyPulseCloseInterestSummaryMenu, true);
                window.addEventListener("resize", window.studyPulseCloseInterestSummaryMenu);
            }})();
            </script>
            """,
            button_id,
            button_id,
            menu_id,
            menu_id,
            edit_url,
            delete_url,
        )

    actions_menu.short_description = "Action"


@admin.register(RecommendedCourse)
class RecommendedCourseAdmin(PlaceholderAdminMixin, ModelAdmin):
    change_list_template = "admin/students/recommendedcourse/change_list.html"
    change_form_template = "admin/students/recommendedcourse/change_form.html"
    show_add_link = False
    list_display = (
        "id",
        "course_name",
        "banner_preview",
        "created_at",
        "actions_menu",
    )
    fields = ("course_name", "banner", "course_calender", "course_curriculum")
    # We remove readonly_fields here so it doesn't appear in the form, 
    # but the method still works for list_display

    def banner_preview(self, obj):
        if not obj or not obj.banner:
            return "-"
        return format_html(
            '<img src="{}" alt="{}" style="height: 56px; width: 96px; object-fit: cover; border-radius: 8px;" />',
            obj.banner.url,
            obj.course_name or "Recommended Course",
        )

    banner_preview.short_description = "Banner Preview"

    def response_add(self, request, obj, post_url_continue=None):
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(f"/admin/teachers/coursemodule/add/?banner={obj.pk}")

    def response_change(self, request, obj):
        if "_save" in request.POST:
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect(f"/admin/teachers/coursemodule/add/?banner={obj.pk}")
        return super().response_change(request, obj)

    def actions_menu(self, obj):
        edit_url = reverse("admin:students_recommendedcourse_change", args=[obj.pk])
        delete_url = reverse("admin:students_recommendedcourse_delete", args=[obj.pk])
        button_id = f"recommended-course-action-button-{obj.pk}"
        menu_id = f"recommended-course-action-menu-{obj.pk}"
        return format_html(
            """
            <button
                type="button"
                id="{}"
                onclick="window.studyPulseToggleRecommendedCourseMenu && window.studyPulseToggleRecommendedCourseMenu(event, '{}', '{}')"
                style="cursor:pointer;display:inline-flex;align-items:center;justify-content:center;
                    width:32px;height:32px;border:1px solid #e5e7eb;border-radius:10px;background:#fff;font-size:20px;">
                &#8942;
            </button>
            <div
                id="{}"
                style="display:none;position:fixed;z-index:9999;min-width:160px;background:#fff;border:1px solid #e5e7eb;
                    border-radius:12px;box-shadow:0 10px 25px rgba(0,0,0,.12);padding:8px;">
                <a href="{}" style="display:block;padding:8px 10px;border-radius:8px;text-decoration:none;color:#111827;">
                    Edit
                </a>
                <a href="{}" style="display:block;padding:8px 10px;border-radius:8px;text-decoration:none;color:#dc2626;"
                    onclick="return confirm('Are you sure you want to delete this course?')">
                    Delete
                </a>
            </div>
            <script>
            (function() {{
                if (window.studyPulseRecommendedCourseMenuBound) {{
                    return;
                }}
                window.studyPulseRecommendedCourseMenuBound = true;
                window.studyPulseActiveRecommendedCourseMenu = null;

                window.studyPulseCloseRecommendedCourseMenu = function() {{
                    if (!window.studyPulseActiveRecommendedCourseMenu) {{
                        return;
                    }}
                    window.studyPulseActiveRecommendedCourseMenu.style.display = "none";
                    window.studyPulseActiveRecommendedCourseMenu = null;
                }};

                window.studyPulseToggleRecommendedCourseMenu = function(event, buttonId, menuId) {{
                    event.preventDefault();
                    event.stopPropagation();

                    const button = document.getElementById(buttonId);
                    const menu = document.getElementById(menuId);
                    if (!button || !menu) {{
                        return;
                    }}

                    const isOpen = menu.style.display === "block";
                    window.studyPulseCloseRecommendedCourseMenu();
                    if (isOpen) {{
                        return;
                    }}

                    const rect = button.getBoundingClientRect();
                    menu.style.display = "block";
                    menu.style.top = (rect.bottom + 6) + "px";
                    menu.style.left = Math.max(8, rect.right - menu.offsetWidth) + "px";
                    window.studyPulseActiveRecommendedCourseMenu = menu;
                }};

                document.addEventListener("click", function(event) {{
                    if (!window.studyPulseActiveRecommendedCourseMenu) {{
                        return;
                    }}
                    if (window.studyPulseActiveRecommendedCourseMenu.contains(event.target)) {{
                        return;
                    }}
                    window.studyPulseCloseRecommendedCourseMenu();
                }});

                window.addEventListener("scroll", window.studyPulseCloseRecommendedCourseMenu, true);
                window.addEventListener("resize", window.studyPulseCloseRecommendedCourseMenu);
            }})();
            </script>
            """,
            button_id,
            button_id,
            menu_id,
            menu_id,
            edit_url,
            delete_url,
        )

    actions_menu.short_description = "Action"


@admin.register(StudentProfile)
class StudentProfileAdmin(PlaceholderAdminMixin, ModelAdmin):
    change_list_template = "admin/students/studentprofile/change_list.html"
    list_display = (
        "id",
        "student",
        "profile_picture_preview",
        "phone_number",
        "age",
        "gender",
        "last_achieved_degree",
        "parents_name",
        "parents_phone_number",
        "updated_at",
    )
    search_fields = ("student__full_name", "student__email", "phone_number", "parents_phone_number")
    list_filter = ("gender", "updated_at")
    list_select_related = ("student",)
    autocomplete_fields = ("student",)
    readonly_fields = ("profile_picture_preview", "created_at", "updated_at")
    fieldsets = (
        (
            "Student Account",
            {
                "fields": ("student",),
            },
        ),
        (
            "Basic Information",
            {
                "fields": (
                    "student_name",
                    "profile_picture",
                    "profile_picture_preview",
                    "phone_number",
                    "age",
                    "gender",
                    "last_achieved_degree",
                ),
            },
        ),
        (
            "Parent Information",
            {
                "fields": (
                    "parents_name",
                    "parents_phone_number",
                ),
            },
        ),
        (
            "Study Preferences",
            {
                "fields": (
                    "preferred_study_time",
                    "preferred_study_mode",
                    "preferred_study_language",
                ),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "export-excel/",
                self.admin_site.admin_view(self.export_excel_view),
                name="students_studentprofile_export_excel",
            ),
        ]
        return custom_urls + urls

    def export_excel_view(self, request):
        headers = [
            "Profile ID",
            "Student ID",
            "Student Name",
            "Account Full Name",
            "Email",
            "Phone Number",
            "Age",
            "Gender",
            "Last Achieved Degree",
            "Parents Name",
            "Parents Phone Number",
            "Preferred Study Time",
            "Preferred Study Mode",
            "Preferred Study Language",
            "Profile Picture URL",
            "Created At",
            "Updated At",
        ]

        queryset = self.get_queryset(request).order_by("-updated_at")
        rows = []
        for profile in queryset:
            values = [
                profile.id,
                profile.student_id,
                profile.student_name or "",
                profile.student.full_name if profile.student_id else "",
                profile.student.email if profile.student_id else "",
                profile.phone_number or "",
                profile.age if profile.age is not None else "",
                profile.gender or "",
                profile.last_achieved_degree or "",
                profile.parents_name or "",
                profile.parents_phone_number or "",
                self._format_export_value(profile.preferred_study_time),
                self._format_export_value(profile.preferred_study_mode),
                self._format_export_value(profile.preferred_study_language),
                request.build_absolute_uri(profile.profile_picture.url) if profile.profile_picture else "",
                self._format_datetime(profile.created_at),
                self._format_datetime(profile.updated_at),
            ]
            rows.append(
                "<tr>{}</tr>".format(
                    "".join(f"<td>{escape(str(value))}</td>" for value in values)
                )
            )
        header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
        table_html = (
            "<html><head><meta charset='utf-8'></head><body>"
            "<table border='1'>"
            f"<thead><tr>{header_html}</tr></thead>"
            f"<tbody>{''.join(rows)}</tbody>"
            "</table>"
            "</body></html>"
        )

        response = HttpResponse(
            table_html,
            content_type="application/vnd.ms-excel; charset=utf-8",
        )
        response["Content-Disposition"] = 'attachment; filename="student_profiles.xls"'
        return response

    def _format_export_value(self, value):
        if not value:
            return ""
        if isinstance(value, (list, tuple)):
            return ", ".join(str(item) for item in value)
        return str(value)

    def _format_datetime(self, value):
        if not value:
            return ""
        return timezone.localtime(value).strftime("%Y-%m-%d %I:%M %p")

    def profile_picture_preview(self, obj):
        if obj.profile_picture:
            return format_html(
                '<img src="{}" alt="Profile Picture" style="height:48px;width:48px;object-fit:cover;border-radius:50%;" />',
                obj.profile_picture.url,
            )
        return "-"

    profile_picture_preview.short_description = "Photo"


class AssessmentSectionInline(admin.TabularInline):
    model = AssessmentSection
    extra = 0
    fields = ("order", "title", "skill", "weight")


class AssessmentLevelBandInline(admin.TabularInline):
    model = AssessmentLevelBand
    extra = 0
    fields = ("order", "label", "min_score", "max_score")


@admin.register(AssessmentTemplate)
class AssessmentTemplateAdmin(PlaceholderAdminMixin, ModelAdmin):
    list_display = ("id", "name", "version", "pass_percentage", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    inlines = (AssessmentSectionInline, AssessmentLevelBandInline)
    list_per_page = 20


class AssessmentQuestionInline(admin.TabularInline):
    model = AssessmentQuestion
    extra = 0
    fields = ("order", "question_type", "marks", "is_active")

    def save_new(self, form, commit=True):
        obj = super().save_new(form, commit=False)
        self._apply_skill_question_type(obj)
        if commit:
            obj.save()
        return obj

    def save_existing(self, form, instance, commit=True):
        obj = super().save_existing(form, instance, commit=False)
        self._apply_skill_question_type(obj)
        if commit:
            obj.save()
        return obj

    @staticmethod
    def _apply_skill_question_type(obj):
        if obj.section_id:
            from students.models import AssessmentSection
            try:
                skill = AssessmentSection.objects.get(pk=obj.section_id).skill
                if skill == "reading":
                    obj.question_type = "passage"
                elif skill == "listening":
                    obj.question_type = "audio"
            except AssessmentSection.DoesNotExist:
                pass


@admin.register(AssessmentSection)
class AssessmentSectionAdmin(PlaceholderAdminMixin, ModelAdmin):
    list_display = ("id", "template", "title", "skill", "order", "weight")
    list_filter = ("skill", "template")
    search_fields = ("title", "template__name")
    inlines = (AssessmentQuestionInline,)
    list_per_page = 20


class AssessmentOptionInline(admin.TabularInline):
    model = AssessmentOption
    extra = 0
    fields = ("order", "text", "is_correct")


@admin.register(AssessmentQuestion)
class AssessmentQuestionAdmin(PlaceholderAdminMixin, ModelAdmin):
    list_display = ("id", "section", "order", "question_type", "marks", "is_active")
    list_filter = ("question_type", "is_active", "section__skill", "section__template")
    search_fields = ("prompt", "section__title", "section__template__name")
    inlines = (AssessmentOptionInline,)
    list_per_page = 20
    fieldsets = (
        (
            "Question",
            {
                "fields": (
                    "section",
                    "order",
                    "question_type",
                    "marks",
                    "is_active",
                ),
            },
        ),
        (
            "Content",
            {
                "fields": (
                    "prompt",
                    "prompt_i18n",
                    "audio_file",
                    "max_listens",
                    "transcript",
                ),
            },
        ),
    )

    @staticmethod
    def _skill_forces_type(skill):
        """Return the forced question_type for a skill, or None if free choice."""
        return {"reading": "passage", "listening": "audio"}.get(skill)

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj) or [])
        if obj and obj.section:
            if self._skill_forces_type(obj.section.skill):
                if "question_type" not in ro:
                    ro.append("question_type")
        return tuple(ro)

    def save_model(self, request, obj, form, change):
        if obj.section:
            forced = self._skill_forces_type(obj.section.skill)
            if forced:
                obj.question_type = forced
        super().save_model(request, obj, form, change)


@admin.register(AssessmentOption)
class AssessmentOptionAdmin(PlaceholderAdminMixin, ModelAdmin):
    list_display = ("id", "question", "order", "text", "is_correct")
    list_filter = ("is_correct", "question__question_type")
    search_fields = ("text", "question__prompt")


class StudentAssessmentAnswerInline(admin.TabularInline):
    model = StudentAssessmentAnswer
    extra = 0
    fields = (
        "question",
        "selected_option",
        "text_answer",
        "is_correct",
        "auto_score",
        "teacher_score",
        "listen_count",
    )
    readonly_fields = ("question", "selected_option", "text_answer", "auto_score")
    autocomplete_fields = ("question", "selected_option")
    show_change_link = True


@admin.register(StudentAssessmentAttempt)
class StudentAssessmentAttemptAdmin(PlaceholderAdminMixin, ModelAdmin):
    list_display = (
        "id",
        "student",
        "template",
        "status",
        "total_score",
        "is_passed",
        "reading_score",
        "listening_score",
        "writing_score",
        "grammar_score",
        "vocabulary_score",
        "started_at",
    )
    list_filter = ("status", "is_passed", "template", "started_at")
    search_fields = ("student__full_name", "student__email", "template__name")
    autocomplete_fields = ("student", "template")
    readonly_fields = ("started_at",)
    inlines = (StudentAssessmentAnswerInline,)
    list_per_page = 20


@admin.register(StudentAssessmentAnswer)
class StudentAssessmentAnswerAdmin(PlaceholderAdminMixin, ModelAdmin):
    list_display = (
        "id",
        "attempt",
        "question",
        "selected_option",
        "is_correct",
        "auto_score",
        "teacher_score",
        "listen_count",
        "evaluated_at",
    )
    list_filter = ("is_correct", "question__question_type", "question__section__skill")
    search_fields = ("attempt__student__full_name", "question__prompt")
    autocomplete_fields = ("attempt", "question", "selected_option")


@admin.register(AssessmentLevelBand)
class AssessmentLevelBandAdmin(PlaceholderAdminMixin, ModelAdmin):
    list_display = ("id", "template", "order", "label", "min_score", "max_score")
    list_filter = ("template",)
    search_fields = ("label", "template__name")
    autocomplete_fields = ("template",)


@admin.register(StudentLocation)
class StudentLocationAdmin(PlaceholderAdminMixin, ModelAdmin):
    list_display = ("id", "student", "latitude", "longitude", "updated_at")
    search_fields = ("student__full_name", "student__email")
    autocomplete_fields = ("student",)
    readonly_fields = ("updated_at",)


# @admin.register(AssessmentTemplateImporter)
# class AssessmentTemplateImporterAdmin(PlaceholderAdminMixin, ModelAdmin):
#     list_display = ("id", "gdoc_url", "created_at", "status_preview")
#     readonly_fields = ("status", "created_at")

#     def status_preview(self, obj):
#         if not obj.status:
#             return "-"
#         return obj.status[:50] + ("..." if len(obj.status) > 50 else "")

#     status_preview.short_description = "Status"

#     def save_model(self, request, obj, form, change):
#         from django.core.management import call_command
#         from io import StringIO
#         import traceback

#         is_new = obj.pk is None
#         super().save_model(request, obj, form, change)

#         out = StringIO()
#         try:
#             call_command("import_from_gdoc", obj.gdoc_url, stdout=out, stderr=out)
#             obj.status = out.getvalue()
#         except Exception as e:
#             obj.status = f"Error: {str(e)}\n\n{traceback.format_exc()}\n\n{out.getvalue()}"
#         obj.save(update_fields=["status"])

from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
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


# @admin.register(Intterest)
# class IntterestAdmin(ModelAdmin):
#     change_list_template = "admin/students/intterest/change_list.html"
#     change_form_template = "admin/students/intterest/change_form.html"
#     show_add_link = False
#     list_display = ("id", "interest_name", "student", "created_at")
#     search_fields = ("interest_name", "student__full_name", "student__email")


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
        "teachers_list",
        "interest_type_list",
        "seat_limit",
        "resource_link",
        "banner_preview",
        "created_at",
        "actions_menu",
    )
    list_filter = ("teachers", "interest_type")
    readonly_fields = ("banner_preview",)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "teachers":
            kwargs["widget"] = MultiCheckboxDropdownWidget(attrs={"empty_label": "Select teachers"})
            kwargs["queryset"] = db_field.remote_field.model.objects.order_by("name")
        if db_field.name == "interest_type":
            kwargs["widget"] = MultiCheckboxDropdownWidget(attrs={"empty_label": "Select interest type"})
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
            obj.course_name or "Recommended Course",
        )

    banner_preview.short_description = "Banner Preview"

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
    list_display = (
        "id",
        "student",
        "phone_number",
        "age",
        "gender",
        "updated_at",
    )
    search_fields = ("student__full_name", "student__email", "phone_number", "parents_phone_number")
    list_filter = ("gender", "updated_at")
    autocomplete_fields = ("student",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Student Information",
            {
                "fields": (
                    "student",
                    "phone_number",
                    "age",
                    "gender",
                    "last_achieved_degree",
                    "parents_name",
                    "parents_phone_number",
                ),
            },
        ),
        (
            "Preferences",
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


class AssessmentQuestionInline(admin.TabularInline):
    model = AssessmentQuestion
    extra = 0
    fields = ("order", "question_type", "difficulty", "marks", "is_active")


@admin.register(AssessmentSection)
class AssessmentSectionAdmin(PlaceholderAdminMixin, ModelAdmin):
    list_display = ("id", "template", "title", "skill", "order", "weight")
    list_filter = ("skill", "template")
    search_fields = ("title", "template__name")
    inlines = (AssessmentQuestionInline,)


class AssessmentOptionInline(admin.TabularInline):
    model = AssessmentOption
    extra = 0
    fields = ("order", "text", "is_correct")


@admin.register(AssessmentQuestion)
class AssessmentQuestionAdmin(PlaceholderAdminMixin, ModelAdmin):
    list_display = ("id", "section", "order", "question_type", "difficulty", "marks", "is_active")
    list_filter = ("question_type", "difficulty", "is_active", "section__skill", "section__template")
    search_fields = ("prompt", "section__title", "section__template__name")
    inlines = (AssessmentOptionInline,)
    readonly_fields = ()
    fieldsets = (
        (
            "Question",
            {
                "fields": (
                    "section",
                    "order",
                    "question_type",
                    "difficulty",
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

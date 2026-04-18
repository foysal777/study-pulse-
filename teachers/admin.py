from django import forms
from django.contrib import admin
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from unfold.admin import ModelAdmin

from teachers.models import (
    GeneralInfo, PendingRequest, SessionList, Teacher, TeacherLevel,
    TeacherProfile, TeachersLocation, TeacherAvailability,
    TeacherSlot, StudentBooking
)





class CapabilityLevelDropdownWidget(forms.CheckboxSelectMultiple):
    template_name = "teachers/widgets/capability_level_dropdown.html"


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
            else:
                placeholder = f"Enter {label.lower()}"

            widget.attrs["placeholder"] = placeholder

        return form


@admin.register(TeacherProfile)
class TeacherProfileAdmin(PlaceholderAdminMixin, ModelAdmin):
    list_display = ("id", "name", "phone_number", "age", "gender", "created_at")
    search_fields = ("name", "phone_number")
    list_filter = ("gender",)


# @admin.register(TeacherLevel)
# class TeacherLevelAdmin(ModelAdmin):
#     list_display = ("id", "name", "code")
#     search_fields = ("name", "code")


@admin.register(Teacher)
class TeacherAdmin(PlaceholderAdminMixin, ModelAdmin):
    change_list_template = "admin/teachers/teacher/change_list.html"
    change_form_template = "admin/teachers/teacher/change_form.html"
    show_add_link = False
    list_display = (
        "id",
        "name",
        "capability_level_list",
        "recommended_courses_list",
        "email",
        "created_at",
        "actions_menu",
    )
    list_filter = ("capability_level",)
    search_fields = ("name", "email")

    def capability_level_list(self, obj):
        return obj.capability_level_display or "-"

    capability_level_list.short_description = "Capability Level"

    def recommended_courses_list(self, obj):
        return obj.recommended_courses_display or "-"

    recommended_courses_list.short_description = "Recommended Courses"

    def actions_menu(self, obj):
        edit_url = reverse("admin:teachers_teacher_change", args=[obj.pk])
        delete_url = reverse("admin:teachers_teacher_delete", args=[obj.pk])
        button_id = f"teacher-action-button-{obj.pk}"
        menu_id = f"teacher-action-menu-{obj.pk}"
        return format_html(
            """
            <button
                type="button"
                id="{}"
                onclick="window.toggleTeacherMenu && window.toggleTeacherMenu(event, '{}', '{}')"
                class="teacher-action-button">
                &#8942;
            </button>
            <div
                id="{}"
                class="teacher-action-menu">
                <a href="{}" class="edit-action">
                    ✏️ Edit
                </a>
                <a href="{}" class="delete-action" onclick="return confirm('Are you sure?')">
                    🗑️ Delete
                </a>
            </div>
            """,
            button_id,
            button_id,
            menu_id,
            menu_id,
            edit_url,
            delete_url,
        )

    actions_menu.short_description = "Actions"

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "capability_level":
            kwargs["widget"] = CapabilityLevelDropdownWidget()
            kwargs["queryset"] = TeacherLevel.objects.order_by("name")
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("email",)
        return ()


@admin.register(SessionList)
class SessionListAdmin(PlaceholderAdminMixin, ModelAdmin):
    change_form_template = "admin/teachers/sessionlist/change_form.html"
    list_display = (
        "id",
        "teacher_name",
        "date_time",
        "number_of_students",
        "actions_menu",
    )
    list_filter = ("cancel", "teacher_name", "date_time")
    search_fields = ("teacher_name__name", "send_notification")
    autocomplete_fields = ("teacher_name",)
    fieldsets = (
        (
            None,
            {
                "fields": ("teacher_name", "date_time", "number_of_students"),
            },
        ),
        (
            "Action",
            {
                "fields": ("send_notification", "cancel"),
                "description": "Type the notification text and mark cancel if the session should be cancelled.",
            },
        ),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/send-notification/",
                self.admin_site.admin_view(self.send_notification_view),
                name="teachers_sessionlist_send_notification",
            ),
            path(
                "<path:object_id>/cancel-session/",
                self.admin_site.admin_view(self.cancel_session_view),
                name="teachers_sessionlist_cancel_session",
            ),
        ]
        return custom_urls + urls

    def send_notification_view(self, request, object_id):
        if request.method != "POST":
            return JsonResponse({"ok": False, "error": "Method not allowed."}, status=405)

        obj = self.get_object(request, object_id)
        if obj is None:
            return JsonResponse({"ok": False, "error": "Session not found."}, status=404)
        if not self.has_change_permission(request, obj):
            return JsonResponse({"ok": False, "error": "Permission denied."}, status=403)

        message = (request.POST.get("message") or "").strip()
        if not message:
            return JsonResponse({"ok": False, "error": "Notification message is required."}, status=400)

        obj.send_notification = message
        obj.save(update_fields=["send_notification", "updated_at"])
        return JsonResponse({"ok": True, "message": "Notification sent."})

    def cancel_session_view(self, request, object_id):
        if request.method != "POST":
            return JsonResponse({"ok": False, "error": "Method not allowed."}, status=405)

        obj = self.get_object(request, object_id)
        if obj is None:
            return JsonResponse({"ok": False, "error": "Session not found."}, status=404)
        if not self.has_delete_permission(request, obj):
            return JsonResponse({"ok": False, "error": "Permission denied."}, status=403)

        obj_display = str(obj)
        self.log_deletion(request, obj, obj_display)
        obj.delete()
        return JsonResponse({"ok": True, "message": f"{obj_display} deleted."})

    def notification_preview(self, obj):
        if not obj.send_notification:
            return "-"
        return obj.send_notification[:40] + ("..." if len(obj.send_notification) > 40 else "")

    notification_preview.short_description = "Send notification"

    def actions_menu(self, obj):
        notify_url = reverse("admin:teachers_sessionlist_send_notification", args=[obj.pk])
        cancel_url = reverse("admin:teachers_sessionlist_cancel_session", args=[obj.pk])
        button_id = f"session-action-button-{obj.pk}"
        menu_id = f"session-action-menu-{obj.pk}"
        return format_html(
            """
            <button
                type="button"
                id="{}"
                onclick="window.studyPulseToggleSessionMenu && window.studyPulseToggleSessionMenu(event, '{}', '{}')"
                style="cursor:pointer;display:inline-flex;align-items:center;justify-content:center;
                    width:32px;height:32px;border:1px solid #e5e7eb;border-radius:10px;background:#fff;font-size:20px;">
                &#8942;
            </button>
            <div
                id="{}"
                style="display:none;position:fixed;z-index:9999;min-width:190px;background:#fff;border:1px solid #e5e7eb;
                    border-radius:12px;box-shadow:0 10px 25px rgba(0,0,0,.12);padding:8px;">
                <button type="button"
                    onclick="window.studyPulseOpenNotificationPopup && window.studyPulseOpenNotificationPopup(event, '{}')"
                    style="display:block;width:100%;text-align:left;padding:8px 10px;border:0;border-radius:8px;background:transparent;cursor:pointer;color:#111827;">
                    Send notification
                </button>
                <button type="button"
                    onclick="window.studyPulseDeleteSession && window.studyPulseDeleteSession(event, '{}')"
                    style="display:block;width:100%;text-align:left;padding:8px 10px;border:0;border-radius:8px;background:transparent;cursor:pointer;color:#dc2626;">
                    Cancel
                </button>
            </div>
            <script>
            (function() {{
                if (window.studyPulseSessionMenuBound) {{
                    return;
                }}
                window.studyPulseSessionMenuBound = true;
                window.studyPulseActiveSessionMenu = null;
                window.studyPulseNotificationPopup = null;
                window.studyPulseNotificationInput = null;
                window.studyPulseNotificationSendButton = null;
                window.studyPulseNotificationTargetUrl = null;

                window.studyPulseCloseSessionMenu = function() {{
                    if (!window.studyPulseActiveSessionMenu) {{
                        return;
                    }}
                    window.studyPulseActiveSessionMenu.style.display = "none";
                    window.studyPulseActiveSessionMenu = null;
                }};

                function getCookie(name) {{
                    const value = `; ${{document.cookie}}`;
                    const parts = value.split(`; ${{name}}=`);
                    if (parts.length === 2) {{
                        return parts.pop().split(";").shift();
                    }}
                    return "";
                }}

                function ensureNotificationPopup() {{
                    if (window.studyPulseNotificationPopup) {{
                        return;
                    }}
                    const popup = document.createElement("div");
                    popup.style.display = "none";
                    popup.style.position = "fixed";
                    popup.style.inset = "0";
                    popup.style.zIndex = "10000";
                    popup.style.background = "rgba(17,24,39,0.35)";
                    popup.innerHTML = `
                        <div style="max-width:420px;margin:14vh auto 0;background:#fff;border-radius:12px;border:1px solid #e5e7eb;box-shadow:0 14px 40px rgba(0,0,0,.2);padding:16px;">
                            <p style="margin:0 0 10px;font-size:16px;font-weight:600;color:#111827;">Send notification</p>
                            <input type="text" id="study-pulse-notification-input"
                                style="width:100%;height:40px;padding:0 12px;border:1px solid #d1d5db;border-radius:10px;font-size:14px;outline:none;"
                                placeholder="Write notification message" />
                            <div style="margin-top:12px;display:flex;gap:8px;justify-content:flex-end;">
                                <button type="button" id="study-pulse-send-notification-btn"
                                    style="height:36px;padding:0 14px;border:0;border-radius:9px;background:#111827;color:#fff;cursor:pointer;">
                                    Send
                                </button>
                                <button type="button" id="study-pulse-close-notification-btn"
                                    style="height:36px;padding:0 14px;border:1px solid #d1d5db;border-radius:9px;background:#fff;color:#111827;cursor:pointer;">
                                    Cancel
                                </button>
                            </div>
                        </div>
                    `;
                    document.body.appendChild(popup);
                    window.studyPulseNotificationPopup = popup;
                    window.studyPulseNotificationInput = popup.querySelector("#study-pulse-notification-input");
                    window.studyPulseNotificationSendButton = popup.querySelector("#study-pulse-send-notification-btn");

                    popup.querySelector("#study-pulse-close-notification-btn").addEventListener("click", function() {{
                        popup.style.display = "none";
                        window.studyPulseNotificationTargetUrl = null;
                        window.studyPulseNotificationInput.value = "";
                    }});

                    popup.addEventListener("click", function(event) {{
                        if (event.target === popup) {{
                            popup.style.display = "none";
                            window.studyPulseNotificationTargetUrl = null;
                            window.studyPulseNotificationInput.value = "";
                        }}
                    }});

                    window.studyPulseNotificationSendButton.addEventListener("click", function() {{
                        const targetUrl = window.studyPulseNotificationTargetUrl;
                        const message = (window.studyPulseNotificationInput.value || "").trim();
                        if (!targetUrl) {{
                            return;
                        }}
                        if (!message) {{
                            alert("Please write a notification message.");
                            window.studyPulseNotificationInput.focus();
                            return;
                        }}

                        window.studyPulseNotificationSendButton.disabled = true;
                        fetch(targetUrl, {{
                            method: "POST",
                            headers: {{
                                "Content-Type": "application/x-www-form-urlencoded",
                                "X-CSRFToken": getCookie("csrftoken")
                            }},
                            body: `message=${{encodeURIComponent(message)}}`
                        }})
                            .then((response) => response.json())
                            .then((data) => {{
                                if (!data.ok) {{
                                    throw new Error(data.error || "Failed to send notification.");
                                }}
                                popup.style.display = "none";
                                window.studyPulseNotificationTargetUrl = null;
                                window.studyPulseNotificationInput.value = "";
                            }})
                            .catch((error) => {{
                                alert(error.message || "Failed to send notification.");
                            }})
                            .finally(() => {{
                                window.studyPulseNotificationSendButton.disabled = false;
                            }});
                    }});
                }}

                window.studyPulseOpenNotificationPopup = function(event, notifyUrl) {{
                    event.preventDefault();
                    event.stopPropagation();
                    ensureNotificationPopup();
                    window.studyPulseCloseSessionMenu();
                    window.studyPulseNotificationTargetUrl = notifyUrl;
                    window.studyPulseNotificationPopup.style.display = "block";
                    window.studyPulseNotificationInput.focus();
                }};

                window.studyPulseDeleteSession = function(event, deleteUrl) {{
                    event.preventDefault();
                    event.stopPropagation();
                    window.studyPulseCloseSessionMenu();
                    if (!confirm("Are you sure you want to delete this session?")) {{
                        return;
                    }}

                    fetch(deleteUrl, {{
                        method: "POST",
                        headers: {{
                            "X-CSRFToken": getCookie("csrftoken")
                        }}
                    }})
                        .then((response) => response.json())
                        .then((data) => {{
                            if (!data.ok) {{
                                throw new Error(data.error || "Delete failed.");
                            }}
                            window.location.reload();
                        }})
                        .catch((error) => {{
                            alert(error.message || "Delete failed.");
                        }});
                }};

                window.studyPulseToggleSessionMenu = function(event, buttonId, menuId) {{
                    event.preventDefault();
                    event.stopPropagation();

                    const button = document.getElementById(buttonId);
                    const menu = document.getElementById(menuId);
                    if (!button || !menu) {{
                        return;
                    }}

                    const isOpen = menu.style.display === "block";
                    window.studyPulseCloseSessionMenu();

                    if (isOpen) {{
                        return;
                    }}

                    const rect = button.getBoundingClientRect();
                    menu.style.display = "block";
                    menu.style.top = (rect.bottom + 6) + "px";
                    menu.style.left = Math.max(8, rect.right - menu.offsetWidth) + "px";
                    window.studyPulseActiveSessionMenu = menu;
                }};

                document.addEventListener("click", function(event) {{
                    if (!window.studyPulseActiveSessionMenu) {{
                        return;
                    }}
                    if (window.studyPulseActiveSessionMenu.contains(event.target)) {{
                        return;
                    }}
                    window.studyPulseCloseSessionMenu();
                }});

                window.addEventListener("scroll", window.studyPulseCloseSessionMenu, true);
                window.addEventListener("resize", window.studyPulseCloseSessionMenu);
            }})();
            </script>
            """,
            button_id,
            button_id,
            menu_id,
            menu_id,
            notify_url,
            cancel_url,
        )

    actions_menu.short_description = "Action"


class PendingRequestStatusFilter(admin.SimpleListFilter):
    title = "Status"
    parameter_name = "status"

    def lookups(self, request, model_admin):
        return (
            ("pending", "Pending"),
            ("accepted", "Accepted"),
            ("rejected", "Rejected"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "accepted":
            return queryset.filter(accept=True, cancel=False)
        if value == "rejected":
            return queryset.filter(cancel=True, accept=False)
        if value == "pending":
            return queryset.filter(accept=False, cancel=False)
        return queryset


@admin.register(PendingRequest)
class PendingRequestAdmin(PlaceholderAdminMixin, ModelAdmin):
    change_form_template = "admin/teachers/pendingrequest/change_form.html"
    list_display = (
        "id",
        "teacher_name",
        "withdraw_type",
        "session_availability",
        "status_badge",
        "actions_menu",
    )
    list_filter = (PendingRequestStatusFilter, "teacher_name")
    search_fields = ("teacher_name__name", "withdraw_type", "session_availability")
    autocomplete_fields = ("teacher_name",)
    readonly_fields = ("status_badge",)
    fieldsets = (
        (
            None,
            {
                "fields": ("teacher_name", "withdraw_type", "session_availability"),
            },
        ),
        (
            "Action",
            {
                "fields": ("status_badge", "accept", "cancel"),
            },
        ),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/set-status/<str:status>/",
                self.admin_site.admin_view(self.set_status_view),
                name="teachers_pendingrequest_set_status",
            ),
        ]
        return custom_urls + urls

    def set_status_view(self, request, object_id, status):
        if request.method != "POST":
            return JsonResponse({"ok": False, "error": "Method not allowed."}, status=405)

        obj = self.get_object(request, object_id)
        if obj is None:
            return JsonResponse({"ok": False, "error": "Request not found."}, status=404)
        if not self.has_change_permission(request, obj):
            return JsonResponse({"ok": False, "error": "Permission denied."}, status=403)

        if status == "accepted":
            obj.accept = True
            obj.cancel = False
            status_label = "Accepted"
        elif status == "rejected":
            obj.accept = False
            obj.cancel = True
            status_label = "Rejected"
        else:
            return JsonResponse({"ok": False, "error": "Invalid status."}, status=400)

        obj.save(update_fields=["accept", "cancel", "updated_at"])
        return JsonResponse({"ok": True, "status": status_label})

    def _status_text(self, obj):
        if obj.accept and not obj.cancel:
            return "Accepted"
        if obj.cancel and not obj.accept:
            return "Rejected"
        return "Pending"

    def status_badge(self, obj):
        status = self._status_text(obj)
        color_map = {
            "Pending": "#f59e0b",
            "Accepted": "#16a34a",
            "Rejected": "#dc2626",
        }
        color = color_map.get(status, "#6b7280")
        return format_html(
            '<span style="display:inline-flex;align-items:center;padding:3px 10px;border-radius:9999px;'
            'font-weight:600;font-size:12px;color:{};background:{}20;border:1px solid {}40;">{}</span>',
            color,
            color,
            color,
            status,
        )

    status_badge.short_description = "Status"

    def actions_menu(self, obj):
        accept_url = reverse("admin:teachers_pendingrequest_set_status", args=[obj.pk, "accepted"])
        cancel_url = reverse("admin:teachers_pendingrequest_set_status", args=[obj.pk, "rejected"])
        button_id = f"pending-request-action-button-{obj.pk}"
        menu_id = f"pending-request-action-menu-{obj.pk}"
        return format_html(
            """
            <button
                type="button"
                id="{}"
                onclick="window.studyPulseTogglePendingRequestMenu && window.studyPulseTogglePendingRequestMenu(event, '{}', '{}')"
                style="cursor:pointer;display:inline-flex;align-items:center;justify-content:center;
                    width:32px;height:32px;border:1px solid #e5e7eb;border-radius:10px;background:#fff;font-size:20px;">
                &#8942;
            </button>
            <div
                id="{}"
                style="display:none;position:fixed;z-index:9999;min-width:180px;background:#fff;border:1px solid #e5e7eb;
                    border-radius:12px;box-shadow:0 10px 25px rgba(0,0,0,.12);padding:8px;">
                <button type="button"
                    onclick="window.studyPulseSetPendingRequestStatus && window.studyPulseSetPendingRequestStatus(event, '{}', 'Accepted')"
                    style="display:block;width:100%;text-align:left;padding:8px 10px;border:0;border-radius:8px;background:transparent;cursor:pointer;color:#16a34a;">
                    Accept
                </button>
                <button type="button"
                    onclick="window.studyPulseSetPendingRequestStatus && window.studyPulseSetPendingRequestStatus(event, '{}', 'Rejected')"
                    style="display:block;width:100%;text-align:left;padding:8px 10px;border:0;border-radius:8px;background:transparent;cursor:pointer;color:#dc2626;">
                    Cancel
                </button>
            </div>
            <script>
            (function() {{
                if (window.studyPulsePendingRequestMenuBound) {{
                    return;
                }}
                window.studyPulsePendingRequestMenuBound = true;
                window.studyPulseActivePendingRequestMenu = null;

                window.studyPulseClosePendingRequestMenu = function() {{
                    if (!window.studyPulseActivePendingRequestMenu) {{
                        return;
                    }}
                    window.studyPulseActivePendingRequestMenu.style.display = "none";
                    window.studyPulseActivePendingRequestMenu = null;
                }};

                function getCookie(name) {{
                    const value = `; ${{document.cookie}}`;
                    const parts = value.split(`; ${{name}}=`);
                    if (parts.length === 2) {{
                        return parts.pop().split(";").shift();
                    }}
                    return "";
                }}

                window.studyPulseSetPendingRequestStatus = function(event, targetUrl, statusLabel) {{
                    event.preventDefault();
                    event.stopPropagation();
                    window.studyPulseClosePendingRequestMenu();

                    if (!confirm("Set status to " + statusLabel + "?")) {{
                        return;
                    }}

                    fetch(targetUrl, {{
                        method: "POST",
                        headers: {{
                            "X-CSRFToken": getCookie("csrftoken")
                        }}
                    }})
                        .then((response) => response.json())
                        .then((data) => {{
                            if (!data.ok) {{
                                throw new Error(data.error || "Failed to update status.");
                            }}
                            alert("Status updated to " + data.status + ".");
                            window.location.reload();
                        }})
                        .catch((error) => {{
                            alert(error.message || "Failed to update status.");
                        }});
                }};

                window.studyPulseTogglePendingRequestMenu = function(event, buttonId, menuId) {{
                    event.preventDefault();
                    event.stopPropagation();

                    const button = document.getElementById(buttonId);
                    const menu = document.getElementById(menuId);
                    if (!button || !menu) {{
                        return;
                    }}

                    const isOpen = menu.style.display === "block";
                    window.studyPulseClosePendingRequestMenu();

                    if (isOpen) {{
                        return;
                    }}

                    const rect = button.getBoundingClientRect();
                    menu.style.display = "block";
                    menu.style.top = (rect.bottom + 6) + "px";
                    menu.style.left = Math.max(8, rect.right - menu.offsetWidth) + "px";
                    window.studyPulseActivePendingRequestMenu = menu;
                }};

                document.addEventListener("click", function(event) {{
                    if (!window.studyPulseActivePendingRequestMenu) {{
                        return;
                    }}
                    if (window.studyPulseActivePendingRequestMenu.contains(event.target)) {{
                        return;
                    }}
                    window.studyPulseClosePendingRequestMenu();
                }});

                window.addEventListener("scroll", window.studyPulseClosePendingRequestMenu, true);
                window.addEventListener("resize", window.studyPulseClosePendingRequestMenu);
            }})();
            </script>
            """,
            button_id,
            button_id,
            menu_id,
            menu_id,
            accept_url,
            cancel_url,
        )

    actions_menu.short_description = "Action"


@admin.register(GeneralInfo)
class GeneralInfoAdmin(PlaceholderAdminMixin, ModelAdmin):
    change_form_template = "admin/teachers/generalinfo/change_form.html"
    show_add_link = False
    list_display = (
        "id",
        "file_name",
   
        "date",
        "time",
        "is_deleted",
    )
    list_filter = ("is_deleted", "date")
    search_fields = ("file_name",)
    readonly_fields = (
        "facebook_button",
        "youtube_button",
        "whatsapp_button",
        "library_button",
        "adult_learning_club_button",
        "kids_learning_club_button",
    )
    fieldsets = (
        (
            "File Information",
            {
                "fields": (
                    "file_name",
                    "date",
                    "time",
                    "file_upload",
                    "is_deleted",
                ),
            },
        ),
        (
            "Links",
            {
                "fields": (
                    ("facebook_link", "facebook_button"),
                    ("youtube_link", "youtube_button"),
                    ("whatsapp_link", "whatsapp_button"),
                    ("library_link", "library_button"),
                    ("adult_learning_club_link", "adult_learning_club_button"),
                    ("kids_learning_club_link", "kids_learning_club_button"),
                ),
            },
        ),
    )

    def changelist_view(self, request, extra_context=None):
        if request.GET.get("show_list") == "1":
            return super().changelist_view(request, extra_context)
        return HttpResponseRedirect(reverse("admin:teachers_generalinfo_add"))

    def add_view(self, request, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["general_info_list"] = self.get_queryset(request)
        return super().add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["general_info_list"] = self.get_queryset(request)
        return super().change_view(request, object_id, form_url, extra_context)

    def response_add(self, request, obj, post_url_continue=None):
        if "_continue" in request.POST or "_addanother" in request.POST:
            return super().response_add(request, obj, post_url_continue)
        return HttpResponseRedirect(reverse("admin:teachers_generalinfo_add"))

    def response_change(self, request, obj):
        if "_continue" in request.POST or "_addanother" in request.POST:
            return super().response_change(request, obj)
        return HttpResponseRedirect(reverse("admin:teachers_generalinfo_add"))

    def _link_button(self, url, label):
        if not url:
            return "-"
        icon = {
            "Facebook": mark_safe(
                '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" '
                'aria-hidden="true"><path d="M24 12.073C24 5.405 18.627 0 12 0S0 5.405 0 12.073c0 6.019 '
                '4.388 11.009 10.125 11.927v-8.437H7.078v-3.49h3.047V9.41c0-3.017 1.792-4.684 '
                '4.533-4.684 1.312 0 2.686.235 2.686.235v2.963h-1.514c-1.491 0-1.956.931-1.956 '
                '1.887v2.262h3.328l-.532 3.49h-2.796v8.437C19.612 23.082 24 18.092 24 '
                '12.073z"/></svg>'
            ),
            "YouTube": mark_safe(
                '<svg width="22" height="16" viewBox="0 0 24 24" fill="none" '
                'aria-hidden="true"><path d="M23.5 6.2a3 3 0 0 0-2.1-2.12C19.54 3.5 12 '
                '3.5 12 3.5s-7.54 0-9.4.58A3 3 0 0 0 .5 6.2 31.4 31.4 0 0 0 0 12a31.4 31.4 '
                '0 0 0 .5 5.8 3 3 0 0 0 2.1 2.12c1.86.58 9.4.58 9.4.58s7.54 0 9.4-.58a3 3 0 '
                '0 0 2.1-2.12A31.4 31.4 0 0 0 24 12a31.4 31.4 0 0 0-.5-5.8Z" fill="#FF0000"/>'
                '<path d="m9.75 15.52 6.27-3.52-6.27-3.52v7.04Z" fill="#fff"/></svg>'
            ),
            "WhatsApp": mark_safe(
                '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" '
                'aria-hidden="true"><path d="M20.52 3.48A11.88 11.88 0 0 0 12.06 0C5.5 0 '
                '.17 5.33.17 11.89c0 2.1.55 4.16 1.6 5.98L11 24l6.3-2.46a11.86 11.86 0 0 '
                '0 5.71-10.11c0-3.18-1.24-6.17-3.49-8.45Z" fill="#25D366"/><path d="M9.54 '
                '6.76c-.22-.5-.45-.51-.66-.52h-.56c-.2 0-.52.08-.8.39-.27.3-1.05 1.03-1.05 '
                '2.51s1.08 2.91 1.23 3.1c.15.2 2.1 3.36 5.2 4.57 2.57 1 3.1.8 3.66.75.56-.05 '
                '1.8-.73 2.05-1.44.25-.72.25-1.33.18-1.45-.08-.12-.28-.2-.58-.35-.3-.16-1.8-.93'
                '-2.08-1.04-.28-.1-.48-.15-.68.16-.2.3-.78 1.03-.95 1.24-.18.2-.35.23-.66.08-.3-'
                '.16-1.28-.5-2.43-1.6-.9-.86-1.5-1.92-1.68-2.24-.18-.3-.02-.47.13-.62.13-.12.3-.31'
                '.45-.46.15-.16.2-.27.3-.46.1-.2.05-.36-.03-.51-.07-.16-.67-1.72-.94-2.31Z" '
                'fill="#fff"/></svg>'
            ),
        }.get(label)

        button_label = icon or label
        return format_html(
            '<a href="{}" target="_blank" rel="noopener" '
            'style="display:inline-block;padding:8px 14px;border-radius:10px;'
            'background:#7c3aed;color:#fff;text-decoration:none;font-weight:600;'
            'line-height:1;display:inline-flex;align-items:center;justify-content:center;'
            'min-width:48px;gap:8px;">{}</a>',
            url,
            button_label,
        )

    def facebook_button(self, obj):
        return self._link_button(obj.facebook_link, "Facebook")

    facebook_button.short_description = "Facebook"

    def youtube_button(self, obj):
        return self._link_button(obj.youtube_link, "YouTube")

    youtube_button.short_description = "YouTube"

    def whatsapp_button(self, obj):
        return self._link_button(obj.whatsapp_link, "WhatsApp")

    whatsapp_button.short_description = "WhatsApp"

    def library_button(self, obj):
        return self._link_button(obj.library_link, "Library")

    library_button.short_description = "Library"

    def adult_learning_club_button(self, obj):
        return self._link_button(obj.adult_learning_club_link, "Adult Learning Club")

    adult_learning_club_button.short_description = "Adult learning club"

    def kids_learning_club_button(self, obj):
        return self._link_button(obj.kids_learning_club_link, "Kids Learning Club")

    kids_learning_club_button.short_description = "Kids learning club"

@admin.register(TeachersLocation)
class TeachersLocationAdmin(ModelAdmin):
    list_display = ("id", "teacher", "latitude", "longitude", "created_at")
    search_fields = ("teacher__name",)
    autocomplete_fields = ("teacher",)


@admin.register(TeacherAvailability)
class TeacherAvailabilityAdmin(ModelAdmin):
    list_display = ("id", "teacher", "day_of_week", "start_time", "end_time", "mode")
    list_filter = ("day_of_week", "mode", "teacher")
    search_fields = ("teacher__name",)
    autocomplete_fields = ("teacher",)


@admin.register(TeacherSlot)
class TeacherSlotAdmin(ModelAdmin):
    list_display = ("id", "teacher", "date", "start_time", "end_time", "mode", "booked_students", "max_students")
    list_filter = ("date", "mode", "teacher")
    search_fields = ("teacher__name", "date")
    autocomplete_fields = ("teacher",)


@admin.register(StudentBooking)
class StudentBookingAdmin(ModelAdmin):
    list_display = ("id", "student", "slot", "booked_at")
    list_filter = ("booked_at", "slot__date")
    search_fields = ("student__full_name", "slot__teacher__name")
    autocomplete_fields = ("slot",)

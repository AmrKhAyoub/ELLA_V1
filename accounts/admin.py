# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, FieldOfStudy


class CustomUserAdmin(UserAdmin):
    # Specify the fields to be displayed in the admin panel list view
    list_display = ("email", "username", "current_level", "target_level", "is_staff")

    # Specify the fields to be grouped in the user editing page
    fieldsets = UserAdmin.fieldsets + (
        (
            "Educational Profile",
            {"fields": ("current_level", "target_level", "learning_goal")},
        ),
        ("Personal Info", {"fields": ("avatar", "gender", "birth_date")}),
        ("Study Details", {"fields": ("study_level", "study_field")}),
    )


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(FieldOfStudy)

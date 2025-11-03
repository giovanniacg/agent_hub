from django.contrib import admin

from .models import TelegramUser


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = (
        "telegram_id",
        "username",
        "first_name",
        "last_name",
        "is_admin",
        "created_at",
        "updated_at",
    )
    search_fields = ("telegram_id", "username", "first_name", "last_name")
    list_filter = ("is_admin",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("telegram_id", "username", "first_name", "last_name")}),
        ("Permissions", {"fields": ("is_admin",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
    ordering = ("-created_at",)

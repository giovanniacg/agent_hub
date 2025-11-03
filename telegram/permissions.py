"""
Pega o header da requisção o id do telegram user e verifica permissões.
"""

from rest_framework import permissions
from .models import TelegramUser


class IsTelegramUser(permissions.BasePermission):
    """
    Permissão para verificar se o usuário é um TelegramUser.
    """

    def has_permission(self, request, view):
        telegram_id = request.headers.get("X-Telegram-User-ID")
        return (
            telegram_id is not None
            and TelegramUser.objects.filter(telegram_id=telegram_id).exists()
        )


class IsTelegramAdmin(permissions.BasePermission):
    """
    Permissão para verificar se o usuário é um admin do TelegramUser.
    """

    def has_permission(self, request, view):
        telegram_id = request.headers.get("X-Telegram-User-ID")
        if not telegram_id:
            return False
        try:
            user = TelegramUser.objects.get(telegram_id=telegram_id)
            return user.is_admin
        except TelegramUser.DoesNotExist:
            return False


class IsTelegramAdminIfProvided(permissions.BasePermission):
    """
    Permissão para verificar se o usuário é um admin do TelegramUser
    se o header X-Telegram-User-ID for fornecido.
    """

    def has_permission(self, request, view):
        telegram_id = request.headers.get("X-Telegram-User-ID")
        if not telegram_id:
            return True  # não fornecido, deixa passar
        try:
            user = TelegramUser.objects.get(telegram_id=telegram_id)
            return user.is_admin
        except TelegramUser.DoesNotExist:
            return False

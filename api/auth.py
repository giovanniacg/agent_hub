# auth.py
from django.conf import settings
from django.utils import timezone
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions

from .models import ApiKey


class APIKeyAuthentication(BaseAuthentication):
    """
    X-API-Key: <key_id>.<secret>
    """

    def authenticate(self, request):
        token = (
            request.headers.get("X-API-Key")
            or request.META.get("HTTP_X_API_KEY")  # fallback
        )
        if not token:
            return None  # deixa outras auths tentarem

        try:
            key_id, secret = token.split(".", 1)
        except Exception:
            raise exceptions.AuthenticationFailed("Invalid API key format")

        try:
            api_key = ApiKey.objects.select_related("user").get(
                key_id=key_id, is_active=True
            )
        except ApiKey.DoesNotExist:
            raise exceptions.AuthenticationFailed("API key not found")

        if api_key.is_expired or api_key.revoked_at:
            raise exceptions.AuthenticationFailed("API key expired or revoked")

        pepper = getattr(settings, "API_KEY_PEPPER", "")
        if not api_key.check_secret(secret, pepper):
            raise exceptions.AuthenticationFailed("Invalid API key")

        user = api_key.user
        if not user or not user.is_active:
            raise exceptions.AuthenticationFailed("User inactive or deleted")

        api_key.last_used_at = timezone.now()
        api_key.save(update_fields=["last_used_at"])

        request.api_key = api_key
        return (user, api_key)


class XApiKeyScheme(OpenApiAuthenticationExtension):
    # mesma import path da sua auth em REST_FRAMEWORK
    target_class = "api.auth.APIKeyAuthentication"
    name = "XApiKey"  # nome do esquema no OpenAPI

    def get_security_definition(self, auto_schema):
        # schema OpenAPI para API Key via header
        return {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",  # cabeçalho esperado
            # opcional: descrição
            "description": "Forneça sua chave no header X-API-Key",
        }

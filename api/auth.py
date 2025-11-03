# auth.py
from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework import exceptions

from .models import ApiKey 

class APIKeyAuthentication(BaseAuthentication):
    """
    Authorization: ApiKey <key_id>.<secret>
    """
    keyword = b"ApiKey"

    def authenticate(self, request):
        auth = get_authorization_header(request).split()
        if not auth or auth[0] != self.keyword or len(auth) != 2:
            return None

        try:
            key_id, secret = auth[1].decode().split(".", 1)
        except Exception:
            raise exceptions.AuthenticationFailed("Invalid API key format")

        try:
            api_key = (ApiKey.objects
                       .select_related("user")
                       .get(key_id=key_id, is_active=True))
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

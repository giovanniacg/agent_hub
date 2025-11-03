import hmac
import hashlib
import secrets
from django.conf import settings
from core.models import BaseModel
from django.db import models
from django.utils import timezone


class ApiKey(BaseModel):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="api_keys"
    )

    key_id = models.CharField(max_length=24, unique=True, db_index=True)  # prefixo
    key_hash = models.CharField(max_length=128, unique=True)  # sha256 hex

    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    last_used_at = models.DateTimeField(null=True, blank=True)

    revoked_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.key_id})"

    @property
    def is_expired(self):
        return bool(self.expires_at and timezone.now() > self.expires_at)

    @staticmethod
    def _hash_secret(raw_secret: str, pepper: str = "") -> str:
        return hashlib.sha256((pepper + raw_secret).encode()).hexdigest()

    def set_key_from_plain(self, plain_secret: str, pepper: str = ""):
        self.key_hash = self._hash_secret(plain_secret, pepper)

    def check_secret(self, plain_secret: str, pepper: str = "") -> bool:
        return hmac.compare_digest(
            self.key_hash, self._hash_secret(plain_secret, pepper)
        )

    @classmethod
    def generate_token(cls):
        key_id = secrets.token_urlsafe(9)  # curto, para lookup
        secret = secrets.token_urlsafe(32)  # segredo
        return key_id, f"{key_id}.{secret}"

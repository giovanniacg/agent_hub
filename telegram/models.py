from core.models import BaseModel
from django.db import models


class TelegramUser(BaseModel):
    telegram_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=150, blank=True, null=True)
    first_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name} (@{self.username})"

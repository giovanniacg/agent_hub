from django.contrib import admin, messages
from django.utils import timezone
from django.conf import settings

from .models import ApiKey

class ApiKeyAdmin(admin.ModelAdmin):
    list_display = (
        "name", "user", "key_id", "is_active",
        "expired_display", "last_used_at", "expires_at", "created_at",
    )
    readonly_fields = ("key_id", "created_at", "last_used_at", "revoked_at")
    search_fields = ("name", "key_id", "user__username", "user__email")
    list_filter = ("is_active",)
    fieldsets = (
        (None, {
            "fields": ("name", "user", "scopes")
        }),
        ("Status", {
            "fields": ("is_active", "expires_at", "revoked_at")
        }),
        ("Somente leitura", {
            "fields": ("key_id", "created_at", "last_used_at")
        }),
    )
    actions = ["revogar_chaves", "rotacionar_chave"]

    def expired_display(self, obj):
        return "Sim" if obj.is_expired else "Não"
    expired_display.short_description = "Expirada?"

    # --- CREATE: gera token na criação e mostra 1x ---
    def save_model(self, request, obj, form, change):
        pepper = getattr(settings, "API_KEY_PEPPER", "")
        generated_token = None

        if not change:
            # criação: gera novo <key_id>.<secret>
            key_id, token = ApiKey.generate_token()
            obj.key_id = key_id
            # salva só o hash do secret (parte após o ponto)
            secret = token.split(".", 1)[1]
            obj.set_key_from_plain(secret, pepper)
            super().save_model(request, obj, form, change)
            generated_token = token
        else:
            # edição normal: apenas salva campos comuns
            super().save_model(request, obj, form, change)

        if generated_token:
            self.message_user(
                request,
                (
                    "✅ <b>API Key criada!</b><br>"
                    "Copie e guarde com segurança (não será mostrada novamente):<br>"
                    f"<code>{generated_token}</code>"
                ),
                level=messages.SUCCESS,
                extra_tags="safe",
            )

    # --- ACTION: revogar (desativar) ---
    def revogar_chaves(self, request, queryset):
        updated = queryset.update(is_active=False, revoked_at=timezone.now())
        self.message_user(request, f"🔒 {updated} chave(s) revogadas.")
    revogar_chaves.short_description = "Revogar chaves selecionadas"

    # --- ACTION: rotacionar (gera novo token) para UMA por vez ---
    def rotacionar_chave(self, request, queryset):
        pepper = getattr(settings, "API_KEY_PEPPER", "")
        if queryset.count() != 1:
            self.message_user(
                request, "Selecione exatamente 1 chave para rotacionar.",
                level=messages.WARNING
            )
            return
        obj = queryset.first()
        key_id, token = ApiKey.generate_token()
        obj.key_id = key_id
        secret = token.split(".", 1)[1]
        obj.set_key_from_plain(secret, pepper)
        obj.revoked_at = None
        obj.is_active = True
        obj.save(update_fields=["key_id", "key_hash", "revoked_at", "is_active"])
        self.message_user(
            request,
            (
                "♻️ <b>Token rotacionado!</b><br>"
                "Copie e guarde com segurança (não será mostrado novamente):<br>"
                f"<code>{token}</code>"
            ),
            level=messages.SUCCESS,
            extra_tags="safe",
        )
    rotacionar_chave.short_description = "Rotacionar (gerar novo token) para a chave selecionada"

admin.site.register(ApiKey, ApiKeyAdmin)

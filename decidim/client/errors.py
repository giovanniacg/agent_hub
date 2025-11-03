class DecidimError(Exception):
    pass


class AuthRequired(DecidimError):
    """Sessão expirada ou não autenticada."""


class AuthFailed(DecidimError):
    """Falha ao autenticar (credenciais)."""


class RequestFailed(DecidimError):
    """Erro HTTP não recuperável (4xx/5xx)."""

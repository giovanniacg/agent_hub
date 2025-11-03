from typing import Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

DEFAULT_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
)


class DecidimAuthError(Exception): ...


class DecidimRequestError(Exception): ...


def build_session(
    base_url: str,
    timeout: float = 30.0,
    verify_ssl: bool = True,
    proxy: Optional[str] = None,
) -> requests.Session:
    s = requests.Session()
    s.verify = verify_ssl
    s.headers.update(
        {
            "User-Agent": DEFAULT_UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
            "Origin": base_url.rstrip("/"),
            "Referer": base_url.rstrip("/"),
        }
    )

    # Retry resiliente (GET/POST idempotentes do fluxo de login e form submit)
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "POST"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=20, pool_maxsize=50)
    s.mount("http://", adapter)
    s.mount("https://", adapter)

    # guardar timeout padrão “manual”
    s.request = _wrap_request_with_timeout(s.request, timeout)
    if proxy:
        s.proxies.update({"http": proxy, "https": proxy})
    return s


def _wrap_request_with_timeout(original_request, default_timeout: float):
    def wrapped(method, url, **kwargs):
        if "timeout" not in kwargs:
            kwargs["timeout"] = default_timeout
        return original_request(method, url, **kwargs)

    return wrapped


class DecidimClient:
    def __init__(
        self, base_url: str, session: Optional[requests.Session] = None, **opts
    ):
        self.base_url = base_url.rstrip("/")
        self.session = session or build_session(self.base_url, **opts)

    # ---------- helpers ----------
    @staticmethod
    def _extract_authenticity_token(html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        inp = soup.find("input", {"name": "authenticity_token"})
        if inp and inp.get("value"):
            return str(inp["value"])
        meta = soup.find("meta", {"name": "csrf-token"})
        if meta and meta.get("content"):
            return str(meta["content"])
        raise DecidimAuthError("authenticity_token não encontrado.")

    def _form_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

    # ---------- login ----------
    def login(self, email: str, password: str) -> None:
        sign_in = f"{self.base_url}/users/sign_in"

        r1 = self.session.get(sign_in)
        if r1.status_code != 200:
            raise DecidimAuthError(f"GET sign_in falhou: {r1.status_code}")
        token = self._extract_authenticity_token(r1.text)

        data = {
            "utf8": "✓",
            "authenticity_token": token,
            "user[email]": email,
            "user[password]": password,
            "user[remember_me]": "1",
        }
        r2 = self.session.post(sign_in, data=data, headers=self._form_headers())
        if r2.status_code >= 400:
            raise DecidimAuthError(f"POST sign_in falhou: {r2.status_code}")

        # Se continuar na tela de login com erro visível, considera falha
        if "users/sign_in" in r2.url and (
            "invalid" in r2.text.lower() or "erro" in r2.text.lower()
        ):
            raise DecidimAuthError("Credenciais inválidas ou bloqueio no login.")

    # ---------- padrão Rails: GET new -> POST create ----------
    def post_form(
        self, new_path: str, create_path: str, extra_form: Dict[str, Any]
    ) -> requests.Response:
        r_get = self.session.get(
            f"{self.base_url}{new_path}", headers={"Accept": "text/html"}
        )
        if r_get.status_code >= 400:
            raise DecidimRequestError(f"GET {new_path} falhou: {r_get.status_code}")

        token = self._extract_authenticity_token(r_get.text)

        form = {"utf8": "✓", "authenticity_token": token}
        form.update(extra_form)

        r_post = self.session.post(
            f"{self.base_url}{create_path}", data=form, headers=self._form_headers()
        )
        if r_post.status_code >= 400:
            raise DecidimRequestError(
                f"POST {create_path} falhou: {r_post.status_code}"
            )
        return r_post

    def close(self):
        self.session.close()


def test_authentication():
    from django.conf import settings

    client = DecidimClient(settings.DECIDIM_BASE_URL, verify_ssl=True)
    try:
        client.login(settings.DECIDIM_EMAIL, settings.DECIDIM_PASSWORD)
        print("Login bem-sucedido!")
    except DecidimAuthError as e:
        print(f"Erro de autenticação: {e}")
    return client


if __name__ == "__main__":
    import decidim.config_django  # noqa: F401

    test_authentication()

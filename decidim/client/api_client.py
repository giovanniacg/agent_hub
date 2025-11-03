import requests
import threading
import logging
from typing import Any, Dict
from urllib.parse import urljoin, urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from django.conf import settings

from .errors import AuthFailed, RequestFailed
from .session_store import load_cookies, save_cookies, clear_cookies
from .auth import devise_login

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux) Chrome/141 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
}


def build_session() -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.4,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "POST"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=20, pool_maxsize=50)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    s.headers.update(DEFAULT_HEADERS)
    return s


class ApiClient:
    """
    Um único ponto de I/O HTTP:
    - Reaproveita cookies via cache
    - Detecta sessão expirada
    - Auto-login com lock (evita tempestade de logins)
    - Reexecuta a requisição após reauth (1x)
    """

    def __init__(self):
        self.base_url = settings.DECIDIM_BASE_URL.rstrip("/")
        self.username = settings.DECIDIM_EMAIL
        self.password = settings.DECIDIM_PASSWORD
        self.session = build_session()
        self._login_lock = threading.Lock()
        # carrega cookies se existirem
        jar = load_cookies(self.base_url, self.username)
        if jar:
            self.session.cookies = jar

    # -------------- públicos --------------
    def get(self, path: str, **kwargs) -> requests.Response:
        logger.info(f"GET {path} {kwargs}")
        return self._request("GET", path, **kwargs)

    def post_form(self, path: str, data: Dict[str, Any], **kwargs) -> requests.Response:
        logger.info(f"POST {path} data={data} {kwargs}")
        headers = kwargs.pop("headers", {})
        headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
        return self._request("POST", path, data=data, headers=headers, **kwargs)

    # -------------- núcleo --------------
    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = urljoin(self.base_url + "/", path.lstrip("/"))
        resp = self.session.request(
            method, url, timeout=kwargs.pop("timeout", 30), **kwargs
        )

        if self._looks_logged_out(resp):
            # tenta reauth 1x
            with self._login_lock:
                self._login()  # pode levantar AuthFailed
                # reexecuta
                resp = self.session.request(
                    method, url, timeout=kwargs.pop("timeout", 30), **kwargs
                )

        if resp.status_code >= 400 and not self._looks_logged_out(resp):
            raise RequestFailed(f"{method} {path} -> {resp.status_code}")

        # salva cookies bons
        save_cookies(self.base_url, self.username, self.session.cookies)
        return resp

    def _login(self):
        try:
            devise_login(self.session, self.base_url, self.username, self.password)
            save_cookies(self.base_url, self.username, self.session.cookies)
        except AuthFailed:
            clear_cookies(self.base_url, self.username)
            raise

    @staticmethod
    def _looks_logged_out(resp: requests.Response) -> bool:
        u = resp.url.lower()
        if "/users/sign_in" in u:
            return True
        ct = resp.headers.get("content-type", "")
        if ct.startswith("text/html") and "users/sign_in" in resp.text.lower():
            return True
        # opcional: 401/403 genéricos do reverse proxy
        if resp.status_code in (401, 403) and "/admin/" in urlparse(resp.url).path:
            return True
        return False

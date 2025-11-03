from bs4 import BeautifulSoup
from .errors import AuthFailed
import requests


def extract_csrf(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    inp = soup.find("input", {"name": "authenticity_token"})
    if inp and inp.get("value"):
        return str(inp["value"])
    meta = soup.find("meta", {"name": "csrf-token"})
    if meta and meta.get("content"):
        return str(meta["content"])
    raise AuthFailed("authenticity_token não encontrado.")


def devise_login(session: requests.Session, base_url: str, email: str, password: str):
    url = f"{base_url.rstrip('/')}/users/sign_in"
    r1 = session.get(url, timeout=30)
    r1.raise_for_status()
    token = extract_csrf(r1.text)
    data = {
        "utf8": "✓",
        "authenticity_token": token,
        "user[email]": email,
        "user[password]": password,
        "user[remember_me]": "1",
    }
    r2 = session.post(
        url,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
        allow_redirects=True,
    )
    if r2.status_code >= 400 or "/users/sign_in" in r2.url.lower():
        raise AuthFailed("Falha no login (credenciais ou bloqueio).")

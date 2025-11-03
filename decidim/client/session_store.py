import json
from typing import Optional
from django.core.cache import cache
from requests.cookies import cookiejar_from_dict, RequestsCookieJar

_KEY = "decidim:cookies:{base}:{user}"


def load_cookies(base_url: str, username: str) -> Optional[RequestsCookieJar]:
    raw = cache.get(_KEY.format(base=base_url, user=username))
    if not raw:
        return None
    try:
        return cookiejar_from_dict(json.loads(raw))
    except Exception:
        return None


def save_cookies(
    base_url: str, username: str, jar: RequestsCookieJar, ttl: int = 6 * 3600
):
    data = {c.name: c.value for c in jar}
    cache.set(_KEY.format(base=base_url, user=username), json.dumps(data), timeout=ttl)


def clear_cookies(base_url: str, username: str):
    cache.delete(_KEY.format(base=base_url, user=username))

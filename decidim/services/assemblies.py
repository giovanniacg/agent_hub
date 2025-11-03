from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
from datetime import datetime

from ..client.api_client import ApiClient
from ..client.errors import RequestFailed


@dataclass
class AssemblyItem:
    title: str
    slug: str
    created_at: Optional[str]
    is_private: Optional[bool]
    is_published: Optional[bool]
    admin_edit_url: str
    public_url: Optional[str]
    admin_links: Dict[str, Optional[str]]


class AssembliesService:
    INDEX_PATH = "/admin/assemblies"

    def __init__(self, api: ApiClient):
        self.api = api
        self.base = api.base_url

    # ------------- façade estilo "frontend" -------------
    def list(self, page: int | None = None, sort: str | None = None, **filters) -> dict:
        params = {}
        if page:
            params["page"] = page
        if sort:
            params["q[s]"] = sort
        for k, v in filters.items():
            # permite passar q[...] já pronto ou “title_cont=...”
            if k.startswith("q["):
                params[k] = v
            else:
                params[f"q[{k}]"] = v
        params["utf8"] = "✓"

        resp = self.api.get(
            self.INDEX_PATH, params=params, headers={"Accept": "text/html"}
        )
        soup = BeautifulSoup(resp.text, "html.parser")

        table = soup.select_one("table.table-list")
        items = [] if not table else self._parse_rows(table)

        return {
            "items": [i.__dict__ for i in items],
            "pagination": self._parse_pagination(soup) or {"current_page": page or 1},
        }

    def search_title(
        self, term: str, page: int | None = None, sort: str | None = None
    ) -> dict:
        return self.list(page=page, sort=sort, **{"title_cont": term})

    # ------------- internals -------------
    def _parse_rows(self, table) -> List[AssemblyItem]:
        out: List[AssemblyItem] = []
        for tr in table.select("tbody > tr"):
            tds = tr.find_all("td")
            if len(tds) < 4:
                continue

            title_a = tds[0].find("a")
            title = (title_a.get_text(strip=True) if title_a else "") or ""
            admin_edit_url = (
                urljoin(self.base, title_a["href"])
                if title_a and title_a.has_attr("href")
                else ""
            )
            slug = self._slug_from_edit(admin_edit_url) or ""

            created_iso = self._ptbr_to_iso(tds[1].get_text(strip=True))

            priv_txt = tds[2].get_text(strip=True).lower()
            is_private = (
                False
                if "público" in priv_txt
                else True
                if "privado" in priv_txt
                else None
            )

            publ_txt = tds[3].get_text(strip=True).lower()
            is_published = (
                True
                if "publicado" in publ_txt and "não" not in publ_txt
                else False
                if "não publicado" in publ_txt
                else None
            )

            admin_links = self._extract_links(tds[4] if len(tds) > 4 else None)
            public_url = admin_links.get("preview")
            if public_url and not public_url.startswith(self.base):
                public_url = urljoin(self.base, public_url)

            out.append(
                AssemblyItem(
                    title=title,
                    slug=slug,
                    created_at=created_iso,
                    is_private=is_private,
                    is_published=is_published,
                    admin_edit_url=admin_edit_url,
                    public_url=public_url,
                    admin_links=admin_links,
                )
            )
        return out

    @staticmethod
    def _ptbr_to_iso(s: str) -> Optional[str]:
        s = s.replace("\xa0", " ").strip()
        for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y"):
            try:
                return datetime.strptime(s, fmt).isoformat(timespec="minutes")
            except ValueError:
                pass
        return None

    @staticmethod
    def _slug_from_edit(url: str) -> Optional[str]:
        path = urlparse(url).path
        parts = [p for p in path.split("/") if p]
        if (
            len(parts) >= 4
            and parts[0] == "admin"
            and parts[1] == "assemblies"
            and parts[-1] == "edit"
        ):
            return parts[2]
        return None

    def _extract_links(self, td) -> Dict[str, Optional[str]]:
        links: Dict[str, Optional[str]] = {
            "export": None,
            "copy": None,
            "edit": None,
            "instances": None,
            "preview": None,
        }
        if not td:
            return links
        for a in td.select("a[href]"):
            href = a["href"]
            title = (a.get("title") or "").lower()
            if "/export" in href or "exportar" in title:
                links["export"] = urljoin(self.base, href)
            elif "/copies/new" in href or "duplicar" in title:
                links["copy"] = urljoin(self.base, href)
            elif href.endswith("/edit") or "configurar" in title:
                links["edit"] = urljoin(self.base, href)
            elif (
                "parent_id_eq" in href or "instâncias" in title or "instancias" in title
            ):
                links["instances"] = urljoin(self.base, href)
            elif (
                href.startswith("/assemblies/")
                or "visualização" in title
                or "preview" in title
            ):
                links["preview"] = urljoin(self.base, href)
        return links

    def _parse_pagination(self, soup) -> Optional[Dict[str, Optional[int]]]:
        nav = soup.select_one("nav.pagination") or soup.select_one(".pagination")
        if not nav:
            return None

        def first_int(txt: str) -> Optional[int]:
            digits = "".join(ch for ch in txt if ch.isdigit())
            return int(digits) if digits else None

        current = None
        curr = nav.select_one(".current")
        if curr:
            current = first_int(curr.get_text(strip=True)) or current

        next_page = prev_page = total_pages = None
        for a in nav.select("a[href]"):
            qs = parse_qs(urlparse(a["href"]).query)
            p = int(qs["page"][0]) if "page" in qs and qs["page"] else None
            text = (a.get_text(strip=True) or "").lower()
            rel = [r.lower() for r in (a.get("rel") or [])]
            if "next" in rel or text in {"próximo", "próxima", "next", "»", ">"}:
                next_page = p
            elif "prev" in rel or text in {"anterior", "previous", "prev", "«", "<"}:
                prev_page = p
            if p is not None:
                total_pages = max(total_pages or 0, p)

        if current is None:
            current = (
                (prev_page + 1) if prev_page else (next_page - 1) if next_page else 1
            )
        if total_pages is None or total_pages < current:
            total_pages = current

        return {
            "current_page": current,
            "next_page": next_page,
            "prev_page": prev_page,
            "total_pages": total_pages,
        }

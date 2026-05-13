import os
import time
import urllib.parse
from dataclasses import dataclass
from typing import Optional
import requests
from dotenv import load_dotenv
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.tools import tool

load_dotenv()

TIMEOUT = 10
MAX_SYNOPSIS = 2000


@dataclass
class BookResult:
    source: str
    synopsis: str = ""
    tags: str = ""

    def __str__(self) -> str:
        parts = [f"SOURCE: {self.source}"]
        if self.synopsis:
            parts.append(f"Synopsis: {self.synopsis[:MAX_SYNOPSIS]}")
        if self.tags:
            parts.append(f"Tags: {self.tags}")
        return "\n".join(parts)

    @property
    def found(self) -> bool:
        return bool(self.synopsis or self.tags)


# Helpers


def _clean(text: str) -> str:
    return text.replace('"', "").strip()


def _truncate(text: str, limit: int = MAX_SYNOPSIS) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "…"


# =================================
# SEARCH ENGINES
# =================================

# Google Books


def _google_books(title: str, authors: str, exact: bool = True) -> Optional[BookResult]:
    """
    Consulta a API do Google Books para extrair sinopse e categorias.

    Depende da variável de ambiente 'GOOGLE_BOOKS_API_KEY'.

    Args:
        title: Título do livro.
        authors: Nome do(s) autor(es).
        exact: Se True, usa operadores restritos (intitle:/inauthor:). Se False, usa busca ampla.
    """

    api_key = os.getenv("GOOGLE_BOOKS_API_KEY")
    if not api_key:
        return None

    # Se for exato, usa intitle/inauthor. Se não, busca livre.

    query = f'intitle:"{title}" inauthor:"{authors}"' if exact else f"{title} {authors}"
    url = f"https://www.googleapis.com/books/v1/volumes?q={urllib.parse.quote(query)}&langRestrict=pt&key={api_key}"

    try:
        r = requests.get(url, timeout=TIMEOUT)
        if r.status_code == 200 and "items" in r.json():
            for item in r.json()["items"]:
                info = item.get("volumeInfo", {})
                synopsis = info.get("description", "").strip()
                if len(synopsis) > 20:
                    tags = ", ".join(info.get("categories", []))
                    return BookResult(
                        source=(
                            "Google Books (Exact)" if exact else "Google Books (Broad)"
                        ),
                        synopsis=synopsis,
                        tags=tags,
                    )
    except Exception:
        pass
    return None


# Open Library


def _open_library(title: str) -> Optional[BookResult]:
    """
    Consulta a API pública do Open Library (sem necessidade de autenticação).
    """

    url = (
        f"https://openlibrary.org/search.json?title={urllib.parse.quote(title)}&limit=3"
    )
    try:
        r = requests.get(url, timeout=TIMEOUT)
        if r.status_code == 200 and r.json().get("numFound", 0) > 0:
            for doc in r.json()["docs"]:
                subjects = ", ".join(doc.get("subject", [])[:10])
                if subjects:
                    return BookResult(source="Open Library", tags=subjects)
    except Exception:
        pass
    return None


# DDGS


def _duckduckgo_search(title: str, target: str) -> Optional[BookResult]:
    """
    Realiza web scraping indireto via resultados do DuckDuckGo.

    Possui um hard-sleep de 1.5s embutido para mitigar o Rate Limit nativo da biblioteca DDGS.

    Args:
        title: Título do livro a ser buscado.
        target: 'amazon' (restringe a site:amazon.com.br) ou 'general' (busca livre por sinopse).
    """

    time.sleep(1.5)  # DDGS Rate Limit
    ddg = DuckDuckGoSearchResults(num_results=2)

    query = (
        f'site:amazon.com.br "{title}" livro'
        if target == "amazon"
        else f'"{title}" livro sinopse'
    )

    try:
        res = ddg.invoke(query)
        if res and "snippet" in res.lower() and len(res) > 30:
            return BookResult(source=f"Web Scraping ({target.title()})", synopsis=res)
    except Exception:
        pass
    return None


def _find_book(title: str, authors: str) -> str:
    """
    Orquestra a busca de informações do livro através de uma esteira em cascata (Fallback Pipeline).

    Tenta recuperar os dados respeitando a seguinte ordem de prioridade:
    Google Exact -> Google Broad -> DDGS Amazon -> DDGS General -> Open Library.
    """

    clean_title = _clean(title)
    clean_authors = _clean(authors)

    pipeline = [
        ("Google Exact", lambda: _google_books(clean_title, clean_authors, exact=True)),
        (
            "Google Broad",
            lambda: _google_books(clean_title, clean_authors, exact=False),
        ),
        ("Amazon (DDGS)", lambda: _duckduckgo_search(clean_title, "amazon")),
        ("Web General", lambda: _duckduckgo_search(clean_title, "general")),
        ("Open Library", lambda: _open_library(clean_title)),
    ]

    for name, fn in pipeline:
        try:
            result = fn()
            if result and result.found:
                result.synopsis = _truncate(result.synopsis)
                return str(result)
        except Exception:
            pass
    return (
        f"SOURCE: NOT FOUND\nDetails: Nenhuma sinopse localizada para '{clean_title}'."
    )


@tool
def find_book(title: str, authors: str) -> str:
    """
    Busca informações detalhadas, sinopse e tags de um livro na internet usando múltiplos motores de busca.
    """
    return _find_book(title, authors)

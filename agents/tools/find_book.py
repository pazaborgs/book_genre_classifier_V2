import requests
import urllib.parse
import os
from dotenv import load_dotenv
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.tools import tool

load_dotenv()

# Base Function


def _find_book(title: str, authors: str, use_google: bool = True) -> str:
    """
    Método interno para buscar livros em cascata.
    Tenta PT-BR primeiro. Se falhar, expande para catálogos globais (Inglês).
    """
    clean_title = title.replace('"', "").strip()
    clean_authors = authors.replace('"', "").split(",")[0].strip()

    if use_google:
        api_key = os.getenv("GOOGLE_BOOKS_API_KEY")
        if api_key:

            def extract_best_synopsis(items):
                for item in items:
                    book = item.get("volumeInfo", {})
                    synopsis = book.get("description", "").strip()
                    if len(synopsis) > 20:
                        tags = ", ".join(book.get("categories", ["Sem categoria"]))
                        pages = book.get("pageCount", "N/A")
                        return f"FONTE: Google Books\nsynopsis: {synopsis}\ntags: {tags}\nPáginas: {pages}"
                return None

            query_str = f'intitle:"{clean_title}" inauthor:"{clean_authors}"'
            query = urllib.parse.quote(query_str)

            # Google Books - PT

            url_pt = f"https://www.googleapis.com/books/v1/volumes?q={query}&langRestrict=pt&key={api_key}"
            try:
                res_pt = requests.get(url_pt, timeout=10)
                if res_pt.status_code == 200 and "items" in res_pt.json():
                    best_result = extract_best_synopsis(res_pt.json()["items"])
                    if best_result:
                        return best_result
            except Exception as e:
                print(f"  [AVISO] Falha no Google Books (PT): {e}")

            # Google Books - Global

            print(f"  [INFO] Google Books (PT) sem sinopse. Tentando busca Global...")
            url_global = (
                f"https://www.googleapis.com/books/v1/volumes?q={query}&key={api_key}"
            )
            try:
                res_global = requests.get(url_global, timeout=10)
                if res_global.status_code == 200 and "items" in res_global.json():
                    data_global = res_global.json()
                    best_result = extract_best_synopsis(data_global["items"])
                    if best_result:
                        return best_result

                    # Fallback final do Google sem sinopse

                    book_fallback = data_global["items"][0].get("volumeInfo", {})
                    tags = ", ".join(book_fallback.get("categories", ["Sem categoria"]))
                    return f"FONTE: Google Books (Global)\nsynopsis: Sinopse ausente na API.\ntags: {tags}"
            except Exception as e:
                print(f"  [AVISO] Falha no Google Books (Global): {e}")

    print(f"  [AVISO] Acionando DuckDuckGo para '{clean_title}'...")
    ddg_search = DuckDuckGoSearchResults(num_results=3)

    # DDGS Skoob - PT

    query_skoob = f'site:skoob.com.br "{clean_title}" "{clean_authors}" sinopse'
    try:
        ddg_res = ddg_search.invoke(query_skoob)
        if ddg_res and "snippet" in ddg_res.lower() and len(ddg_res) > 30:
            return f"FONTE: DuckDuckGo (Skoob)\nResultados:\n{ddg_res}"
    except Exception:
        pass

    # DDGS Goodreads - Global

    print(f"  [INFO] Skoob falhou. Tentando Goodreads (Global)...")
    query_goodreads = (
        f'site:goodreads.com "{clean_title}" "{clean_authors}" book summary'
    )
    try:
        ddg_res = ddg_search.invoke(query_goodreads)
        if ddg_res and "snippet" in ddg_res.lower() and len(ddg_res) > 30:
            return f"FONTE: DuckDuckGo (Goodreads)\nResultados:\n{ddg_res}"
    except Exception:
        pass

    # DDGS - Busca Geral

    print(f"  [INFO] Catálogos falharam. Tentando busca ampla...")
    query_ampla = f'"{clean_title}" "{clean_authors}" book summary OR sinopse'
    try:
        ddg_res = ddg_search.invoke(query_ampla)
        if not ddg_res or "snippet" not in ddg_res.lower():
            return f"FONTE: DuckDuckGo\nResultados: Nenhuma sinopse ou resumo encontrado na web."
        return f"FONTE: DuckDuckGo (Geral)\nResultados:\n{ddg_res}"
    except Exception as e:
        return "FONTE: ERRO\nResultados: Falha ao buscar na web."


# Ferramenta (Tool) de busca
@tool
def find_book(title: str, authors: str) -> str:
    """
    Busca informações detalhadas, synopsis e tags de um livro.
    Esta ferramenta é a única que deve ser usada para pesquisar dados da obra.
    """
    return _find_book(title, authors, use_google=True)

from agents.tools.find_book import _find_book


def search_node(state: dict) -> dict:
    """
    Nó 1: Agente de Enriquecimento de Dados.
    Busca metadados externos (sinopse e tags) para subsidiar a classificação.
    """

    title = state.get("title", "Título Desconhecido")
    authors = state.get("authors", "Autor Desconhecido")

    print(f"\n  [*] Iniciando busca externa: '{title}'")

    try:
        # Chamada da ferramenta de busca
        res = _find_book(title=title, authors=authors)

        # Identificação da origem para o log
        source = "Google Books" if "source: Google Books" in res else "DuckDuckGo"

        print(f"  └─ [SUCESSO] Contexto recuperado via {source}.")

        return {"searched_synopsis": res, "search_source": source}

    except Exception as e:
        print(f"  [!] Falha na recuperação de dados:")
        print(f"      Detalhes: {e}\n")

        return {
            "searched_synopsis": "Falha ao buscar sinopse na internet.",
            "search_source": "ERRO",
        }

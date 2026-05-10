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
        res = _find_book(title=title, authors=authors)

        source_line = [line for line in res.split("\n") if line.startswith("SOURCE:")]
        exact_source = (
            source_line[0].replace("SOURCE: ", "").strip()
            if source_line
            else "Desconhecida"
        )

        state_source = "DuckDuckGo" if "Web Scraping" in exact_source else exact_source

        if exact_source == "NOT FOUND":
            print("  └─ [AVISO] Nenhum contexto encontrado nas fontes disponíveis.")
        else:
            print(f"  └─ [SUCESSO] Contexto recuperado via {exact_source}.")

        return {"searched_synopsis": res, "search_source": state_source}

    except Exception as e:
        print(f"  [!] Falha na recuperação de dados:")
        print(f"      Detalhes: {e}\n")

        return {
            "searched_synopsis": "Falha ao buscar sinopse na internet.",
            "search_source": "ERRO",
        }

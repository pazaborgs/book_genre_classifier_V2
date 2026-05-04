from langgraph.graph import StateGraph, START, END
from agents.state import CollectionState
from agents.nodes.search import search_node
from agents.nodes.classifier import classifier_agent
from agents.nodes.save import save_node


def retry_failed_attempt(state: dict) -> str:
    """
    Roteador Condicional: Decide se o fluxo retrocede para nova busca
    ou avança para persistência na camada Gold.
    """
    color = state.get("color_suggestion", "")
    tries = state.get("retry_count", 0)
    source = state.get("search_source", "")
    LIMIT_TRIES = 3

    problem = color in ["ERRO", "BRANCO"]

    if problem and tries < LIMIT_TRIES and source == "DuckDuckGo":
        print(f"\n  [!] Roteador: Falha detectada (Origem: {source})")
        print(f"      Iniciando tentativa {tries + 1}/{LIMIT_TRIES}...")
        return "try_again"

    return "move_on"


def build_graph():
    print("\n  [*] Orquestrador: Montando arquitetura de grafos...")

    workflow = StateGraph(CollectionState)

    # Nodes
    workflow.add_node("pesquisador", search_node)
    workflow.add_node("classificador", classifier_agent)
    workflow.add_node("armazenamento", save_node)

    # Edges
    workflow.add_edge(START, "pesquisador")
    workflow.add_edge("pesquisador", "classificador")

    workflow.add_conditional_edges(
        "classificador",
        retry_failed_attempt,
        {"try_again": "pesquisador", "move_on": "armazenamento"},
    )

    workflow.add_edge("armazenamento", END)

    app = workflow.compile()

    print("  └─ [SUCESSO] Esteira compilada e pronta para execução.")
    return app

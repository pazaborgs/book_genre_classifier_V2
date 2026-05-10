from langgraph.graph import StateGraph, START, END
from agents.state import CollectionState
from agents.nodes.search import search_node
from agents.nodes.classifier import classifier_agent
from agents.nodes.save import save_node
from rich.console import Console
from rich.tree import Tree
from rich.panel import Panel

console = Console()


def retry_failed_attempt(state: dict) -> str:
    """
    Roteador Condicional: Decide se o fluxo retrocede para nova busca
    ou avança para persistência na camada Gold.
    """
    color = state.get("color_suggestion", "")
    tries = state.get("retry_count", 0)
    source = state.get("search_source", "")
    LIMIT_TRIES = 2

    problem = color in ["ERRO", "BRANCO"]

    if problem and tries < LIMIT_TRIES and source == "DuckDuckGo":
        console.print(
            f"      [bold yellow]↻ Roteador:[/bold yellow] Falha na classificação (Origem: [dim]{source}[/dim])."
        )
        console.print(
            f"      [bold yellow]↳[/bold yellow] Iniciando tentativa [cyan]{tries + 1}/{LIMIT_TRIES}[/cyan] para refinar a busca da obra..."
        )
        return "try_again"

    return "move_on"


def build_graph():
    console.print(
        "\n  [bold cyan][*][/bold cyan] [dim]Orquestrador: Montando arquitetura de grafos...[/dim]"
    )

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

    # Visualização em Árvore do Grafo usando Rich
    tree = Tree("[bold cyan]Fluxo do Agente de Classificação[/bold cyan]")
    tree.add("[green]START[/green]")
    node_pesq = tree.add("[blue]Pesquisador[/blue] (Busca Metadados)")
    node_class = node_pesq.add("[magenta]Classificador[/magenta] (LLM)")

    router = node_class.add(
        "🔀 [yellow]Roteador Condicional[/yellow] (Analisa 'color_suggestion')"
    )
    router.add("[dim]Se Falha < 2:[/dim] Retorna ao [blue]Pesquisador[/blue]")

    node_armaz = router.add(
        "[dim]Se Sucesso ou Limite:[/dim] [blue]Armazenamento[/blue] (Persiste na Camada Gold)"
    )
    node_armaz.add("[red]END[/red]")

    console.print(
        Panel(
            tree,
            title="[bold green]✔ Esteira compilada com sucesso[/bold green]",
            border_style="green",
            expand=False,
            padding=(1, 2),
        )
    )

    return app

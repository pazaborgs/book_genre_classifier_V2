from langgraph.graph import StateGraph, START, END
from agents.state import CollectionState
from agents.nodes.search import search_node
from agents.nodes.classifier import classifier_agent
from agents.nodes.save import save_node
from rich.console import Console
from rich.tree import Tree
from rich.panel import Panel
import time

console = Console()


def retry_failed_attempt(state: dict) -> str:
    """
    Coordena o sistema de novas tentativas.

    Retornos possíveis:
        try_again: Se for "BRANCO" e tries < LIMIT_TRIES, tenta novamente
        move_on: Se for ERRO ou outra cor, prossegue o fluxo.
    """

    color = state.get("color_suggestion", "")
    tries = state.get("retry_count", 0)
    source = state.get("search_source", "")

    LIMIT_TRIES = 1

    if color == "BRANCO" and tries < LIMIT_TRIES:
        console.print(
            f"      [bold yellow]↻ Roteador:[/bold yellow] BRANCO recebido "
            f"(Origem: [dim]{source}[/dim])."
        )
        console.print(
            f"      [bold yellow]↳[/bold yellow] Tentativa "
            f"[cyan]{tries + 1}/{LIMIT_TRIES}[/cyan] — aguardando 15s antes de rebuscar..."
        )
        return "try_again"

    if color == "ERRO":
        console.print(
            f"      [bold red]↻ Roteador:[/bold red] ERRO técnico — persistindo sem retry."
        )

    return "move_on"


def build_graph():
    """
    Monta o workflow agêntico.
    """

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

    # Árvore Rich

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

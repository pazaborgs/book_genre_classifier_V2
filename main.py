import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)
from rich.table import Table
from src.pipeline import run_pipeline
from agents.graph import build_graph
from src.bronze import load_config
from src.to_xlsx import export_to_xlsx
from reset_errors import reset_errors

console = Console()

_COLOR_STYLE = {
    "BRANCO": "white",
    "VERDE": "green",
    "VERMELHO": "red",
    "AZUL": "blue",
    "AMARELO": "yellow",
    "OURO": "yellow",
    "PRATA": "white",
    "PRETO": "bright_black",
    "LARANJA": "orange3",
    "DIDÁTICO": "cyan",
    "ERRO": "bold red",
}


def _color_label(color: str) -> str:
    style = _COLOR_STYLE.get(color, "white")
    return f"[{style}]{color}[/{style}]"


def main(limit: int = 30):
    console.print(
        Panel.fit(
            "[bold blue]Orquestração do Pipeline — Classificação de Livros Agêntica[/bold blue]",
            border_style="blue",
        )
    )

    with console.status(
        "[bold blue]Sincronizando arquitetura Medallion...[/bold blue]", spinner="dots"
    ):
        run_pipeline()
    console.print("[green]✔[/green] [dim]Medallion sincronizada.[/dim]")

    with console.status(
        "[bold blue]Limpando erros da base Gold...[/bold blue]", spinner="dots"
    ):
        reset_errors()
    console.print("[green]✔[/green] [dim]Base Gold estabilizada.[/dim]\n")

    config = load_config()
    df_gold = pd.read_parquet(config["data_paths"]["gold"])
    df_pending = df_gold[
        (df_gold["save_status"] == "pending") & (df_gold["true_color"] == "pending")
    ]

    if df_pending.empty:
        console.print("[bold yellow]Nenhum registro pendente.[/bold yellow]")
        _finish()
        return

    df_batch = df_pending.head(limit)
    console.print(f"[*] [bold]{len(df_pending)}[/bold] pendências totais.")
    console.print(
        f" └─ Processando lote de [bold cyan]{len(df_batch)}[/bold cyan] registros...\n"
    )

    app = build_graph()
    batch_results = []
    error_count = 0
    MAX_ERRORS = 2

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Iniciando...", total=len(df_batch))

        for index, row in df_batch.iterrows():
            title = str(row["titulo"])
            tombo = str(row["tombo"])

            progress.update(task, description=f"[cyan]Avaliando: [white]{title[:35]}")

            book_state = {
                "tombo": tombo,
                "title": title,
                "authors": str(row["autores"]),
                "retry_count": 0,
            }

            try:
                final_state = app.invoke(book_state)
                color = final_state.get("color_suggestion", "N/A")

                # Acumula erros consecutivos
                if color == "ERRO":
                    error_count += 1
                else:
                    error_count = 0  # reseta em qualquer sucesso (inclusive BRANCO)

                batch_results.append(
                    (tombo, title, "[green]✔ Classificado[/green]", color)
                )

                if error_count >= MAX_ERRORS:
                    console.print(
                        f"\n[bold red]{MAX_ERRORS} erros consecutivos — possível falha sistêmica. Abortando lote.[/bold red]"
                    )
                    break

            except Exception as e:
                console.print(
                    f"\n[bold red][!] Exceção não tratada no tombo {tombo}:[/bold red] {e}"
                )
                batch_results.append(
                    (tombo, title, "[bold red]Exceção[/bold red]", "---")
                )
                error_count += 1

                if error_count >= MAX_ERRORS:
                    break

            progress.advance(task)

    # Resultados
    console.print()
    table = Table(title="Resumo do Lote", border_style="blue", header_style="bold cyan")
    table.add_column("Tombo", justify="right", style="cyan", no_wrap=True)
    table.add_column("Título", style="white")
    table.add_column("Status", justify="center")
    table.add_column("Cor", justify="center")

    for tombo, title, status, color in batch_results:
        table.add_row(tombo, title, status, _color_label(color))

    console.print(table)
    _finish()


def _finish():
    console.print("\n[dim]" + "─" * 60 + "[/dim]")
    with console.status(
        "[bold green]Exportando Gold → XLSX...[/bold green]", spinner="bouncingBar"
    ):
        export_to_xlsx()
    console.print(
        Panel.fit("[bold green]PIPELINE FINALIZADO[/bold green]", border_style="green")
    )


if __name__ == "__main__":
    main(limit=10)

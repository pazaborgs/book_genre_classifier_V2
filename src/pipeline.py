import time
from rich.console import Console
from rich.panel import Panel

from src.ingest_sheet import download_spreadsheet
from src.bronze import ingest_bronze
from src.silver import process_silver
from src.gold import process_gold

console = Console()


def run_pipeline(update_sheet=False):

    steps = [
        {"name": "Camada Bronze", "func": ingest_bronze},
        {"name": "Camada Silver", "func": process_silver},
        {"name": "Camada Gold", "func": process_gold},
    ]

    if update_sheet:
        steps.insert(
            0,
            {
                "name": "Baixando Tombo do Drive",
                "func": download_spreadsheet,
            },
        )

    with console.status(
        "[bold cyan]Iniciando orquestração...[/bold cyan]", spinner="point"
    ) as status:
        for i, step in enumerate(steps, 1):
            status.update(
                f"[bold blue]● Etapa {i}/{len(steps)}: Processando {step['name']}...[/bold blue]"
            )

            try:
                step["func"]()
                time.sleep(0.4)

            except Exception as e:
                console.print(
                    f"\n[bold red][ERRO CRÍTICO] Falha na etapa: {step['name']}[/bold red]"
                )
                console.print(f"[red]Detalhes: {e}[/red]")
                return

    console.print("\n[dim]" + "─" * 40 + "[/dim]")
    console.print(
        "[bold green]✔ Pipeline de Dados concluído com sucesso![/bold green]\n"
    )


if __name__ == "__main__":
    run_pipeline(update_sheet=True)

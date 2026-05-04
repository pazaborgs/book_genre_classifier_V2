import time
from tqdm import tqdm
from rich.console import Console
from rich.panel import Panel
from src.ingest_sheet import download_spreadsheet
from src.bronze import ingest_bronze
from src.silver import process_silver
from src.gold import process_gold

console = Console()


def run_pipeline(update_sheet=False):

    # Cabeçalho
    console.print(
        Panel.fit(
            "[bold blue]Book Genre Classifier - Data Pipeline[/bold blue]",
            border_style="blue",
        )
    )
    console.print("[dim]" + "─" * 40 + "[/dim]")

    steps = [
        {"name": "Camada Bronze", "func": ingest_bronze},
        {"name": "Camada Silver", "func": process_silver},
        {"name": "Camada Gold  ", "func": process_gold},
    ]

    if update_sheet:
        steps.insert(
            0,
            {
                "name": "Baixando Tombo do Drive",
                "func": download_spreadsheet,
            },
        )

    with tqdm(
        total=len(steps),
        desc="Progresso",
        bar_format="{l_bar}{bar:15}{r_bar}",
        colour="blue",
    ) as pbar:
        for step in steps:
            pbar.write(f"\n● Processando {step['name']}...\n")

            try:
                step["func"]()
                time.sleep(0.3)
                pbar.update(1)
            except Exception as e:
                pbar.write(f"\n[ERRO CRÍTICO] Falha na etapa: {step['name']}")
                pbar.write(f"Detalhes: {e}")
                return

    console.print("\n[dim]" + "─" * 40 + "[/dim]")
    console.print("[bold green]Pipeline concluído com sucesso![/bold green]\n")


if __name__ == "__main__":
    run_pipeline(update_sheet=True)

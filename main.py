import pandas as pd
import time
from src.pipeline import run_pipeline
from agents.graph import build_graph
from src.bronze import load_config
from src.to_xlsx import export_to_xlsx
from reset_errors import reset_errors


def main(limit=30):
    print(f"\n{'='*60}")
    print(f"ORQUESTRAÇÃO DO PIPELINE")
    print(f"{'='*60}")

    print("\n  [*] Sincronizando arquitetura Medallion (Drive -> Gold)...")
    run_pipeline()

    print("\n  [*] Limpando os erros da base Gold...")
    reset_errors()

    config = load_config()
    gold_path = config["data_paths"]["gold"]

    df_gold = pd.read_parquet(gold_path)

    df_pending_color = df_gold[
        (df_gold["save_status"] == "pending") & (df_gold["true_color"] == "pending")
    ]

    if df_pending_color.empty:
        print("  └─ [CHECK] Nenhum registro pendente localizado.")
    else:
        df_lote = df_pending_color.head(limit)
        print(f"  [*] Orquestrador: {len(df_pending_color)} pendências encontradas.")
        print(f"  └─ Processando lote atual de {len(df_lote)} registros...\n")

        app = build_graph()

        for index, row in df_lote.iterrows():
            book_state = {
                "tombo": str(row["tombo"]),
                "title": str(row["titulo"]),
                "authors": str(row["autores"]),
                "retry_count": 0,
            }

            try:
                app.invoke(book_state)

                print(f"  [INFO] Estabilização de API (5s)...")
                time.sleep(5)

            except Exception as e:
                erro_msg = str(e)
                if "429" in erro_msg or "RESOURCE_EXHAUSTED" in erro_msg:
                    print(f"\n  [EMERGÊNCIA] Limite de Cota (Rate Limit) atingido.")
                    print(f"  └─ Salvando progresso e encerrando lote prematuramente.")
                    break
                else:
                    print(f"\n  [!] Falha Crítica: {erro_msg}")
                    break

    print("\n  [*] Finalizando Reverse ETL (Gold -> XLSX)...")
    export_to_xlsx()

    print(f"\n{'='*60}")
    print(f"{' '*13}PIPELINE FINALIZADO COM SUCESSO")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main(limit=5)

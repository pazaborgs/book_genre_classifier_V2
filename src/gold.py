import pandas as pd
import os
from src.silver import load_config


def process_gold():
    """
    Prepara a base final (Gold) para consumo da IA.
    Implementa Idempotência: Cria a base do zero ou adiciona apenas livros novos,
    preservando o histórico de processamento já existente.
    """

    config = load_config()
    silver_path = config["data_paths"]["silver"]
    gold_path = config["data_paths"]["gold"]

    # Validação

    if not os.path.exists(silver_path):
        print(f"\n[ERRO] Camada Silver não encontrada: {silver_path}")
        print("      Execute o processamento da Silver primeiro.\n")
        return

    print(f"\n  [*] Estruturando dados para inferência...")

    try:
        df_silver = pd.read_parquet(silver_path)

        target_cols = [
            "tombo",
            "titulo",
            "autores",
            "editora",
            "notas_gerais",
            "notas_de_conteudo",
            "assuntos_tags",
            "cor",
        ]

        # Seleção de colunas

        cols_existing = [col for col in target_cols if col in df_silver.columns]
        df_silver_filtered = df_silver[cols_existing].copy()

        # Cor -> true_color

        if "cor" in df_silver_filtered.columns:
            df_silver_filtered = df_silver_filtered.rename(
                columns={"cor": "true_color"}
            )

        model_columns = [
            "searched_synopsis",
            "search_source",
            "final_synopsis",
            "final_tags",
            "color_suggestion",
            "justification",
            "top_3_probabilities",
            "processed_at",
        ]

        if os.path.exists(gold_path):
            print("  [INFO] Base Gold existente detectada. Verificando novos livros...")

            df_gold_current = pd.read_parquet(gold_path)
            current_entries = df_gold_current["tombo"].tolist()

            df_latest_entries = df_silver_filtered[
                ~df_silver_filtered["tombo"].isin(current_entries)
            ].copy()

            if df_latest_entries.empty:
                print(
                    "  └─ [SUCESSO] Nenhum livro novo. A Camada Gold já está sincronizada.\n"
                )
                return

            print(
                f"  [INFO] {len(df_latest_entries)} novos livros encontrados. Preparando schema..."
            )

            for col in model_columns:
                df_latest_entries[col] = None
            df_latest_entries["save_status"] = "pending"
            df_latest_entries["retry_count"] = 0

            # JOIN

            df_gold_final = pd.concat(
                [df_gold_current, df_latest_entries], ignore_index=True
            )

        else:
            print("  [INFO] Primeira execução. Criando base Gold...")
            df_gold_final = df_silver_filtered.copy()

            for col in model_columns:
                df_gold_final[col] = None
            df_gold_final["save_status"] = "pending"
            df_gold_final["retry_count"] = 0

        os.makedirs(os.path.dirname(gold_path), exist_ok=True)
        df_gold_final.to_parquet(gold_path, index=False)

        print(f"  └─ [SUCESSO] Camada Gold salva/atualizada.")
        print(f"     [STATS]   Total de livros na base Gold: {len(df_gold_final)}")
        print(f"     [INFO]    Destino: {gold_path}\n")

    except Exception as e:
        print(f"\n[!] Falha crítica na camada Gold:")
        print(f"    Erro: {e}\n")


if __name__ == "__main__":
    process_gold()

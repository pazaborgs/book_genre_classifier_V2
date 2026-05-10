import pandas as pd
import os
from src.bronze import load_config


def export_to_xlsx():
    """
    Reverse ETL: Lê a Gold, filtra os classificados com sucesso,
    remove colunas técnicas e exporta para os bibliotecários.
    """

    print("\n  [*] Iniciando exportação para Excel (Reverse ETL)...")

    config = load_config()
    gold_path = config["data_paths"]["gold"]
    export_data_path = config["data_paths"]["export_data"]

    os.makedirs(os.path.dirname(export_data_path), exist_ok=True)

    try:
        df = pd.read_parquet(gold_path)
        df_done = df[df["save_status"] == "ok"].copy()

        if df_done.empty:
            print("  [Export] Nenhum livro classificado encontrado para exportação.")
            return

        cols_to_drop = [
            "searched_synopsis",
            "search_source",
            "top_3_probabilities",
            "save_status",
            "retry_count",
            "assuntos_tags",
        ]

        df_clean = df_done.drop(columns=cols_to_drop, errors="ignore")

        # Ordenando

        priority_cols = ["tombo", "titulo", "autores"]
        existing_cols = [col for col in priority_cols if col in df_clean.columns]
        remaining_cols = [col for col in df_clean.columns if col not in existing_cols]
        df_clean = df_clean[existing_cols + remaining_cols]

        # To Excel

        df_clean.to_excel(export_data_path, index=False)

        print(f"  └─ [SUCESSO] 📊 Excel gerado! ({len(df_clean)} livros formatados)")
        print(f"     [INFO]    📁 Salvo em: {export_data_path}\n")

    except Exception as e:
        print(f"  [!] Falha ao gerar o Excel: {e}")


if __name__ == "__main__":
    export_to_xlsx()

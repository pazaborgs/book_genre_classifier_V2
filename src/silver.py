import pandas as pd
import os
from src.bronze import load_config


def process_silver():
    """
    Aplica regras de limpeza, padronização e desduplicação aos dados brutos.
    Salva o resultado no formato Parquet na camada Silver.
    """

    config = load_config()
    bronze_path = config["data_paths"]["bronze"]
    silver_path = config["data_paths"]["silver"]

    # Validação

    if not os.path.exists(bronze_path):
        print(f"\n[ERRO] Camada Bronze não encontrada: {bronze_path}")
        print("       Execute 'python src/bronze.py' primeiro.\n")
        return

    print(f"\n  [*] Iniciando limpeza e padronização...")

    try:
        df = pd.read_csv(bronze_path)

        # Renomeando e selecionando colunas

        to_drop = [
            "Local",
            "Exemplar",
            "Aquisição/ doação ou compra",
            "Data de Entrada",
        ]
        to_rename = {
            "Notas gerais - Público alvo(campo 61 phl)": "Notas_Gerais",
            "Entrada Secundária - ilustrador, adap...": "Entrada_secundaria",
        }

        cols_to_drop = [col for col in to_drop if col in df.columns]
        df = df.drop(columns=cols_to_drop).rename(columns=to_rename)

        # Padronizando cabeçalhos

        df.columns = (
            df.columns.str.lower()
            .str.strip()
            .str.normalize("NFKD")
            .str.encode("ascii", errors="ignore")
            .str.decode("utf-8")
            .str.replace(" ", "_")
            .str.replace(r"[^\w]", "", regex=True)
        )

        # Desduplicação e Merge

        df = df.drop_duplicates(subset=["titulo", "autores"])

        cols_assunto = ["assunto", "assunto1", "assunto2", "assunto3"]
        cols_assunto_existing = [col for col in cols_assunto if col in df.columns]

        if cols_assunto_existing:
            df["assuntos_tags"] = (
                df[cols_assunto_existing]
                .fillna("")
                .agg(", ".join, axis=1)
                .str.strip(", ")
                .str.replace(r", ,+", ", ", regex=True)
            )
            df = df.drop(columns=cols_assunto_existing)

        # Tratamento de nulos

        df = df.dropna(subset=["titulo"])
        df["autores"] = df.get("autores", pd.Series()).fillna("autor_desconhecido")
        df["editora"] = df.get("editora", pd.Series()).fillna("editora_desconhecida")
        df["cor"] = (
            df.get("cor", pd.Series())
            .replace(r"^\s*$", None, regex=True)
            .fillna("pending")
        )
        text_cols = df.select_dtypes(include=["object", "string"]).columns
        for col in text_cols:
            df[col] = (
                df[col]
                .fillna("")
                .astype(str)
                .str.lower()
                .str.strip()
                .str.normalize("NFKD")
                .str.encode("ascii", errors="ignore")
                .str.decode("utf-8")
            )

        # Salvamento

        os.makedirs(os.path.dirname(silver_path), exist_ok=True)
        df.to_parquet(silver_path, index=False)

        # Relatório de Qualidade

        done = (df["cor"] != "pendente").sum() if "cor" in df.columns else 0
        not_done = (df["cor"] == "pendente").sum() if "cor" in df.columns else 0

        print(f"  └─ [SUCESSO] Camada Silver processada.")
        print(f"     [STATS]   Obras únicas: {df.shape[0]} | Colunas: {df.shape[1]}")
        print(f"     [STATS]   Gabarito: {done} | Alvo IA: {not_done}")
        print(f"     [INFO]    Destino: {silver_path}\n")

    except Exception as e:
        print(f"\n[!] Falha ao processar camada Silver:")
        print(f"    Erro: {e}\n")


if __name__ == "__main__":
    process_silver()

import pandas as pd
import yaml
import os


def load_config(config_path="config/config.yaml"):
    """
    Lê o ficheiro YAML de configuração.
    """

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ingest_bronze():
    """
    Copia os dados da origem para a camada Bronze, sem alterações.
    """

    config = load_config()
    raw_data_path = config["data_paths"]["raw_data"]
    bronze_path = config["data_paths"]["bronze"]

    if not os.path.exists(raw_data_path):
        print(f"\n[ERRO] Arquivo não encontrado: {raw_data_path}")
        return

    print(f"\n  [*] Iniciando ingestão dos dados...")

    try:
        df = pd.read_excel(raw_data_path)
        os.makedirs(os.path.dirname(bronze_path), exist_ok=True)

        df.to_csv(bronze_path, index=False, encoding="utf-8")

        print(f"  └─ [SUCESSO] Camada Bronze atualizada.")
        print(f"     [INFO]    Destino: {bronze_path}\n")

    except Exception as e:
        print(f"\n[!] Falha crítica no processamento Bronze:")
        print(f"    Detalhes: {e}\n")


if __name__ == "__main__":
    ingest_bronze()

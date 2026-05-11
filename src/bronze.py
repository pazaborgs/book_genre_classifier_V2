import pandas as pd
import yaml
import os

def load_config(config_path: str = "config/config.yaml") -> dict:
    """
    Lê o arquivo YAML de configuração.

    Args:
        config_path (str, optional): Caminho para o arquivo config.yaml. 
            Default = "config/config.yaml".

    Returns:
        dict: Um dicionário contendo as chaves e valores lidos do arquivo YAML.
    """

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ingest_bronze():
    """
    Copia os dados da origem para a camada Bronze, sem alterações.
    A função lê o caminho dos dados através do arquivo de configuração, 
    cria os diretórios necessários e salva o arquivo de saída.
    """

    config = load_config()
    raw_data_path = config["data_paths"]["raw_data"]
    bronze_path = config["data_paths"]["bronze"]

    if not os.path.exists(raw_data_path):   # Verifica existência do caminho

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

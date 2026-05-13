import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from src.bronze import load_config


def download_spreadsheet():
    """
    Conecta ao Google Drive, baixa a planilha mais recente e salva na camada RAW.
    A função lê o caminho dos dados através do arquivo de configuração, 
    cria os diretórios necessários e salva o arquivo de saída.
    """

    config = load_config()

    raw_data_path = config["data_paths"]["raw_data"]
    spreadsheet_id = config["sheets"]["spreadsheet_id"]
    credentials_path = config["sheets"]["credentials_path"]

    # Verificando as credenciais

    if not os.path.exists(credentials_path):
        print(f"\n[ERRO] Arquivo de credenciais não encontrado: {credentials_path}")
        return

    print(f"\n  [*] Iniciando conexão com o Google Drive...")

    try:
        # Autenticando a conta de serviço

        scopes = ["https://www.googleapis.com/auth/drive.readonly"]
        creds = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=scopes
        )

        service = build("drive", "v3", credentials=creds)
        print(f"  [-] Conectado com sucesso. Lendo arquivo ID: {spreadsheet_id}")

        request = service.files().get_media(fileId=spreadsheet_id)

        # Garantindo a pasta

        os.makedirs(os.path.dirname(raw_data_path), exist_ok=True)

        # Baixando em lotes

        with open(raw_data_path, "wb") as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    print(
                        f"  [-] Progresso do download: {int(status.progress() * 100)}%"
                    )

        print(f"  └─ [SUCESSO] Planilha atualizada.")
        print(f"     [INFO]    Destino: {raw_data_path}\n")

    except Exception as e:
        print(f"\n[!] Falha crítica no download do Drive:")
        print(f"    Detalhes: {e}\n")


if __name__ == "__main__":
    download_spreadsheet()

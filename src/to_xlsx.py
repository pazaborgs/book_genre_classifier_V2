import os
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from src.bronze import load_config


def export_to_xlsx():
    """
    Reverse ETL: Lê a camada Gold, processa os dados, salva localmente em .xlsx
    e sincroniza com uma pasta específica e compartilhada no Google Drive.
    """

    config = load_config()

    gold_path = config["data_paths"]["gold"]
    export_data_path = config["data_paths"]["export_data"]
    credentials_path = config["sheets"]["credentials_path"]
    target_folder_id = config["sheets"]["target_folder_id"]
    target_file_name = "tombo_export.xlsx"

    print(f"\n  [*] Iniciando exportação para Excel (Reverse ETL)...")

    # FASE LOCAL - Processamento e Salvamento

    try:
        os.makedirs(os.path.dirname(export_data_path), exist_ok=True)

        df = pd.read_parquet(gold_path)
        processed_df = df[df["save_status"] == "ok"].copy()

        if processed_df.empty:
            print("  [!] Nenhum livro classificado encontrado para exportação.")
            return

        technical_cols = [
            "searched_synopsis",
            "search_source",
            "top_3_probabilities",
            "save_status",
            "retry_count",
            "assuntos_tags",
        ]
        cleaned_df = processed_df.drop(columns=technical_cols, errors="ignore")

        priority_cols = ["tombo", "titulo", "autores"]
        existing_cols = [col for col in priority_cols if col in cleaned_df.columns]
        remaining_cols = [col for col in cleaned_df.columns if col not in existing_cols]
        cleaned_df = cleaned_df[existing_cols + remaining_cols]

        cleaned_df.to_excel(export_data_path, index=False)
        print(
            f"  [-] Excel local gerado com sucesso. ({len(cleaned_df)} livros formatados)"
        )

    except Exception as e:
        print(f"\n[!] Falha crítica na geração local do Excel: {e}")
        return

    # FASE CLOUD - Google Drive Sync

    if not os.path.exists(credentials_path):
        print(f"\n[ERRO] Arquivo de credenciais não encontrado em: {credentials_path}")
        return

    print(f"\n  [*] Conectando ao Google Drive...")

    try:
        creds = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=["https://www.googleapis.com/auth/drive"]
        )
        service = build("drive", "v3", credentials=creds)

        print(f"  [-] Buscando '{target_file_name}' na pasta compartilhada...")

        query = f"name = '{target_file_name}' and '{target_folder_id}' in parents and trashed = false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get("files", [])

        media = MediaFileUpload(
            export_data_path,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            resumable=True,
        )

        if files:
            file_id = files[0]["id"]
            print(
                f"  [-] Arquivo encontrado. Realizando In-Place Update (ID: {file_id})..."
            )
            service.files().update(fileId=file_id, media_body=media).execute()
            print(f"  └─ [SUCESSO] Planilha atualizada na nuvem!")
        else:
            print(f"  [-] Arquivo não encontrado. Criando novo arquivo...")
            file_metadata = {"name": target_file_name, "parents": [target_folder_id]}
            service.files().create(body=file_metadata, media_body=media).execute()
            print(f"  └─ [SUCESSO] Novo arquivo criado na pasta compartilhada.")

    except Exception as e:
        print(f"\n[!] Falha crítica na sincronização com o Drive: {e}")


if __name__ == "__main__":
    export_to_xlsx()

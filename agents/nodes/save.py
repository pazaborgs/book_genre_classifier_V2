import pandas as pd
import json
from datetime import datetime
from src.bronze import load_config


def save_node(state: dict) -> dict:
    """
    Nó 3: Persistência de Dados (Padrão UPDATE)
    Localiza o registro na camada Gold e consolida os metadados finais.
    """
    config = load_config()
    gold_path = config["data_paths"]["gold"]
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    tombo = state.get("tombo", "")
    title = state.get("title", "")
    color = state.get("color_suggestion", "ERRO")

    print(f"\n  [*] Finalizando ciclo de vida: '{title}'")

    try:
        df = pd.read_parquet(gold_path)

        # Localiza a linha exata pelo tombo (PK)
        mask = df["tombo"].astype(str) == str(tombo)

        if not mask.any():
            print(f"  [!] ERRO: Tombo {tombo} não localizado na base Gold.")
            return {"save_status": "pending"}

        # Injeção de metadados processados
        df.loc[mask, "color_suggestion"] = color
        df.loc[mask, "justification"] = state.get("justification", "")
        df.loc[mask, "final_synopsis"] = state.get("final_synopsis", "")
        df.loc[mask, "final_tags"] = ", ".join(state.get("final_tags", []))
        df.loc[mask, "search_source"] = state.get("search_source", "")
        df.loc[mask, "searched_synopsis"] = state.get("searched_synopsis", "")
        df.loc[mask, "top_3_probabilities"] = json.dumps(
            state.get("top_3_probabilities", [])
        )
        df.loc[mask, "processed_at"] = now

        # Lógica de status binária para o banco e para o grafo
        status_final = "ok" if color != "ERRO" else "pending"
        df.loc[mask, "save_status"] = status_final

        # Persistência em Parquet (Gold Layer)
        df.to_parquet(gold_path, index=False)

        print(f"  └─ [SUCESSO] Persistência concluída na camada Gold.")
        print(f"     [INFO]    Status do registro: {status_final}\n")

        return {"save_status": status_final}

    except Exception as e:
        print(f"\n[!] Falha crítica na gravação Gold:")
        print(f"    Detalhes: {e}\n")
        return {"save_status": "pending"}

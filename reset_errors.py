import pandas as pd
from src.bronze import load_config

print("\n  [*] Limpando os erros da base Gold...")


def reset_errors():

    config = load_config()
    gold_path = config["data_paths"]["gold"]
    df = pd.read_parquet(gold_path)
    errors = len(df[df["save_status"] == "error"])
    df.loc[df["save_status"] == "error", "save_status"] = "pending"
    df.to_parquet(gold_path, index=False)
    print(f"  └─ [SUCESSO] {errors} livros voltaram para a fila de classificação.")

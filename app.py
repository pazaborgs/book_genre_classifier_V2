import streamlit as st
import pandas as pd
import ast
from datetime import datetime, timedelta
from src.bronze import load_config

st.set_page_config(page_title="UME Andradas 2 | Logs", page_icon="📖", layout="wide")


def main():
    st.markdown("> **`Classificador de Livros (V2)`**")
    st.markdown("---")

    try:
        config = load_config()
        gold_path = config["data_paths"]["gold"]

        df = pd.read_parquet(gold_path)
        df_success = df[df["save_status"].isin(["ok", "concluido"])].copy()

        if df_success.empty:
            st.error("> [ERRO] Nenhum livro classificado no banco de dados.")
            return

        if "processed_at" in df_success.columns:
            df_success["processed_at"] = pd.to_datetime(
                df_success["processed_at"], format="%d/%m/%Y %H:%M:%S", errors="coerce"
            )
            df_success = df_success.dropna(subset=["processed_at"])
            df_success = df_success.sort_values(by="processed_at", ascending=False)

        st.markdown("### `[⚙️] PARÂMETROS DE FILTRAGEM`")
        filter_col1, filter_col2 = st.columns(2)

        with filter_col1:
            timeframe_options = [
                "Hoje",
                "Últimos 3 dias",
                "Últimos 7 dias",
                "Todos os registros",
            ]
            selected_timeframe = st.selectbox(
                "`Selecione o Timeframe:`", timeframe_options
            )

        with filter_col2:
            unique_colors = sorted(
                df_success["color_suggestion"].dropna().unique().tolist()
            )
            selected_colors = st.multiselect(
                "`Filtrar por Cor (Deixe vazio para todas):`", unique_colors
            )

        now = datetime.now()
        if selected_timeframe == "Hoje":
            df_success = df_success[df_success["processed_at"].dt.date == now.date()]
        elif selected_timeframe == "Últimos 3 dias":
            df_success = df_success[
                df_success["processed_at"] >= (now - timedelta(days=3))
            ]
        elif selected_timeframe == "Últimos 7 dias":
            df_success = df_success[
                df_success["processed_at"] >= (now - timedelta(days=7))
            ]

        if selected_colors:
            df_success = df_success[
                df_success["color_suggestion"].isin(selected_colors)
            ]

        st.markdown("---")
        st.markdown(f"### `[>] RESULTADOS ENCONTRADOS: {len(df_success)}`")

        if df_success.empty:
            st.warning("`> [AVISO] Nenhum registro bate com os filtros aplicados.`")
            return

        latest_books = df_success.head(20)

        for _, row in latest_books.iterrows():
            title = row.get("titulo", "Sem Título").upper()
            author = row.get("autores", "Desconhecido")
            book_id = row.get("tombo", "N/A")
            color = row.get("color_suggestion", "ERRO")
            justification = row.get("justification", "Sem justificativa.")
            proc_date = row["processed_at"].strftime("%d/%m/%Y %H:%M:%S")

            # Tratamento seguro para extrair e formatar as probabilidades
            # Assumindo que a coluna gerada pelo seu Pydantic schema chama 'top_3_probabilities'
            raw_probs = row.get("top_3_probabilities", "N/A")
            probs_formatted = "N/A"

            if isinstance(raw_probs, dict):
                probs_formatted = " | ".join(
                    [f"{k}: {float(v)*100:.1f}%" for k, v in raw_probs.items()]
                )
            elif isinstance(raw_probs, str) and raw_probs.startswith("{"):
                try:
                    dict_probs = ast.literal_eval(raw_probs)
                    probs_formatted = " | ".join(
                        [f"{k}: {float(v)*100:.1f}%" for k, v in dict_probs.items()]
                    )
                except Exception:
                    probs_formatted = raw_probs
            else:
                probs_formatted = str(raw_probs)

            log_entry = f"""> LIVRO_ID: {book_id} | TIMESTAMP: {proc_date}
> TÍTULO:   {title}
> AUTOR:    {author}
> STATUS:   [CLASSIFICADO]
> COR_ALVO: [{color}]
> SCORES:   [{probs_formatted}]
> LOG:      "{justification}"
"""
            st.code(log_entry, language="yaml")

    except Exception as e:
        st.error(f"`> [FATAL EXCEPTION] Falha ao ler a camada Gold: {e}`")


if __name__ == "__main__":
    main()

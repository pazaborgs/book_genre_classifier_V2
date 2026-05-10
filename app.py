import streamlit as st
import pandas as pd
import ast
from datetime import datetime, timedelta
from src.bronze import load_config

st.set_page_config(page_title="book_genre_classifier_V2", page_icon="📖", layout="wide")

# Paleta

CLI_PALETTE = {
    "DIDÁTICO": "#56B6C2",
    "VERMELHO": "#E06C75",
    "OURO": "#D19A66",
    "AMARELO": "#E5C07B",
    "PRATA": "#ABB2BF",
    "LARANJA": "#FF8C00",
    "VERDE": "#98C379",
    "PRETO": "#5C6370",
    "AZUL": "#61AFEF",
    "BRANCO": "#FFFFFF",
    "ERRO": "#FF0000",
}


def get_badge_html(color_name: str) -> str:
    """
    Gera um indicador de status com estética CLI.
    """
    hex_color = CLI_PALETTE.get(color_name.upper(), "#FF0000")

    return f"""
    <div style="
        display: flex; 
        align-items: center; 
        justify-content: flex-end; 
        font-family: 'Courier New', Courier, monospace;
        font-weight: bold;
        font-size: 1.1rem;
        letter-spacing: 1px;
        color: #E0E0E0;
        margin-top: 5px;
    ">
        <span style="
            display: inline-block;
            width: 14px;
            height: 14px;
            background-color: {hex_color};
            border-radius: 50%;
            margin-right: 8px;
        "></span>
        {color_name}
    </div>
    """


def main():

    try:
        config = load_config()
        gold_path = config["data_paths"]["gold"]

        df = pd.read_parquet(gold_path)
        df_success = df[df["save_status"].isin(["ok", "concluido"])].copy()

        if df_success.empty:
            st.error("> `[ERRO] Nenhum livro classificado no banco de dados.`")
            return

        if "processed_at" in df_success.columns:
            df_success["processed_at"] = pd.to_datetime(
                df_success["processed_at"], format="%d/%m/%Y %H:%M:%S", errors="coerce"
            )
            df_success = df_success.dropna(subset=["processed_at"])
            df_success = df_success.sort_values(by="processed_at", ascending=False)

        st.markdown("### `[⚙️] PARÂMETROS DE BUSCA`")
        filter_col1, filter_col2 = st.columns(2)

        with filter_col1:
            timeframe_options = ["Hoje", "Últimos 3 dias", "Últimos 7 dias", "Todos"]
            selected_timeframe = st.selectbox("`Timeframe:`", timeframe_options)

        with filter_col2:
            unique_colors = sorted(
                df_success["color_suggestion"].dropna().unique().tolist()
            )
            selected_colors = st.multiselect("`Cor-Alvo:`", unique_colors)

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
        st.markdown(f"### `[>] REGISTROS ENCONTRADOS: {len(df_success)}`")

        if df_success.empty:
            st.warning("`> [AVISO] Query retornou 0 resultados.`")
            return

        # Render

        grid_cols = st.columns(2)

        for index, (_, row) in enumerate(df_success.iterrows()):
            title = str(row.get("titulo", "Sem Título")).upper()
            author = str(row.get("autores", "Desconhecido")).upper()
            book_id = str(row.get("tombo", "N/A"))
            color = str(row.get("color_suggestion", "ERRO"))
            justification = str(row.get("justification", "Sem justificativa."))
            proc_date = row["processed_at"].strftime("%d/%m/%y %H:%M")

            # Prob Parser

            raw_probs = row.get("top_3_probabilities", "[]")
            probs_formatted = "N/A"

            if isinstance(raw_probs, str) and raw_probs.startswith("["):
                try:
                    list_probs = ast.literal_eval(raw_probs)
                    if isinstance(list_probs, list):
                        probs_formatted = " | ".join(
                            [
                                f"{p.get('color', '?')}: {float(p.get('score', 0))*100:.0f}%"
                                for p in list_probs
                            ]
                        )
                except Exception:
                    probs_formatted = "[ERRO_NO_PARSER]"

            with grid_cols[index % 2]:
                with st.container(border=True):

                    # Título na esquerda (70%), Badge na direita (30%)
                    c_title, c_badge = st.columns([7, 3])

                    with c_title:
                        st.markdown(f"#### `{title}`")
                        st.caption(
                            f"**AUTOR:** `{author}`  |  **TOMBO:** `{book_id}`  |  **DATA:** `{proc_date}`"
                        )

                    with c_badge:
                        st.markdown(get_badge_html(color), unsafe_allow_html=True)

                    st.markdown("**`> JUSTIFICATIVA:`**")
                    st.info(justification, icon="🤖")

                    st.markdown(f"**`> SCORES:`**   `{probs_formatted}`")

    except Exception as e:
        st.error(f"`> [FATAL EXCEPTION] Kernel Panic: {e}`")


if __name__ == "__main__":
    main()

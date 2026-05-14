import streamlit as st
import pandas as pd
import ast
import html as html_lib
from datetime import datetime, timedelta
from src.bronze import load_config

st.set_page_config(
    page_title="book_genre_classifier",
    page_icon="📖",
    layout="wide",
)

# ── Paleta ────────────────────────────────────────────────────────────────────
CLI_PALETTE = {
    "DIDÁTICO": "#56B6C2",
    "PARADIDÁTICO": "#56B6C2",
    "VERMELHO": "#E06C75",
    "OURO": "#D19A66",
    "AMARELO": "#E5C07B",
    "PRATA": "#ABB2BF",
    "LARANJA": "#FF8C00",
    "VERDE": "#98C379",
    "PRETO": "#7A8694",
    "AZUL": "#61AFEF",
    "BRANCO": "#DCDFE4",
    "ERRO": "#E06C75",
}

# ── Estilos globais ───────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600&display=swap');

/* Reset geral */
html, body, [class*="css"] {
    font-family: 'JetBrains Mono', 'Courier New', monospace !important;
}

/* Fundo da página */
.stApp {
    background-color: #1E2127;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #181A1F;
    border-right: 1px solid #2C313A;
}

/* Esconde botão de deploy e menu */
#MainMenu, footer, header { visibility: hidden; }

/* Inputs e selects */
[data-testid="stSelectbox"] > div,
[data-testid="stMultiSelect"] > div {
    background-color: #2C313A !important;
    border: 1px solid #3E4451 !important;
    border-radius: 4px !important;
    color: #ABB2BF !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* Labels */
label, .stSelectbox label, .stMultiSelect label {
    color: #5C6370 !important;
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* Divisor */
hr { border-color: #2C313A !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #1E2127; }
::-webkit-scrollbar-thumb { background: #3E4451; border-radius: 2px; }
</style>
""",
    unsafe_allow_html=True,
)


# ── Componentes HTML ──────────────────────────────────────────────────────────


def terminal_chrome(title: str = "book_genre_classifier — zsh") -> str:
    dot = (
        lambda c: f'<span style="width:12px;height:12px;border-radius:50%;background:{c};display:inline-block;"></span>'
    )
    return (
        '<div style="background:#282C34;border:1px solid #3E4451;border-radius:8px 8px 0 0;'
        'padding:10px 16px;display:flex;align-items:center;gap:8px;margin-bottom:0;">'
        + dot("#E06C75")
        + dot("#E5C07B")
        + dot("#98C379")
        + f"<span style=\"margin-left:12px;font-family:'JetBrains Mono',monospace;"
        f'font-size:0.72rem;color:#5C6370;letter-spacing:0.05em;">{html_lib.escape(title)}</span>'
        + "</div>"
    )


def color_badge(color_name: str) -> str:
    hex_color = CLI_PALETTE.get(color_name.upper(), "#E06C75")
    return f"""
    <div style="display:flex;align-items:center;gap:7px;justify-content:flex-end;">
        <span style="
            width:9px;height:9px;border-radius:50%;
            background:{hex_color};
            flex-shrink:0;
            box-shadow: 0 0 6px {hex_color}88;
        "></span>
        <span style="
            font-family:'JetBrains Mono',monospace;
            font-size:0.78rem;
            font-weight:600;
            color:{hex_color};
            letter-spacing:0.06em;
        ">{color_name.upper()}</span>
    </div>
    """


def tags_row(tags: list[str]) -> str:
    pill_style = (
        "background:#2C313A;border:1px solid #3E4451;color:#5C6370;"
        "font-family:'JetBrains Mono',monospace;font-size:0.65rem;"
        "padding:2px 8px;border-radius:3px;letter-spacing:0.04em;"
    )
    pills = "".join(
        f'<span style="{pill_style}">#{html_lib.escape(t)}</span>' for t in tags
    )
    return f'<div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:10px;">{pills}</div>'


def scores_line(probs: list[dict]) -> str:
    parts = []
    for i, p in enumerate(probs):
        color_name = p.get("color", "?").upper()
        score_pct = f"{float(p.get('score', 0)) * 100:.0f}%"
        hex_c = CLI_PALETTE.get(color_name, "#5C6370")
        if i == 0:
            parts.append(
                f'<span style="color:{hex_c};font-weight:700;font-size:0.82rem;">{color_name}</span>'
                f'<span style="color:{hex_c};font-weight:700;font-size:0.82rem;opacity:0.85;">:{score_pct}</span>'
            )
        else:
            parts.append(
                f'<span style="color:{hex_c};font-weight:500;opacity:0.7;">{color_name}</span>'
                f'<span style="color:#5C6370;">:{score_pct}</span>'
            )
    sep = '<span style="color:#3E4451;margin:0 6px;">|</span>'
    joined = sep.join(parts)
    return (
        "<div style=\"font-family:'JetBrains Mono',monospace;font-size:0.72rem;margin-top:10px;"
        'padding:7px 10px;background:#1E2127;border-radius:4px;border-left:2px solid #3E4451;">'
        f'<span style="color:#5C6370;margin-right:10px;">scores</span>{joined}'
        "</div>"
    )


def book_card(row: pd.Series) -> str:
    title = str(row.get("titulo", "Sem Título")).upper()
    author = str(row.get("autores", "Desconhecido"))
    book_id = str(row.get("tombo", "N/A"))
    color = str(row.get("color_suggestion", "ERRO")).upper()
    justif = str(row.get("justification", "—"))
    proc_dt = row["processed_at"]
    proc_date = proc_dt.strftime("%d/%m/%y") if pd.notna(proc_dt) else "—"
    proc_time = proc_dt.strftime("%H:%M") if pd.notna(proc_dt) else ""

    # Tags
    raw_tags = row.get("final_tags", "[]")
    tags: list[str] = []
    if isinstance(raw_tags, list):
        tags = raw_tags
    elif isinstance(raw_tags, str) and raw_tags.startswith("["):
        try:
            tags = ast.literal_eval(raw_tags)
        except Exception:
            tags = []

    # Scores
    raw_probs = row.get("top_3_probabilities", "[]")
    probs: list[dict] = []
    if isinstance(raw_probs, str) and raw_probs.startswith("["):
        try:
            probs = ast.literal_eval(raw_probs)
        except Exception:
            probs = []
    elif isinstance(raw_probs, list):
        probs = raw_probs

    hex_color = CLI_PALETTE.get(color, "#E06C75")
    safe_justif = html_lib.escape(justif)
    safe_title = html_lib.escape(title)
    safe_author = html_lib.escape(author.upper())

    return (
        f'<div style="background:#21252B;border:1px solid #2C313A;border-top:2px solid {hex_color};'
        f"border-radius:0 0 6px 6px;padding:16px 18px 14px;margin-bottom:16px;font-family:'JetBrains Mono',monospace;\">"
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;margin-bottom:10px;">'
        f'<div style="flex:1;min-width:0;">'
        f'<div style="font-size:0.82rem;font-weight:600;color:{hex_color};letter-spacing:0.03em;line-height:1.4;'
        f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{safe_title}</div>'
        f'<div style="margin-top:4px;font-size:0.68rem;color:#5C6370;letter-spacing:0.04em;">'
        f"{safe_author}"
        f'&nbsp;<span style="color:#3E4451;">·</span>&nbsp;'
        f'tombo <span style="color:#ABB2BF;">{book_id}</span>'
        f'&nbsp;<span style="color:#3E4451;">·</span>&nbsp;'
        f'<span style="color:#ABB2BF;">{proc_date}</span>'
        f'<span style="color:#3E4451;"> {proc_time}</span>'
        f"</div></div>"
        f'<div style="flex-shrink:0;">{color_badge(color)}</div>'
        f"</div>"
        f'<div style="border-top:1px solid #2C313A;margin:10px 0;"></div>'
        f'<div style="font-size:0.68rem;color:#5C6370;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:5px;">justificativa</div>'
        f'<div style="font-size:0.82rem;color:#C8CDD6;line-height:1.8;padding:10px 14px;'
        f'background:#1E2127;border-radius:4px;border-left:2px solid {hex_color}55;">{safe_justif}</div>'
        + (scores_line(probs) if probs else "")
        + (tags_row(tags) if tags else "")
        + "</div>"
    )


# ── App principal ─────────────────────────────────────────────────────────────
def main():
    try:
        config = load_config()
        gold_path = config["data_paths"]["gold"]
        df = pd.read_parquet(gold_path)
        df_ok = df[df["save_status"].isin(["ok", "concluido"])].copy()

        if df_ok.empty:
            st.error("`[ERRO] Nenhum livro classificado no banco de dados.`")
            return

        if "processed_at" in df_ok.columns:
            df_ok["processed_at"] = pd.to_datetime(
                df_ok["processed_at"], format="%d/%m/%Y %H:%M:%S", errors="coerce"
            )
            df_ok = df_ok.dropna(subset=["processed_at"])
            df_ok = df_ok.sort_values("processed_at", ascending=False)

        # ── Header ────────────────────────────────────────────────────────────
        st.markdown(terminal_chrome(), unsafe_allow_html=True)
        st.markdown(
            """
        <div style="
            background:#282C34;
            border:1px solid #3E4451;
            border-top:none;
            border-radius:0 0 6px 6px;
            padding:14px 20px 16px;
            margin-bottom:24px;
            font-family:'JetBrains Mono',monospace;
        ">
            <div style="font-size:0.68rem;color:#5C6370;margin-bottom:2px;">
                ~ / acervo / classificador
            </div>
            <div style="font-size:1.05rem;color:#DCDFE4;font-weight:600;letter-spacing:0.02em;">
                book_genre_classifier
                <span style="color:#98C379;font-weight:400;font-size:0.78rem;margin-left:8px;">v2</span>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # ── Filtros ───────────────────────────────────────────────────────────
        col_tf, col_cor, col_info = st.columns([2, 3, 2])

        with col_tf:
            timeframe = st.selectbox(
                "timeframe",
                ["Hoje", "Últimos 3 dias", "Últimos 7 dias", "Todos"],
            )

        with col_cor:
            cores_unicas = sorted(df_ok["color_suggestion"].dropna().unique().tolist())
            cores_sel = st.multiselect("cor-alvo", cores_unicas)

        # Aplicar filtros
        now = datetime.now()
        if timeframe == "Hoje":
            df_ok = df_ok[df_ok["processed_at"].dt.date == now.date()]
        elif timeframe == "Últimos 3 dias":
            df_ok = df_ok[df_ok["processed_at"] >= now - timedelta(days=3)]
        elif timeframe == "Últimos 7 dias":
            df_ok = df_ok[df_ok["processed_at"] >= now - timedelta(days=7)]

        if cores_sel:
            df_ok = df_ok[df_ok["color_suggestion"].isin(cores_sel)]

        with col_info:
            st.markdown(
                f"""
            <div style="
                margin-top:28px;
                font-family:'JetBrains Mono',monospace;
                font-size:0.72rem;
                color:#5C6370;
                text-align:right;
            ">
                <span style="color:#61AFEF;font-weight:600;">{len(df_ok)}</span>
                &nbsp;registros
            </div>
            """,
                unsafe_allow_html=True,
            )

        st.markdown("<hr>", unsafe_allow_html=True)

        if df_ok.empty:
            st.markdown(
                """
            <div style="
                font-family:'JetBrains Mono',monospace;
                font-size:0.8rem;
                color:#5C6370;
                padding:24px 0;
                text-align:center;
            ">
                <span style="color:#E06C75;">✕</span>&nbsp; query retornou 0 resultados
            </div>
            """,
                unsafe_allow_html=True,
            )
            return

        # ── Grid de cards ─────────────────────────────────────────────────────
        col_a, col_b = st.columns(2, gap="medium")

        for i, (_, row) in enumerate(df_ok.iterrows()):
            target = col_a if i % 2 == 0 else col_b
            with target:
                st.markdown(
                    terminal_chrome(f"tombo/{row.get('tombo', 'N/A')}")
                    + book_card(row),
                    unsafe_allow_html=True,
                )

    except Exception as e:
        st.markdown(
            f"""
        <div style="
            font-family:'JetBrains Mono',monospace;
            color:#E06C75;
            font-size:0.8rem;
            padding:16px;
            background:#21252B;
            border:1px solid #E06C7533;
            border-radius:6px;
        ">
            [FATAL] kernel panic: {e}
        </div>
        """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
TAMU — Dashboard de Reservas v6
Sem Plotly e sem Matplotlib.

Arquivos necessários na mesma pasta:
- reservas_historico.json
- analise_reservas_apartamentos.json

Executar:
    py -m streamlit run dashboard_tamu_reservas_v6.py
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


BASE = Path(__file__).resolve().parent
ARQ_ANALISE = BASE / "analise_reservas_apartamentos.json"


st.set_page_config(
    page_title="TAMU | Dashboard de Reservas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# TEMA TAMU — DARK / TECH
# ============================================================

st.markdown(
    """
    <style>
    /* ========================================================
       ESTRUTURA GERAL
       ======================================================== */

    html, body, [data-testid="stAppViewContainer"] {
        background: #070B12 !important;
    }

    .stApp {
        background:
            radial-gradient(
                circle at 88% 8%,
                rgba(56,189,248,0.075),
                transparent 27%
            ),
            radial-gradient(
                circle at 8% 92%,
                rgba(255,77,90,0.045),
                transparent 24%
            ),
            #070B12 !important;
        color: #F5F7FA !important;
    }

    .main .block-container {
        background: transparent !important;
        max-width: 1500px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    /* Remove a faixa/header branco superior */
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 0 !important;
    }

    header[data-testid="stHeader"] > div {
        background: transparent !important;
    }

    [data-testid="stToolbar"] {
        background: transparent !important;
    }

    /* ========================================================
       SIDEBAR
       ======================================================== */

    section[data-testid="stSidebar"] {
        background:
            linear-gradient(
                180deg,
                #0A101C 0%,
                #080D16 55%,
                #070B12 100%
            ) !important;
        border-right: 1px solid rgba(56,189,248,0.10);
    }

    section[data-testid="stSidebar"] > div {
        background: transparent !important;
        padding-top: 1.2rem;
    }

    section[data-testid="stSidebar"] * {
        color: #DCE7F3 !important;
    }

    section[data-testid="stSidebar"] hr {
        border-color: rgba(148,163,184,0.10) !important;
    }

    /* ========================================================
       TIPOGRAFIA
       ======================================================== */

    h1, h2, h3, h4, h5, h6 {
        color: #F8FAFC !important;
    }

    p, label {
        color: #B6C5D6 !important;
    }

    .tamu-title {
        font-size: 2.25rem;
        font-weight: 800;
        letter-spacing: -0.8px;
        color: #F8FAFC;
        text-shadow: 0 0 25px rgba(56,189,248,0.12);
    }

    .tamu-title-accent {
        color: #38BDF8;
    }

    .tamu-subtitle {
        color: #7F93A9;
        font-size: 0.96rem;
        margin-top: -3px;
        margin-bottom: 12px;
    }

    .tamu-section {
        color: #F8FAFC;
        font-size: 1.30rem;
        font-weight: 800;
        border-left: 3px solid #38BDF8;
        padding-left: 10px;
        margin-top: 1.6rem;
        margin-bottom: 0.8rem;
    }

    /* ========================================================
       FILTROS — SEM CAIXAS BRANCAS
       ======================================================== */

    section[data-testid="stSidebar"] [data-baseweb="select"] {
        background: transparent !important;
    }

    section[data-testid="stSidebar"] [data-baseweb="select"] > div {
        background: #0E1726 !important;
        border: 1px solid rgba(91,160,210,0.16) !important;
        border-radius: 8px !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.018) !important;
        min-height: 42px !important;
    }

    section[data-testid="stSidebar"] [data-baseweb="select"] > div:hover {
        border-color: rgba(56,189,248,0.42) !important;
    }

    section[data-testid="stSidebar"] [data-baseweb="select"] input {
        color: #F8FAFC !important;
    }

    section[data-testid="stSidebar"] [data-baseweb="select"] svg {
        fill: #7890A8 !important;
    }

    /* Chips dos multiselect */
    section[data-testid="stSidebar"] span[data-baseweb="tag"] {
        background: #17263A !important;
        border: 1px solid rgba(56,189,248,0.20) !important;
        border-radius: 5px !important;
    }

    section[data-testid="stSidebar"] span[data-baseweb="tag"] * {
        color: #DFF4FF !important;
    }

    /* Popover dos filtros */
    div[data-baseweb="popover"] {
        background: #0D1625 !important;
        border: 1px solid rgba(56,189,248,0.18) !important;
    }

    div[data-baseweb="menu"] {
        background: #0D1625 !important;
    }

    div[data-baseweb="menu"] li {
        color: #DCE7F3 !important;
        background: #0D1625 !important;
    }

    div[data-baseweb="menu"] li:hover {
        background: #14253A !important;
    }

    /* ========================================================
       KPIs — MAIS FLUIDOS
       ======================================================== */

    [data-testid="stMetric"] {
        background:
            linear-gradient(
                145deg,
                rgba(16,29,48,0.88),
                rgba(8,15,27,0.82)
            ) !important;
        border: 1px solid rgba(56,189,248,0.16) !important;
        border-radius: 10px !important;
        padding: 14px 16px !important;
        box-shadow:
            0 8px 28px rgba(0,0,0,0.15),
            inset 0 1px 0 rgba(255,255,255,0.02) !important;
    }

    [data-testid="stMetricLabel"] {
        color: #E7EEF8 !important;
        font-size: 0.86rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.1px;
    }

    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-size: 2.15rem !important;
        line-height: 1.05 !important;
        font-weight: 900 !important;
        letter-spacing: -0.8px;
        text-shadow: 0 0 18px rgba(56,189,248,0.08);
    }

    /* ========================================================
       TABELAS
       ======================================================== */

    [data-testid="stDataFrame"] {
        border: 1px solid rgba(56,189,248,0.10) !important;
        border-radius: 9px !important;
        overflow: hidden !important;
    }

    /* ========================================================
       LINHAS / DIVISORES
       ======================================================== */

    hr {
        border-color: rgba(148,163,184,0.10) !important;
    }

    /* ========================================================
       ALERTAS / CAPTIONS
       ======================================================== */

    [data-testid="stAlert"] {
        background: #0D1625 !important;
        border: 1px solid rgba(56,189,248,0.15) !important;
        color: #DCE8F5 !important;
    }

    [data-testid="stCaptionContainer"],
    .stCaption {
        color: #71869D !important;
    }

    /* ========================================================
       LINKS / BOTÕES / ELEMENTOS NATIVOS
       ======================================================== */

    button {
        color: #DCE8F5 !important;
    }

    /* Remove fundos claros residuais do Streamlit */
    [data-testid="stAppViewContainer"] > section {
        background: transparent !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)



# ============================================================
# BARRAS HTML — SEM DEPENDÊNCIAS EXTERNAS
# ============================================================

def cor_serie(serie, indice=0):
    """
    Paleta TAMU + cores semânticas.
    """
    s = str(serie).strip().lower()

    if "airbnb" in s:
        return "#EC4899"       # rosa
    if "booking" in s:
        return "#8B5CF6"       # roxo
    if "cancel" in s:
        return "#EF4444"       # vermelho
    if "2025" in s:
        return "#238BFF"       # azul
    if "2026" in s:
        return "#22C55E"       # verde
    if "website" in s:
        return "#06B6D4"       # ciano
    if "sem canal" in s:
        return "#64748B"       # cinza azulado
    if "outro" in s:
        return "#F59E0B"       # âmbar

    cores = [
        "#238BFF",
        "#22C55E",
        "#EC4899",
        "#8B5CF6",
        "#06B6D4",
        "#F59E0B",
    ]
    return cores[indice % len(cores)]


def grafico_barras_html(df_grafico, titulo="", ylabel="Quantidade"):
    """
    Desenha barras horizontais/verticais simples em HTML/CSS.
    Os valores ficam sempre visíveis.
    """

    if df_grafico is None or len(df_grafico) == 0:
        st.info("Sem dados para exibir.")
        return

    # Série única
    if isinstance(df_grafico, pd.Series):
        dados = pd.DataFrame({
            "Categoria": [str(x) for x in df_grafico.index],
            "Valor": pd.to_numeric(df_grafico.values, errors="coerce").fillna(0)
            if hasattr(pd.to_numeric(df_grafico.values, errors="coerce"), "fillna")
            else pd.Series(pd.to_numeric(df_grafico.values, errors="coerce")).fillna(0),
        })
        dados["Serie"] = ""
    else:
        dados = df_grafico.copy()
        dados.index = [str(x) for x in dados.index]
        dados = dados.reset_index().rename(columns={"index": "Categoria"})

    # Normalizar para formato longo
    if "Valor" in dados.columns:
        longo = dados.copy()
    else:
        col_categoria = "Categoria"
        series_cols = [
            c for c in dados.columns
            if c != col_categoria
        ]

        registros = []
        for _, row in dados.iterrows():
            for serie in series_cols:
                valor = row[serie]
                if pd.notna(valor):
                    registros.append({
                        "Categoria": str(row[col_categoria]),
                        "Serie": str(serie),
                        "Valor": float(valor),
                    })
        longo = pd.DataFrame(registros)

    if longo.empty:
        st.info("Sem dados para exibir.")
        return

    longo["Valor"] = pd.to_numeric(longo["Valor"], errors="coerce").fillna(0)

    max_valor = float(longo["Valor"].max())
    if max_valor <= 0:
        max_valor = 1

    categorias = list(dict.fromkeys(longo["Categoria"].tolist()))
    series = list(dict.fromkeys(longo["Serie"].tolist()))

    # Altura proporcional para evitar gráfico gigante.
    altura = max(330, min(560, 150 + len(categorias) * 38))

    html = f"""
    <div style="
        border-radius:8px;
        padding:12px 10px 8px 10px;
        background:rgba(10,17,29,0.38);
        border:1px solid rgba(56,189,248,0.08);
        box-shadow:none;
        margin-bottom:12px;
    ">
        <div style="
            font-size:16px;
            font-weight:700;
            margin-bottom:12px;
            color:#F8FAFC;
        ">{titulo}</div>

        <div style="
            display:flex;
            align-items:flex-end;
            gap:10px;
            height:{altura}px;
            padding:10px 8px 38px 8px;
            border-bottom:1px solid rgba(148,163,184,0.18);
            overflow-x:auto;
        ">
    """

    # Barras lado a lado por categoria
    for categoria in categorias:
        registros_cat = longo[longo["Categoria"] == categoria]

        html += f"""
        <div style="
            min-width:{max(48, 720 // max(len(categorias),1))}px;
            height:100%;
            display:flex;
            flex-direction:column;
            justify-content:flex-end;
            align-items:center;
        ">
            <div style="
                height:100%;
                width:100%;
                display:flex;
                justify-content:center;
                align-items:flex-end;
                gap:4px;
                padding-top:38px;
                box-sizing:border-box;
            ">
        """

        largura_barra = max(28, min(72, 100 // max(len(series), 1)))

        for serie in series:
            linha = registros_cat[registros_cat["Serie"] == serie]

            if linha.empty:
                valor = 0
            else:
                valor = float(linha.iloc[0]["Valor"])

            percentual = (valor / max_valor) * 100 if max_valor else 0

            # Mantém uma margem segura no topo para o rótulo numérico.
            # Assim o número nunca fica cortado quando a barra é a maior.
            altura_barra = max(2, min(86, percentual))

            # Cores sem necessidade de configurar Matplotlib/Plotly.
            # Apenas diferencia séries visualmente.
            serie_cor = serie if serie else categoria
            fundo = cor_serie(
                serie_cor,
                series.index(serie) if serie in series else 0,
            )

            texto = (
                f"{int(valor):,}".replace(",", ".")
                if float(valor).is_integer()
                else f"{valor:.1f}"
            )

            html += f"""
            <div style="
                height:{altura_barra}%;
                width:{largura_barra}px;
                min-height:7px;
                background:{fundo};
                border-radius:5px 5px 0 0;
                position:relative;
                display:flex;
                justify-content:center;
                align-items:flex-start;
            ">
                <span style="
                    position:absolute;
                    top:-29px;
                    font-size:21px;
                    font-weight:900;
                    color:#F8FAFC;
                    text-shadow:0 2px 8px rgba(0,0,0,0.65);
                    white-space:nowrap;
                    line-height:1;
                    z-index:20;
                    overflow:visible;
                ">{texto}</span>
            </div>
            """

        html += f"""
            </div>

            <div style="
                font-size:11px;
                color:#9FB1C6;
                margin-top:8px;
                white-space:nowrap;
            ">{categoria}</div>
        </div>
        """

    html += """
        </div>
    """

    if len(series) > 1 and any(str(x) for x in series):
        html += """
        <div style="
            display:flex;
            gap:22px;
            margin-top:12px;
            font-size:14px;
            font-weight:800;
            color:#F8FAFC;
        ">
        """

        for i, serie in enumerate(series):
            if not serie:
                continue

            fundo = cor_serie(serie, i)

            html += f"""
            <span>
                <span style="
                    display:inline-block;
                    width:11px;
                    height:11px;
                    background:{fundo};
                    border-radius:2px;
                    margin-right:5px;
                "></span>
                {serie}
            </span>
            """

        html += "</div>"

    html += "</div>"

    components.html(html, height=altura + 125, scrolling=False)


# ============================================================
# CARGA
# ============================================================

if not ARQ_ANALISE.exists():
    st.error(
        "Não encontrei analise_reservas_apartamentos.json. "
        "Execute primeiro analise_reservas_apartamentos.py."
    )
    st.stop()

with open(ARQ_ANALISE, encoding="utf-8") as f:
    analise = json.load(f)

df = pd.DataFrame(analise.get("reservas", []))
aptos = pd.DataFrame(analise.get("apartamentos", []))

if df.empty:
    st.warning("Não existem reservas vinculadas aos apartamentos da operação.")
    st.stop()

for col in [
    "ano",
    "mes",
    "codigo_apto",
    "responsavel_apto",
    "responsavel_reserva",
    "canal",
]:
    if col in df.columns:
        df[col] = df[col].astype(str)

df["ano_num"] = pd.to_numeric(df["ano"], errors="coerce")
df["mes_num"] = pd.to_numeric(
    df["mes"].str[-2:],
    errors="coerce",
)

df["checkin"] = pd.to_datetime(df["checkin"], errors="coerce")
df["checkout"] = pd.to_datetime(df["checkout"], errors="coerce")

# Detecta status de cancelamento somente se a base fornecer essa informação.
COLUNA_STATUS = next(
    (
        c for c in [
            "status",
            "reservation_status",
            "booking_status",
            "situacao",
            "estado",
        ]
        if c in df.columns
    ),
    None,
)

if COLUNA_STATUS:
    df["status_dashboard"] = df[COLUNA_STATUS].astype(str)
else:
    df["status_dashboard"] = ""

datas_criacao = pd.to_datetime(
    df["mes"].astype(str) + "-01",
    errors="coerce",
)
max_mes_historico = datas_criacao.max()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("Filtros")

anos_disponiveis = sorted(
    [int(x) for x in df["ano_num"].dropna().unique()]
)

anos_selecionados = st.sidebar.multiselect(
    "Ano da visão geral",
    anos_disponiveis,
    default=anos_disponiveis,
)

nomes_meses = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}

meses_disponiveis = sorted(
    [int(x) for x in df["mes_num"].dropna().unique()]
)

meses_selecionados = st.sidebar.multiselect(
    "Mês da visão geral",
    meses_disponiveis,
    default=meses_disponiveis,
    format_func=lambda x: nomes_meses[x],
)

responsaveis = sorted(df["responsavel_apto"].dropna().unique())

responsaveis_sel = st.sidebar.multiselect(
    "Responsável pelo apartamento",
    responsaveis,
    default=responsaveis,
)

canais = sorted(df["canal"].dropna().unique())

canais_sel = st.sidebar.multiselect(
    "Canal da reserva",
    canais,
    default=canais,
)

aptos_disponiveis = sorted(df["codigo_apto"].dropna().unique())

aptos_sel = st.sidebar.multiselect(
    "Apartamento",
    aptos_disponiveis,
    default=[],
    placeholder="Todos",
)

st.sidebar.divider()

st.sidebar.caption(
    "Exemplo: Agosto + Setembro com 2025 + 2026 "
    "compara cada mês entre os dois anos."
)


# ============================================================
# FILTROS
# ============================================================

df_filtrado = df.copy()

if anos_selecionados:
    df_filtrado = df_filtrado[
        df_filtrado["ano_num"].isin(anos_selecionados)
    ]
else:
    df_filtrado = df_filtrado.iloc[0:0]

if meses_selecionados:
    df_filtrado = df_filtrado[
        df_filtrado["mes_num"].isin(meses_selecionados)
    ]
else:
    df_filtrado = df_filtrado.iloc[0:0]

if responsaveis_sel:
    df_filtrado = df_filtrado[
        df_filtrado["responsavel_apto"].isin(responsaveis_sel)
    ]

if canais_sel:
    df_filtrado = df_filtrado[
        df_filtrado["canal"].isin(canais_sel)
    ]

if aptos_sel:
    df_filtrado = df_filtrado[
        df_filtrado["codigo_apto"].isin(aptos_sel)
    ]


# Base específica para comparação 2025 x 2026.
df_comparacao = df.copy()

if meses_selecionados:
    df_comparacao = df_comparacao[
        df_comparacao["mes_num"].isin(meses_selecionados)
    ]
else:
    df_comparacao = df_comparacao.iloc[0:0]

if responsaveis_sel:
    df_comparacao = df_comparacao[
        df_comparacao["responsavel_apto"].isin(responsaveis_sel)
    ]

if canais_sel:
    df_comparacao = df_comparacao[
        df_comparacao["canal"].isin(canais_sel)
    ]

if aptos_sel:
    df_comparacao = df_comparacao[
        df_comparacao["codigo_apto"].isin(aptos_sel)
    ]


# ============================================================
# CABEÇALHO
# ============================================================

st.markdown(
    '<div class="tamu-title">'
    '📊 TAMU <span class="tamu-title-accent">—</span> Dashboard de Reservas'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="tamu-subtitle">'
    "Volume de reservas • apartamentos • canais • responsáveis"
    "</div>",
    unsafe_allow_html=True,
)

meses_texto = ", ".join(
    nomes_meses[x]
    for x in meses_selecionados
)

anos_texto = ", ".join(
    str(x)
    for x in anos_selecionados
)

st.markdown(
    f'<div style="color:#5E7894;font-size:0.78rem;'
    f'margin-bottom:10px;">'
    f'Visão atual: {meses_texto or "nenhum mês"} • '
    f'{anos_texto or "nenhum ano"}'
    f'</div>',
    unsafe_allow_html=True,
)


# ============================================================
# KPIs
# ============================================================

total_operacao = 72

aptos_com_reserva = df_filtrado["codigo_apto"].nunique()
aptos_sem_reserva = max(
    total_operacao - aptos_com_reserva,
    0,
)

reservas_thiago = df_filtrado.loc[
    df_filtrado["responsavel_reserva"] == "Thiago"
].shape[0]

reservas_evellyn = df_filtrado.loc[
    df_filtrado["responsavel_reserva"] == "Evellyn"
].shape[0]

k1, k2, k3, k4, k5, k6 = st.columns(6)

k1.metric(
    "Reservas",
    f"{len(df_filtrado):,}".replace(",", "."),
)

k2.metric(
    "Apartamentos",
    "72",
)

k3.metric(
    "Com reservas",
    str(aptos_com_reserva),
)

k4.metric(
    "Sem reservas",
    str(aptos_sem_reserva),
)

k5.metric(
    "Reservas Thiago",
    f"{reservas_thiago:,}".replace(",", "."),
)

k6.metric(
    "Reservas Evellyn",
    f"{reservas_evellyn:,}".replace(",", "."),
)

st.divider()


# ============================================================
# 1. EVOLUÇÃO
# ============================================================

st.markdown('<div class="tamu-section">1. Evolução das reservas</div>', unsafe_allow_html=True)

mensal = (
    df_filtrado
    .groupby(["ano_num", "mes_num"])
    .size()
    .reset_index(name="Reservas")
)

if not mensal.empty:

    mensal["Ano"] = mensal["ano_num"].astype(int).astype(str)
    mensal["Mês"] = mensal["mes_num"].astype(int)

    grafico_mensal = mensal.pivot_table(
        index="Mês",
        columns="Ano",
        values="Reservas",
        aggfunc="sum",
        fill_value=0,
    )

    grafico_mensal = grafico_mensal.reindex(
        meses_selecionados,
        fill_value=0,
    )

    grafico_mensal.index = [
        nomes_meses[x]
        for x in grafico_mensal.index
    ]

    grafico_barras_html(
        grafico_mensal,
        titulo="Reservas por mês",
        ylabel="Quantidade de reservas",
    )


# ============================================================
# 2. COMPARAÇÃO 2025 X 2026
# ============================================================

st.markdown('<div class="tamu-section">2. Comparação mensal — 2025 × 2026</div>', unsafe_allow_html=True)

df_comp_periodo = df_comparacao[
    df_comparacao["ano_num"].isin([2025, 2026])
].copy()

comp = (
    df_comp_periodo
    .groupby(["mes_num", "ano_num"])
    .size()
    .unstack(level=1, fill_value=0)
)

for ano in [2025, 2026]:
    if ano not in comp.columns:
        comp[ano] = 0

comp = comp.reindex(
    meses_selecionados,
    fill_value=0,
)

comp = comp[[2025, 2026]]

comp.columns = [
    "2025",
    "2026",
]

# Não transformar meses futuros em -100%.
if max_mes_historico.year == 2026:
    mes_limite_2026 = max_mes_historico.month

    for mes in comp.index:
        if mes > mes_limite_2026:
            comp.loc[mes, "2026"] = pd.NA

comp["Variação"] = pd.NA

for mes in comp.index:

    v25 = comp.loc[mes, "2025"]
    v26 = comp.loc[mes, "2026"]

    if pd.isna(v26) or v25 == 0:
        comp.loc[mes, "Variação"] = pd.NA
    else:
        comp.loc[mes, "Variação"] = (
            (v26 - v25) / v25 * 100
        )

comp.index = [
    nomes_meses[x]
    for x in comp.index
]

grafico_barras_html(
    comp[["2025", "2026"]],
    titulo="Comparação 2025 × 2026",
    ylabel="Quantidade de reservas",
)

tabela_comp = comp.copy()

tabela_comp["Variação"] = tabela_comp[
    "Variação"
].apply(
    lambda x:
        "N/D"
        if pd.isna(x)
        else f"{x:+.1f}%"
)

st.dataframe(
    tabela_comp,
    use_container_width=True,
)

total_2025 = df_comp_periodo[
    df_comp_periodo["ano_num"] == 2025
].shape[0]

total_2026 = df_comp_periodo[
    df_comp_periodo["ano_num"] == 2026
].shape[0]

r1, r2, r3 = st.columns(3)

r1.metric(
    "Período selecionado — 2025",
    f"{total_2025:,}".replace(",", "."),
)

r2.metric(
    "Período selecionado — 2026",
    f"{total_2026:,}".replace(",", "."),
)

if total_2025 > 0:
    variacao_periodo = (
        (total_2026 - total_2025)
        / total_2025
        * 100
    )

    r3.metric(
        "Variação do período",
        f"{variacao_periodo:+.1f}%",
    )
else:
    r3.metric(
        "Variação do período",
        "N/D",
    )

st.caption(
    "A comparação utiliza somente os meses selecionados no filtro lateral."
)

st.caption(
    "N/D = mês ainda não disponível no histórico atual. "
    "O histórico utilizado vai até 28/09/2026."
)


# ============================================================
# 3. CANAIS E RESPONSÁVEIS
# ============================================================

st.markdown('<div class="tamu-section">3. Canais e responsáveis</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)

with c1:

    st.subheader("Reservas por canal")

    canal_df = (
        df_filtrado
        .groupby("canal")
        .size()
        .rename("Reservas")
        .sort_values(ascending=False)
    )

    canal_grafico = canal_df.copy()
    canal_grafico.index = [
        str(x) for x in canal_grafico.index
    ]
    grafico_barras_html(
        canal_grafico,
        titulo="Reservas por canal",
        ylabel="Quantidade",
    )

    st.dataframe(
        canal_df.reset_index(),
        use_container_width=True,
        hide_index=True,
    )

    if COLUNA_STATUS:
        cancelados = df_filtrado[
            df_filtrado["status_dashboard"]
            .str.lower()
            .str.contains("cancel", na=False)
        ]

        if not cancelados.empty:
            st.caption(
                f"Canceladas identificadas na base: "
                f"{len(cancelados):,}".replace(",", ".")
            )
        else:
            st.caption(
                "Nenhuma reserva cancelada identificada no filtro atual."
            )
    else:
        st.caption(
            "Cancelamentos: a base atual não fornece um campo de status."
        )


with c2:

    st.subheader("Responsável pela reserva")

    resp_reserva_df = (
        df_filtrado
        .groupby("responsavel_reserva")
        .size()
        .rename("Reservas")
        .sort_values(ascending=False)
    )

    grafico_barras_html(
        resp_reserva_df,
        titulo="Responsável pela reserva",
        ylabel="Quantidade",
    )

    st.dataframe(
        resp_reserva_df.reset_index(),
        use_container_width=True,
        hide_index=True,
    )


st.subheader(
    "Responsável pelo apartamento"
)

resp_apto_df = (
    df_filtrado
    .groupby("responsavel_apto")
    .size()
    .rename("Reservas")
    .sort_values(ascending=False)
)

grafico_barras_html(
    resp_apto_df,
    titulo="Responsável pelo apartamento",
    ylabel="Quantidade",
)


cruzamento = pd.crosstab(
    df_filtrado["responsavel_apto"],
    df_filtrado["canal"],
)

st.subheader(
    "Responsável pelo apartamento × canal"
)

st.dataframe(
    cruzamento,
    use_container_width=True,
)


# ============================================================
# 4. CHECK-INS / CHECK-OUTS
# ============================================================

st.markdown('<div class="tamu-section">4. Check-ins e check-outs</div>', unsafe_allow_html=True)

eventos = []

ci = df_filtrado.dropna(
    subset=["checkin"]
).copy()

if not ci.empty:

    ci["mes_evento"] = (
        ci["checkin"]
        .dt.to_period("M")
        .astype(str)
    )

    for mes, qtd in (
        ci.groupby("mes_evento")
        .size()
        .items()
    ):
        eventos.append({
            "Mês": mes,
            "Tipo": "Check-in",
            "Quantidade": qtd,
        })


co = df_filtrado.dropna(
    subset=["checkout"]
).copy()

if not co.empty:

    co["mes_evento"] = (
        co["checkout"]
        .dt.to_period("M")
        .astype(str)
    )

    for mes, qtd in (
        co.groupby("mes_evento")
        .size()
        .items()
    ):
        eventos.append({
            "Mês": mes,
            "Tipo": "Check-out",
            "Quantidade": qtd,
        })


if eventos:

    eventos_df = pd.DataFrame(eventos)

    eventos_pivot = eventos_df.pivot_table(
        index="Mês",
        columns="Tipo",
        values="Quantidade",
        aggfunc="sum",
        fill_value=0,
    )

    st.line_chart(
        eventos_pivot,
        use_container_width=True,
    )

    st.dataframe(
        eventos_pivot,
        use_container_width=True,
    )

else:

    st.info(
        "Não há datas de check-in/check-out disponíveis."
    )


# ============================================================
# 5. PERFORMANCE
# ============================================================

st.markdown('<div class="tamu-section">5. Performance dos apartamentos</div>', unsafe_allow_html=True)

perf = (
    df_filtrado
    .groupby(
        [
            "codigo_apto",
            "responsavel_apto",
        ]
    )
    .size()
    .reset_index(name="Reservas")
    .sort_values(
        "Reservas",
        ascending=False,
    )
)

st.subheader(
    "Ranking por volume de reservas"
)

st.dataframe(
    perf,
    use_container_width=True,
    hide_index=True,
)


apt_comp = (
    df_comparacao[
        df_comparacao["ano_num"].isin(
            [2025, 2026]
        )
    ]
    .groupby(
        [
            "codigo_apto",
            "responsavel_apto",
            "ano_num",
        ]
    )
    .size()
    .unstack(fill_value=0)
)

for ano in [2025, 2026]:

    if ano not in apt_comp.columns:
        apt_comp[ano] = 0

apt_comp = apt_comp[
    [2025, 2026]
].reset_index()

apt_comp.columns = [
    "Apartamento",
    "Responsável",
    "2025",
    "2026",
]

apt_comp["Variação"] = pd.NA

for i, row in apt_comp.iterrows():

    if row["2025"] != 0:

        apt_comp.loc[i, "Variação"] = (
            (row["2026"] - row["2025"])
            / row["2025"]
            * 100
        )

apt_comp_display = apt_comp.copy()

apt_comp_display["Variação"] = (
    apt_comp_display["Variação"]
    .apply(
        lambda x:
            "N/D"
            if pd.isna(x)
            else f"{x:+.1f}%"
    )
)

st.subheader(
    "Cada apartamento — 2025 × 2026"
)

st.dataframe(
    apt_comp_display.sort_values(
        ["2026", "2025"],
        ascending=False,
    ),
    use_container_width=True,
    hide_index=True,
)


# ============================================================
# ============================================================
# 6. APARTAMENTOS SEM RESERVAS NO PERÍODO
# ============================================================

st.markdown(
    '<div class="tamu-section">6. Apartamentos sem reservas no período</div>',
    unsafe_allow_html=True,
)

if not aptos.empty and "codigo_apto" in aptos.columns:

    cadastro = aptos.copy()

    cadastro["codigo_apto"] = (
        cadastro["codigo_apto"].astype(str).str.strip()
    )

    reservas_por_apto = (
        df_filtrado
        .groupby("codigo_apto")
        .size()
        .rename("reservas_periodo")
    )

    cadastro = cadastro.join(
        reservas_por_apto,
        on="codigo_apto",
    )

    cadastro["reservas_periodo"] = (
        cadastro["reservas_periodo"]
        .fillna(0)
        .astype(int)
    )

    sem_reservas = cadastro[
        cadastro["reservas_periodo"] == 0
    ].copy()

    sem_reservas = sem_reservas.sort_values(
        ["responsavel_apto", "codigo_apto"]
    )

    qtd_sem_reserva = len(sem_reservas)

    qtd_thiago_sem = int(
        (sem_reservas["responsavel_apto"] == "Thiago").sum()
    )

    qtd_evellyn_sem = int(
        (sem_reservas["responsavel_apto"] == "Evellyn").sum()
    )

    s1, s2, s3 = st.columns(3)

    s1.metric(
        "Apartamentos sem reservas",
        str(qtd_sem_reserva),
    )

    s2.metric(
        "Sem reservas — Thiago",
        str(qtd_thiago_sem),
    )

    s3.metric(
        "Sem reservas — Evellyn",
        str(qtd_evellyn_sem),
    )

    if qtd_sem_reserva == 0:

        st.success(
            "Todos os apartamentos receberam pelo menos uma reserva "
            "no período e filtros selecionados."
        )

    else:

        st.markdown(
            f"""
            <div style="
                margin:12px 0 16px 0;
                padding:14px 16px;
                border-left:3px solid #EF4444;
                background:rgba(239,68,68,0.055);
                border-radius:6px;
                color:#CBD5E1;
            ">
                <strong style="color:#F87171;">
                    {qtd_sem_reserva} apartamento(s)
                </strong>
                não receberam nenhuma reserva dentro do período e filtros
                selecionados.
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_t, col_e = st.columns(2)

        with col_t:

            sem_t = sem_reservas[
                sem_reservas["responsavel_apto"] == "Thiago"
            ]

            st.markdown(
                '<div style="font-size:1.05rem;font-weight:800;'
                'color:#F8FAFC;margin-bottom:8px;">'
                '🔵 Thiago'
                '</div>',
                unsafe_allow_html=True,
            )

            if sem_t.empty:

                st.caption(
                    "Nenhum apartamento do Thiago está sem reserva."
                )

            else:

                chips = ""

                for _, row in sem_t.iterrows():

                    codigo = row["codigo_apto"]

                    chips += f"""
                    <span style="
                        display:inline-block;
                        padding:7px 10px;
                        margin:0 6px 6px 0;
                        background:#101D30;
                        border:1px solid rgba(35,139,255,0.35);
                        border-radius:6px;
                        color:#E5F2FF;
                        font-weight:700;
                        font-size:0.86rem;
                    ">
                        {codigo}
                    </span>
                    """

                st.markdown(
                    chips,
                    unsafe_allow_html=True,
                )

        with col_e:

            sem_e = sem_reservas[
                sem_reservas["responsavel_apto"] == "Evellyn"
            ]

            st.markdown(
                '<div style="font-size:1.05rem;font-weight:800;'
                'color:#F8FAFC;margin-bottom:8px;">'
                '🟣 Evellyn'
                '</div>',
                unsafe_allow_html=True,
            )

            if sem_e.empty:

                st.caption(
                    "Nenhum apartamento da Evellyn está sem reserva."
                )

            else:

                chips = ""

                for _, row in sem_e.iterrows():

                    codigo = row["codigo_apto"]

                    chips += f"""
                    <span style="
                        display:inline-block;
                        padding:7px 10px;
                        margin:0 6px 6px 0;
                        background:#101D30;
                        border:1px solid rgba(139,92,246,0.38);
                        border-radius:6px;
                        color:#F1EAFF;
                        font-weight:700;
                        font-size:0.86rem;
                    ">
                        {codigo}
                    </span>
                    """

                st.markdown(
                    chips,
                    unsafe_allow_html=True,
                )

        with st.expander(
            "Ver tabela detalhada dos apartamentos sem reservas"
        ):

            tabela_sem = sem_reservas.copy()

            colunas = [
                c for c in [
                    "codigo_apto",
                    "responsavel_apto",
                    "encontrado_stays",
                ]
                if c in tabela_sem.columns
            ]

            tabela_sem = tabela_sem[colunas].copy()

            tabela_sem = tabela_sem.rename(columns={
                "codigo_apto": "Apartamento",
                "responsavel_apto": "Responsável",
                "encontrado_stays": "Ativo no Stays",
            })

            if "Ativo no Stays" in tabela_sem.columns:
                tabela_sem["Ativo no Stays"] = (
                    tabela_sem["Ativo no Stays"]
                    .map({True: "Sim", False: "Não"})
                    .fillna("Não informado")
                )

            st.dataframe(
                tabela_sem,
                use_container_width=True,
                hide_index=True,
            )

else:

    st.info(
        "Não foi possível cruzar o cadastro dos apartamentos "
        "com as reservas do período."
    )


# 7. CADASTRO DA OPERAÇÃO
# ============================================================

st.markdown('<div class="tamu-section">7. Cadastro da operação</div>', unsafe_allow_html=True)

if not aptos.empty:

    cad = aptos.copy()

    if "encontrado_stays" in cad.columns:

        ativos_stays = int(
            cad["encontrado_stays"].sum()
        )

        fora_stays = (
            len(cad)
            - ativos_stays
        )

    else:

        ativos_stays = 0
        fora_stays = 0

    a1, a2, a3, a4 = st.columns(4)

    a1.metric(
        "Total da operação",
        str(len(cad)),
    )

    a2.metric(
        "Thiago",
        str(
            (
                cad["responsavel_apto"]
                == "Thiago"
            ).sum()
        ),
    )

    a3.metric(
        "Evellyn",
        str(
            (
                cad["responsavel_apto"]
                == "Evellyn"
            ).sum()
        ),
    )

    a4.metric(
        "Ativos no Stays",
        str(ativos_stays),
    )

    st.caption(
        f"{fora_stays} apartamentos da nossa lista "
        "não estão entre os imóveis ativos atualmente "
        "retornados pelo Stays."
    )


# ============================================================
# REGRAS
# ============================================================

st.divider()

st.markdown(
    "**Regras utilizadas no painel**"
)

st.write(
    "• Booking.com → responsável pela reserva = Evellyn."
)

st.write(
    "• Airbnb → responsável pela reserva = responsável pelo apartamento."
)

st.write(
    "• Website e reservas sem canal → Não definido."
)

st.write(
    "• 161154 está ativo no Stays, mas não pertence "
    "às 72 unidades da operação."
)

st.write(
    "• Nenhum indicador financeiro é utilizado."
)

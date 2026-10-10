import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import preprocessament as pp

st.set_page_config(page_title="Alta velocitat: Renfe, Iryo i Ouigo", layout="wide")

COLORS = {"Renfe": "#b0409a", "Iryo": "#e5202e", "Ouigo": "#1a9db7"}

# Depenent de la mesura seleccionada, quina columna del DataFrame s'ha d'agafar, com s'ha de mostrar a l'eix vertical i com s'ha de formatar el valor.
MESURES = {
    "Viatgers": {"col": "Viatgers", "eix": "Viatgers (nombre)", "fmt": ",.0f", "suf": ""},
    "Quota de mercat (%)": {"col": "Quota", "eix": "Quota de mercat (%)", "fmt": ".1f", "suf": " %"},
    "Ocupació (%)": {"col": "Ocupacio", "eix": "Ocupació (% de places ocupades)", "fmt": ".1f", "suf": " %"},
}

EIX = dict(showgrid=True, gridcolor="rgba(128,128,128,0.15)", zeroline=False,
           linecolor="rgba(128,128,128,0.4)", ticks="outside")
LAYOUT = dict(template="simple_white", margin=dict(l=10, r=10, t=10, b=10),
              font=dict(size=14), hoverlabel=dict(font_size=14))


@st.cache_data
def dades() -> pd.DataFrame:
    """Pipeline de la Fase 2 (en memòria cau: només es calcula un cop)."""
    return pp.preparar()


def format_valor(v: float, m: dict) -> str:
    """Format català: punt de milers i coma decimal."""
    txt = format(v, m["fmt"])
    return txt.replace(",", "X").replace(".", ",").replace("X", ".") + m["suf"]



st.title("Viatgers d'alta velocitat a Espanya: Renfe, Iryo i Ouigo")
st.caption("Cinc corredors principals · dades trimestrals 2023–2026 · Font: CNMC (CNMCData)")

# Dibuixa el selector de mesura
nom_mesura = st.radio(
    "Mesura", list(MESURES), horizontal=True,
    help="Viatgers: valor absolut. Quota: % del total de les tres empreses. "
         "Ocupació: % de les places ofertades que s'omplen.",
)

m = MESURES[nom_mesura]
df = dades()
trimestres = list(df["Etiqueta"].drop_duplicates())

# Trimestre seleccionat per defecte: T3 2025, el que va fer servir el gràfic
# original (les seves xifres coincideixen amb aquest trimestre, no amb tot 2025).
if "trimestre" not in st.session_state:
    st.session_state.trimestre = "T3 2025"



"""
    Gràfic 1; mostr a l'evolució de la mesura seleccionada per trimestre, amb línies i punts interactius.

"""
st.subheader(f"{nom_mesura} per trimestre")
st.caption("Passa el ratolí per veure el valor exacte · Mou el control lliscant per canviar el trimestre que es compara a sota")

# Reordena la llegenda segons la mitjana de la mesura, de més gran a més petita
ordre_llegenda = (df.groupby("Empresa")[m["col"]].mean()
                  .sort_values(ascending=False).index.tolist())

fig_l = go.Figure()
for i, emp in enumerate(ordre_llegenda):
    d = df[df["Empresa"] == emp]
    fig_l.add_trace(go.Scatter(
        x=d["Data"], y=d[m["col"]], name=emp, mode="lines+markers",
        line=dict(color=COLORS[emp], width=2.5),
        marker=dict(size=9, color=COLORS[emp], line=dict(width=2, color="white")),
        customdata=d[["Etiqueta"]],
        hovertemplate=(f"<b>{emp}</b> · %{{customdata[0]}}<br>"
                       f"{nom_mesura}: %{{y:{m['fmt']}}}{m['suf']}<extra></extra>"),  # Es el cuadrante que apareix al passar el ratolí per sobre un punt
        legendrank=i,
    ))

# Marca el trimestre seleccionat amb una línia vertical suau
data_sel = df.loc[df["Etiqueta"] == st.session_state.trimestre, "Data"]
if not data_sel.empty:
    centre = data_sel.iloc[0]
    fig_l.add_vrect(
        x0=centre - pd.Timedelta(days=40), x1=centre + pd.Timedelta(days=40),
        fillcolor="rgba(128,128,128,0.22)", line_width=0, layer="below",
        annotation_text=st.session_state.trimestre, annotation_position="top",
        annotation_font_size=13,
    )
 
fig_l.update_layout(
    **LAYOUT, height=430, hovermode="closest", separators=",.",
       legend=dict(orientation="h", y=1.08, x=0, title=None,
               itemclick=False, itemdoubleclick=False),
)
eix_x = df.drop_duplicates("Data")
fig_l.update_xaxes(**{**EIX, "showgrid": False}, title=None,  # sense graella vertical
                   tickvals=eix_x["Data"], ticktext=eix_x["Etiqueta"], tickangle=-45)
fig_l.update_yaxes(**EIX, title=m["eix"], rangemode="tozero",  # eix sempre des de 0
                   range=[0, 100] if m["col"] == "Ocupacio" else None)
 
st.plotly_chart(fig_l, use_container_width=True, key="linies")

"""
    Gràfic 2; comparació de la mesura seleccionada entre les tres empreses per al trimestre seleccionat, amb barres i valors exactes a sobre.
"""
st.select_slider("Trimestre", options=trimestres, key="trimestre")  # alternativa sense ratolí

sel = df[df["Etiqueta"] == st.session_state.trimestre]
sel = pp.ordenar(sel, m["col"])  # ordre per la mesura, no alfabètic

st.subheader(f"{nom_mesura} · {st.session_state.trimestre}")

fig_b = go.Figure(go.Bar(
    x=sel["Empresa"], y=sel[m["col"]],
    marker=dict(color=[COLORS[e] for e in sel["Empresa"]], cornerradius=4),
    text=[format_valor(v, m) for v in sel[m["col"]]],
    textposition="outside", cliponaxis=False,
    hovertemplate=f"<b>%{{x}}</b><br>{nom_mesura}: %{{y:{m['fmt']}}}{m['suf']}<extra></extra>",
))
fig_b.update_layout(**LAYOUT, height=380, showlegend=False, bargap=0.45, separators=",.")
fig_b.update_xaxes(**{**EIX, "showgrid": False}, title=None)  # sense graella vertical
fig_b.update_yaxes(**EIX, title=m["eix"], rangemode="tozero",  # barres sempre des de 0
                   range=[0, 100] if m["col"] == "Ocupacio" else None)
st.plotly_chart(fig_b, use_container_width=True, key="barres")

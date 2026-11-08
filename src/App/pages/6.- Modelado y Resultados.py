"""
Página 6 · Modelado y Resultados (Avance 3)

Muestra el modelado probabilístico de la espera para una audiencia:
planteamiento, resultados contra líneas base, simulador de una causa y
comparador de tribunales con mapa.

La página NO entrena nada: solo lee los artefactos de `models/`, generados por
el notebook `04_Modelado_audienciasparquet.ipynb` (o `python src/Modelado/entrenar.py`).
Nota: `st.set_page_config` ya se define en Inicio.py.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# -----------------------------------------------------------------------------
# Constantes visuales
# -----------------------------------------------------------------------------
COLOR = "#2E6F95"
COLOR_TRAMO = {"Rápido": "#2A9D8F", "Estándar": "#E9B949", "Demora": "#D1495B"}
COLOR_SEVERA = "#7F1D1D"
ESCALA_ESPERA = "YlOrRd"  # más intenso = más espera
PLANTILLA = "plotly_white"

_VER = tuple(int(x) for x in st.__version__.split(".")[:2])
ANCHO = {"width": "stretch"} if _VER >= (1, 50) else {"use_container_width": True}

# Ubicación y provincia de cada tribunal (Región de Valparaíso)
TRIBUNALES = {
    "JUZGADO DE FAMILIA DE VALPARAISO": ("Valparaíso", "Familia", "Valparaíso", -33.0458, -71.6197),
    "JUZGADO DE FAMILIA DE VINA DEL MAR": ("Viña del Mar", "Familia", "Valparaíso", -33.0246, -71.5518),
    "JUZGADO DE FAMILIA DE CASABLANCA": ("Casablanca", "Familia", "Valparaíso", -33.3196, -71.4103),
    "JUZGADO DE LETRAS Y GARANTIA DE QUINTERO": ("Quintero", "Letras y Garantía", "Valparaíso", -32.7794, -71.5266),
    "JUZGADO DE FAMILIA DE QUILPUE": ("Quilpué", "Familia", "Marga Marga", -33.0475, -71.4425),
    "JUZGADO DE FAMILIA DE VILLA ALEMANA": ("Villa Alemana", "Familia", "Marga Marga", -33.0428, -71.3733),
    "JUZGADO DE FAMILIA DE LIMACHE": ("Limache", "Familia", "Marga Marga", -32.9850, -71.2756),
    "JUZGADO DE FAMILIA DE QUILLOTA": ("Quillota", "Familia", "Quillota", -32.8834, -71.2488),
    "JUZGADO DE FAMILIA DE LA LIGUA": ("La Ligua", "Familia", "Petorca", -32.4524, -71.2311),
    "JUZGADO DE LETRAS Y GARANTIA DE PETORCA": ("Petorca", "Letras y Garantía", "Petorca", -32.2525, -70.9333),
    "JUZGADO DE FAMILIA DE SAN FELIPE": ("San Felipe", "Familia", "San Felipe de Aconcagua", -32.7507, -70.7251),
    "JUZGADO DE LETRAS Y GARANTIA DE PUTAENDO": ("Putaendo", "Letras y Garantía", "San Felipe de Aconcagua", -32.6278, -70.7167),
    "JUZGADO DE FAMILIA DE LOS ANDES": ("Los Andes", "Familia", "Los Andes", -32.8337, -70.5983),
    "JUZGADO DE FAMILIA DE SAN ANTONIO": ("San Antonio", "Familia", "San Antonio", -33.5933, -71.6217),
    "JUZGADO DE LETRAS Y GARANTIA DE ISLA DE PASCUA": ("Isla de Pascua", "Letras y Garantía", "Isla de Pascua", -27.1500, -109.4333),
}
FUERA_DEL_MAPA = "JUZGADO DE LETRAS Y GARANTIA DE ISLA DE PASCUA"
METRICAS_MAPA = {
    "Mediana de espera (días)": ("mediana", "{:.0f} d"),
    "Probabilidad de demora (> 30 d)": ("p_demora", "{:.0%}"),
    "Probabilidad de espera severa (> 60 d)": ("p_severa", "{:.0%}"),
}


def corto(trib: str) -> str:
    return TRIBUNALES.get(trib, (trib.title(),))[0]


TILDES = {"continuacion": "continuación", "proteccion": "protección", "adopcion": "adopción",
          "transaccion": "transacción", "genero": "género", "mediacion": "mediación", "oposicion": "oposición",
          "revision": "revisión", "suspension": "suspensión", "citacion": "citación"}


def bonito(txt: str) -> str:
    palabras = [TILDES.get(p, p) for p in txt.lower().split()]
    return " ".join(palabras).capitalize()


# -----------------------------------------------------------------------------
# Carga de artefactos
# -----------------------------------------------------------------------------
def _buscar_models() -> Path | None:
    base = Path(__file__).resolve()
    candidatos = [Path.cwd() / "models"] + [p / "models" for p in base.parents[:5]]
    return next((c for c in candidatos if (c / "resultados_modelado.json").exists()), None)


@st.cache_data(show_spinner="Cargando resultados del modelo...")
def cargar():
    carpeta = _buscar_models()
    if carpeta is None:
        return None, None
    R = json.loads((carpeta / "resultados_modelado.json").read_text(encoding="utf-8"))
    g = pd.read_parquet(carpeta / "predicciones_tribunales.parquet")
    g["TRIB_CORTO"] = g["TRIBUNAL"].map(corto)
    g["PROVINCIA"] = g["TRIBUNAL"].map(lambda t: TRIBUNALES.get(t, ("", "", "—"))[2])
    g["LAT"] = g["TRIBUNAL"].map(lambda t: TRIBUNALES.get(t, (0, 0, 0, np.nan))[3])
    g["LON"] = g["TRIBUNAL"].map(lambda t: TRIBUNALES.get(t, (0, 0, 0, 0, np.nan))[4])
    return R, g


R, G = cargar()
st.title("Modelado y Resultados")
if R is None:
    st.error("No se encontraron los artefactos del modelo en `models/`. "
             "Ejecuta el notebook `04_Modelado_audienciasparquet.ipynb` o `python src/Modelado/entrenar.py`.")
    st.stop()

T, S = R["tramo"], R["severa"]
TAB_T, TAB_S = pd.DataFrame(T["tabla"]), pd.DataFrame(S["tabla"])
EL_T, EL_S = T["eleccion"], S["eleccion"]
PRUEBA, VALID = "Prueba 2024–2025", "Validación 2023"


MODELOS = ["Bayesiano jerárquico", "Regresión logística", "HistGradientBoosting"]
CORTO_MODELO = {"Bayesiano jerárquico": "Bayesiano", "Regresión logística": "Logística",
                "HistGradientBoosting": "Boosting"}


def fila(tabla, receta_et, modelo, calibrado, conjunto=PRUEBA):
    t = tabla[(tabla["receta"] == receta_et) & (tabla["modelo"] == modelo) & (tabla["conjunto"] == conjunto)]
    if modelo in MODELOS:
        t = t[t["calibrado"] == calibrado]
    return t.iloc[0]


def nombre_modelo(el):
    return f"{el['modelo']}{' + calibración' if el['calibrado'] else ''}"


F_T = fila(TAB_T, EL_T["receta_etiqueta"], EL_T["modelo"], EL_T["calibrado"])
F_S = fila(TAB_S, EL_S["receta_etiqueta"], EL_S["modelo"], EL_S["calibrado"])
BASE_GLOBAL = fila(TAB_T, EL_T["receta_etiqueta"], "Distribución global (sin variables)", False)
MAYOR = fila(TAB_T, EL_T["receta_etiqueta"], "Siempre la clase mayoritaria", False)

st.caption("Avance 3 · **¿Cuánto esperará la próxima audiencia?** Clasificación probabilística sobre "
           "466.178 audiencias de Familia, C.A. de Valparaíso (2015–2025).")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Modelo elegido · tramo", CORTO_MODELO[EL_T["modelo"]],
          f"{EL_T['receta_etiqueta'].lower()}{' · calibrado' if EL_T['calibrado'] else ''}", delta_color="off")
k2.metric("Log-loss en prueba (↓ mejor)", f"{F_T['log_loss']:.3f}",
          f"{F_T['log_loss'] - BASE_GLOBAL['log_loss']:+.3f} vs. sin variables", delta_color="inverse")
k3.metric("Accuracy en prueba", f"{F_T['accuracy']:.1%}",
          f"{(F_T['accuracy'] - MAYOR['accuracy']) * 100:+.1f} pp vs. clase mayoritaria")
k4.metric("Alerta > 60 días · ROC-AUC", f"{F_S['roc_auc']:.2f}", f"PR-AUC {F_S['pr_auc']:.2f}", delta_color="off")

tabs = st.tabs(["1 · Planteamiento", "2 · Resultados", "3 · Simulador: mi causa",
                "4 · Comparar tribunales", "5 · Conclusiones"])


def anios_rol(receta, calibrado, etapa="Prueba (origen 2024)", rol="Entrenamiento"):
    anios = [int(a) for a, r in R["esquemas"][f"{receta}|{calibrado}"][etapa].items() if r == rol]
    return f"{min(anios)}–{max(anios)}" if anios else "—"


def layout(fig, titulo=None, alto=360):
    fig.update_layout(template=PLANTILLA, height=alto, margin=dict(l=10, r=10, t=50 if titulo else 20, b=10),
                      title=dict(text=titulo, font=dict(size=15)) if titulo else None,
                      legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0))
    return fig


# =============================================================================
# 1 · Planteamiento
# =============================================================================
with tabs[0]:
    c1, c2, c3 = st.columns(3)
    with c1.container(border=True):
        st.markdown("#### Qué predecimos")
        st.markdown(
            "La **probabilidad** de cada tramo de espera entre que se agenda y se realiza la audiencia:\n\n"
            f"- <span style='color:{COLOR_TRAMO['Rápido']}'>■</span> **Rápido**: ≤ 15 días\n"
            f"- <span style='color:{COLOR_TRAMO['Estándar']}'>■</span> **Estándar**: 16–30 días\n"
            f"- <span style='color:{COLOR_TRAMO['Demora']}'>■</span> **Demora**: > 30 días\n\n"
            f"Y una **alerta** aparte: probabilidad de espera severa (> 60 días).",
            unsafe_allow_html=True)
    with c2.container(border=True):
        st.markdown("#### Con qué información")
        st.markdown("Solo lo que el abogado **sabe al agendar**:\n\n"
                    "- Tribunal\n- Tipo de procedimiento\n- Tipo de audiencia")
    with c3.container(border=True):
        st.markdown("#### Cómo validamos")
        st.markdown("**Origen móvil**: simulamos estar en una fecha y usamos solo los años anteriores.\n\n"
                    "- **Validación**: desde inicios de 2023, predecir 2023 → aquí se **elige** el modelo\n"
                    "- **Prueba ciega**: desde inicios de 2024, predecir 2024–2025 → solo se **reporta**\n"
                    "- Se comparan 3 modelos × 2 ventanas × con y sin calibración")

    st.markdown("")
    col_a, col_b = st.columns([1, 1])
    prev = pd.DataFrame(R["prevalencia"])
    with col_a:
        r1, r2 = st.columns([2, 1])
        clave_rec = r1.radio("Ventana de entrenamiento", list(R["recetas"]), format_func=R["recetas"].get,
                             horizontal=True, index=list(R["recetas"]).index(EL_T["receta"]), key="rec_plan")
        cal_plan = r2.toggle("Con calibración", value=EL_T["calibrado"], key="cal_plan",
                             help="Calibrar = reservar el último año antes del origen para ajustar las probabilidades, en vez de entrenar con él.")
        esq = R["esquemas"][f"{clave_rec}|{cal_plan}"]
        filas_esq = [{"Etapa": etapa, "Año": int(a), "Rol": rol} for etapa, roles in esq.items() for a, rol in roles.items()]
        esq_df = pd.DataFrame(filas_esq)
        fig = px.scatter(esq_df, x="Año", y="Etapa", color="Rol", symbol_sequence=["square"],
                         color_discrete_map={"Entrenamiento": COLOR, "Calibración": "#8E6CC0",
                                             "Evaluación": "#D1495B", "No se usa": "#E3E3E3"},
                         category_orders={"Etapa": list(esq), "Rol": ["Entrenamiento", "Calibración", "Evaluación", "No se usa"]})
        fig.update_traces(marker=dict(size=30, line=dict(width=1, color="white")))
        fig.update_xaxes(dtick=1, title="", tickangle=0, range=[2014.5, 2025.5])
        fig.update_yaxes(title="")
        fig.update_layout(legend_title_text="")
        st.plotly_chart(layout(fig, "Qué años usa cada etapa", 260), **ANCHO)
    with col_b:
        fig = go.Figure()
        fig.add_vrect(x0=2019.5, x1=2021.5, fillcolor="#8E6CC0", opacity=0.10, line_width=0,
                      annotation_text="Pandemia", annotation_position="top left")
        fig.add_vrect(x0=2021.5, x1=2025.5, fillcolor="#2E6F95", opacity=0.07, line_width=0,
                      annotation_text="Régimen híbrido", annotation_position="top right")
        for col, nombre, color in [("demora", "Espera mayor a 30 días", COLOR_TRAMO["Demora"]),
                                   ("severa", "Espera mayor a 60 días", COLOR_SEVERA)]:
            fig.add_scatter(x=prev["ANIO"], y=prev[col], mode="lines+markers+text", name=nombre,
                            line=dict(color=color, width=3), marker=dict(size=7),
                            text=[f"{v:.0%}" for v in prev[col]], textposition="top center",
                            textfont=dict(size=10, color=color))
        fig.update_yaxes(tickformat=".0%", range=[0, 0.78], title="% de audiencias")
        fig.update_xaxes(dtick=1, tickangle=0, title="", range=[2014.5, 2025.5])
        st.plotly_chart(layout(fig, "Audiencias con espera larga, por año", 380), **ANCHO)

# =============================================================================
# 2 · Resultados
# =============================================================================
with tabs[1]:
    s1, s2, s3 = st.columns([1.3, 1.3, 1])
    objetivo = s1.radio("Objetivo", ["Tramo de espera (3 clases)", "Alerta: espera severa (> 60 d)"], horizontal=True)
    es_tramo = objetivo.startswith("Tramo")
    tabla, el = (TAB_T, EL_T) if es_tramo else (TAB_S, EL_S)
    rec_et = s2.radio("Ventana de entrenamiento", list(R["recetas"].values()), horizontal=True,
                      index=list(R["recetas"].values()).index(el["receta_etiqueta"]), key="rec_res")
    usar_cal = s3.toggle("Con calibración", value=el["calibrado"], key="cal_res",
                         help="Reserva el último año antes del origen para calibrar (isotónica) en vez de entrenar con él.")

    t = tabla[(tabla["receta"] == rec_et) & (tabla["conjunto"] == PRUEBA)]
    t = t[(t["tipo"] != "Modelo") | (t["calibrado"] == usar_cal)].copy()
    t["es_elegido"] = (t["modelo"] == el["modelo"]) & (rec_et == el["receta_etiqueta"]) & (usar_cal == el["calibrado"])
    orden = {"Regla": 0, "Línea base": 1, "Modelo": 2}
    t = t.sort_values(["tipo"], key=lambda s: s.map(orden), kind="stable")

    st.markdown(f"##### Desempeño en la prueba ciega 2024–2025 · {rec_et}")
    cols = {"modelo": "Enfoque", "tipo": "Tipo", "accuracy": "Accuracy", "f1_macro": "F1 macro",
            "log_loss": "Log-loss ↓", "brier": "Brier ↓"}
    if not es_tramo:
        cols.update({"roc_auc": "ROC-AUC", "pr_auc": "PR-AUC"})
    vista = t[list(cols) + ["es_elegido"]].rename(columns=cols)
    fmt = {"Accuracy": "{:.1%}", "F1 macro": "{:.3f}", "Log-loss ↓": "{:.3f}", "Brier ↓": "{:.3f}",
           "ROC-AUC": "{:.3f}", "PR-AUC": "{:.3f}"}
    for c, f in fmt.items():
        if c in vista:
            vista[c] = pd.to_numeric(vista[c], errors="coerce").map(lambda v: "—" if pd.isna(v) else f.format(v))
    vista["Enfoque"] = np.where(vista["es_elegido"], vista["Enfoque"] + " (elegido)", vista["Enfoque"])
    estilo = (vista.drop(columns="es_elegido").style
              .apply(lambda r: ["font-weight: 700; background-color: rgba(46, 111, 149, 0.18)"
                                if vista.loc[r.name, "es_elegido"] else "" for _ in r], axis=1))
    c_tab, c_bar = st.columns([1.15, 1])
    c_tab.dataframe(estilo, hide_index=True, **ANCHO)

    mods = t[t["tipo"] != "Regla"].copy()
    err_sup = mods.get("log_loss_ic_sup", pd.Series(np.nan, index=mods.index)) - mods["log_loss"]
    err_inf = mods["log_loss"] - mods.get("log_loss_ic_inf", pd.Series(np.nan, index=mods.index))
    fig = go.Figure(go.Bar(
        y=[f"{m} · {v:.3f}" for m, v in zip(mods["modelo"], mods["log_loss"])], x=mods["log_loss"], orientation="h",
        marker_color=np.where(mods["es_elegido"], "#E9B949", np.where(mods["tipo"] == "Modelo", COLOR, "#B8B8B8")),
        error_x=dict(type="data", array=err_sup.fillna(0), arrayminus=err_inf.fillna(0), color="#444"),
        hovertemplate="%{y}<extra></extra>"))
    fig.update_xaxes(range=[mods["log_loss"].min() * 0.9, mods["log_loss"].max() * 1.03], title="Log-loss (más bajo = mejores probabilidades)")
    fig.update_yaxes(autorange="reversed")
    c_bar.plotly_chart(layout(fig, "Calidad de las probabilidades (IC 95 % por bootstrap de causas)", 300), **ANCHO)


    st.markdown("---")
    fe = fila(tabla, el["receta_etiqueta"], el["modelo"], el["calibrado"])
    cv = T["curvas"] if es_tramo else S["curvas"]
    g1, g2 = st.columns(2)
    with g1:
        if es_tramo:
            clase = st.radio("Calibración del tramo", R["clases"], horizontal=True, index=2)
            curva = cv["calibracion"][clase]
        else:
            curva = cv["calibracion"]
        fig = go.Figure()
        fig.add_scatter(x=[0, 1], y=[0, 1], mode="lines", name="Calibración perfecta", line=dict(dash="dot", color="#999"))
        estilo_sc = dict(color=COLOR, width=3) if not el["calibrado"] else dict(color="#B8B8B8")
        estilo_c = dict(color=COLOR, width=3) if el["calibrado"] else dict(color="#B8B8B8")
        fig.add_scatter(x=curva["sin_calibrar"]["prob_predicha"], y=curva["sin_calibrar"]["frecuencia_real"],
                        mode="lines+markers", name=f"Sin calibrar (entrena {anios_rol(el['receta'], False)})", line=estilo_sc)
        fig.add_scatter(x=curva["calibrado"]["prob_predicha"], y=curva["calibrado"]["frecuencia_real"],
                        mode="lines+markers", name=f"Calibrado (entrena {anios_rol(el['receta'], True)}, calibra 2023)",
                        line=estilo_c)
        fig.update_xaxes(title="Probabilidad que dice el modelo", tickformat=".0%", range=[0, 1])
        fig.update_yaxes(title="Frecuencia real en 2024–2025", tickformat=".0%", range=[0, 1])
        fig = layout(fig, "¿Las probabilidades dicen la verdad?", 430)
        fig.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.22, x=0))
        st.plotly_chart(fig, **ANCHO)
    with g2:
        if es_tramo:
            cm = np.array(cv["confusion"])
            nombres = [c.split(" (")[0] for c in R["clases"]]
            fig = px.imshow(cm, x=nombres, y=nombres, text_auto=".0%", color_continuous_scale="Blues",
                            labels=dict(x="Tramo predicho", y="Tramo real", color="%"), aspect="auto")
            fig.update_coloraxes(showscale=False)
            st.markdown("<div style='height: 2.6rem'></div>", unsafe_allow_html=True)
            st.plotly_chart(layout(fig, "Matriz de confusión (% de cada tramo real)", 380), **ANCHO)
        else:
            fig = go.Figure()
            fig.add_scatter(x=cv["pr"]["recall"], y=cv["pr"]["precision"], mode="lines", name="Modelo",
                            line=dict(color=COLOR_SEVERA, width=3), fill="tozeroy", fillcolor="rgba(127,29,29,0.08)")
            fig.add_hline(y=cv["prevalencia"], line_dash="dot", line_color="#999",
                          annotation_text=f"Al azar ({cv['prevalencia']:.0%})", annotation_position="bottom right")
            fig.update_xaxes(title="Recall: % de esperas severas detectadas", tickformat=".0%")
            fig.update_yaxes(title="Precisión: % de alertas correctas", tickformat=".0%", range=[0, 1])
            st.plotly_chart(layout(fig, "Curva precisión–recall de la alerta (> 60 d)", 380), **ANCHO)

    if es_tramo:
        st.markdown("---")
        ab = pd.DataFrame(R["ablacion"])
        fig = px.bar(ab, x="log_loss", y="variables", color="conjunto", barmode="group", orientation="h",
                     color_discrete_map={VALID: "#E9B949", PRUEBA: COLOR}, text_auto=".3f",
                     labels={"log_loss": "Log-loss (↓ mejor)", "variables": "", "conjunto": ""})
        fig.update_xaxes(range=[ab["log_loss"].min() * 0.95, ab["log_loss"].max() * 1.02])
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(layout(fig, "¿Agregar variables mejora el modelo? (log-loss, más bajo = mejor)", 300), **ANCHO)

# =============================================================================
# Utilidades del simulador / comparador
# =============================================================================
PROCS = (G.groupby("TIPO_PROCEDIMIENTO")["n"].sum().sort_values(ascending=False).index.tolist())


def selector_combo(prefijo, col1, col2):
    proc = col1.selectbox("Tipo de procedimiento", PROCS, format_func=bonito, key=f"{prefijo}_proc")
    tipos = (G[G["TIPO_PROCEDIMIENTO"] == proc].groupby("TIPO_AUDIENCIA")["n"].sum()
             .sort_values(ascending=False).index.tolist())
    tipo = col2.selectbox("Tipo de audiencia", tipos, format_func=bonito, key=f"{prefijo}_tipo_{proc}")
    return proc, tipo


def recomendaciones(r):
    recs = []
    if r["p_severa"] >= 0.25:
        recs.append(("", "**Riesgo de espera severa.** Marque la causa como de riesgo, reserve holgura en el "
                           "calendario y advierta al cliente que podría superar los 60 días."))
    if r["p_demora"] >= 0.6:
        recs.append(("", "**Lo más probable es esperar más de 30 días.** Informe al cliente un plazo de 1 a 2 meses "
                           "y, si hay urgencia, evalúe solicitar que se adelante la audiencia."))
    elif r["p_rapido"] >= 0.5:
        recs.append(("", "**Lo más probable es una audiencia pronta (≤ 15 días).** Prepare documentos y prueba desde ya."))
    else:
        recs.append(("", "**Escenario intermedio.** Planifique con el rango típico (P25–P75) que se muestra a la derecha."))
    if r["n"] < 30:
        recs.append(("", f"**Pocos casos recientes ({r['n']}).** La estimación se apoya en tribunales y audiencias "
                           "similares; tómela con cautela."))
    return recs


def tarjeta(titulo, valor, color, nota=""):
    return (f"<div style='border-left:6px solid {color}; padding:0.6rem 0.9rem; border-radius:6px;"
            f"background:rgba(127,127,127,0.06)'><div style='font-size:0.85rem;opacity:0.75'>{titulo}</div>"
            f"<div style='font-size:2rem;font-weight:700;color:{color};line-height:1.2'>{valor}</div>"
            f"<div style='font-size:0.8rem;opacity:0.7'>{nota}</div></div>")


# =============================================================================
# 3 · Simulador: mi causa
# =============================================================================
with tabs[2]:
    c1, c2, c3 = st.columns(3)
    proc, tipo = selector_combo("sim", c1, c2)
    sub = G[(G["TIPO_PROCEDIMIENTO"] == proc) & (G["TIPO_AUDIENCIA"] == tipo)]
    tribs = sub.sort_values("n", ascending=False)["TRIBUNAL"].tolist()
    previo = st.session_state.get("sim_trib_elegido")
    trib = c3.selectbox("Tribunal", tribs, index=tribs.index(previo) if previo in tribs else 0,
                        format_func=lambda t: f"{corto(t)} · {TRIBUNALES.get(t, ('', '?'))[1]}",
                        key=f"sim_trib_{proc}_{tipo}")
    st.session_state["sim_trib_elegido"] = trib
    r = sub[sub["TRIBUNAL"] == trib].iloc[0]

    st.markdown("")
    izq, der = st.columns([1.35, 1])
    with izq:
        st.markdown("##### Probabilidad de cada tramo de espera")
        t1, t2, t3 = st.columns(3)
        t1.markdown(tarjeta("Rápido · ≤ 15 días", f"{r['p_rapido']:.0%}", COLOR_TRAMO["Rápido"]), unsafe_allow_html=True)
        t2.markdown(tarjeta("Estándar · 16–30 días", f"{r['p_estandar']:.0%}", "#C99A1E"), unsafe_allow_html=True)
        t3.markdown(tarjeta("Demora · > 30 días", f"{r['p_demora']:.0%}", COLOR_TRAMO["Demora"]), unsafe_allow_html=True)
        fig = go.Figure()
        for nombre, col in [("Rápido", "p_rapido"), ("Estándar", "p_estandar"), ("Demora", "p_demora")]:
            fig.add_bar(x=[r[col]], y=[""], orientation="h", name=nombre, marker_color=COLOR_TRAMO[nombre],
                        text=f"{nombre} {r[col]:.0%}" if r[col] >= 0.12 else "", textposition="inside",
                        insidetextanchor="middle")
        fig.update_layout(barmode="stack", showlegend=False, xaxis=dict(tickformat=".0%", range=[0, 1]))
        st.plotly_chart(layout(fig, None, 110), **ANCHO)

        nivel = "Alta" if r["p_severa"] >= 0.25 else "Media" if r["p_severa"] >= 0.10 else "Baja"
        color_niv = {"Alta": COLOR_SEVERA, "Media": "#D97706", "Baja": "#2A9D8F"}[nivel]
        st.markdown(tarjeta("Alerta · probabilidad de espera severa (> 60 días)", f"{r['p_severa']:.0%}", color_niv,
                            f"Nivel de riesgo: <b>{nivel}</b> (umbrales 10 % y 25 %)"), unsafe_allow_html=True)

    with der:
        st.markdown("##### Lo que ocurrió en 2024–2025")
        reg = sub[sub["n"] > 0]
        if r["n"] > 0:
            fig = go.Figure()
            fig.add_bar(x=[r["p75"] - r["p25"]], base=[r["p25"]], y=[corto(trib)], orientation="h",
                        marker_color=COLOR, opacity=0.35, name="Rango típico P25–P75", width=0.5)
            fig.add_scatter(x=[r["mediana"]], y=[corto(trib)], mode="markers+text", marker=dict(size=16, color=COLOR),
                            text=[f"{r['mediana']:.0f} d"], textposition="top center", name="Mediana")
            med_reg = np.average(reg["mediana"], weights=reg["n"])
            fig.add_vline(x=med_reg, line_dash="dot", line_color="#D1495B",
                          annotation_text=f"Promedio regional {med_reg:.0f} d", annotation_position="top")
            fig.update_layout(showlegend=False, xaxis=dict(title="Días de espera", rangemode="tozero"))
            st.plotly_chart(layout(fig, None, 190), **ANCHO)
            m1, m2, m3 = st.columns(3)
            m1.metric("Mediana", f"{r['mediana']:.0f} d")
            m2.metric("Rango típico", f"{r['p25']:.0f}–{r['p75']:.0f} d")
            m3.metric("Audiencias", f"{int(r['n']):,}".replace(",", "."))
        else:
            st.warning("Este tribunal no registró esta audiencia en 2024–2025. La probabilidad se basa en audiencias similares.")

    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
    st.markdown("##### Recomendación para el estudio")
    for icono, texto in recomendaciones(r):
        st.markdown(f"- {texto}")

# =============================================================================
# 4 · Comparar tribunales
# =============================================================================
with tabs[3]:
    c1, c2, c3 = st.columns([1, 1, 1])
    proc_c, tipo_c = selector_combo("cmp", c1, c2)
    metrica = c3.selectbox("Colorear por", list(METRICAS_MAPA))
    col_m, fmt_m = METRICAS_MAPA[metrica]
    sub = G[(G["TIPO_PROCEDIMIENTO"] == proc_c) & (G["TIPO_AUDIENCIA"] == tipo_c)].copy()
    con_datos = sub[sub["n"] >= 30]["TRIBUNAL"].tolist()
    por_defecto = [t for t in con_datos if t != FUERA_DEL_MAPA]
    elegidos = st.multiselect("Tribunales legalmente competentes para la causa",
                              con_datos, default=por_defecto, format_func=corto, key=f"cmp_tribs_{proc_c}_{tipo_c}")
    sub = sub[sub["TRIBUNAL"].isin(elegidos)].copy()

    if len(sub) == 0:
        st.warning("Seleccione al menos un tribunal.")
    else:
        sub = sub.sort_values("mediana")
        mas_rapido = sub.iloc[0]
        sub["Comparación"] = np.where(
            sub["TRIBUNAL"] == mas_rapido["TRIBUNAL"], "Más rápido",
            np.where(sub["mediana_ic_inf"] <= mas_rapido["mediana_ic_sup"], "Sin diferencia clara", "Más lento"))
        rango = (sub[col_m].min(), sub[col_m].max()) if len(sub) > 1 else (sub[col_m].min() * 0.9, sub[col_m].max() * 1.1)

        mapa, rank = st.columns([1.15, 1])
        with mapa:
            en_mapa = sub[sub["TRIBUNAL"] != FUERA_DEL_MAPA].copy()
            en_mapa["etiqueta"] = en_mapa["TRIB_CORTO"] + " · " + en_mapa[col_m].map(fmt_m.format)
            en_mapa["tam"] = np.sqrt(en_mapa["n"])
            fig = px.scatter_map(
                en_mapa, lat="LAT", lon="LON", color=col_m, size="tam", size_max=26, text="etiqueta",
                color_continuous_scale=ESCALA_ESPERA, range_color=rango, zoom=7.4,
                center={"lat": -32.93, "lon": -71.15}, map_style="carto-positron-nolabels",
                hover_name="TRIB_CORTO",
                hover_data={"PROVINCIA": True, "mediana": ":.0f", "p_demora": ":.0%", "p_severa": ":.0%",
                            "n": True, "tam": False, "LAT": False, "LON": False, "etiqueta": False, col_m: False},
                labels={"PROVINCIA": "Provincia", "mediana": "Mediana (d)", "p_demora": "P(> 30 d)",
                        "p_severa": "P(> 60 d)", "n": "Audiencias 2024–25"})
            fig.update_traces(textposition="top right", textfont=dict(size=11, color="#222"))
            fig.update_layout(height=560, margin=dict(l=0, r=0, t=40, b=0),
                              title=dict(text=f"{metrica} por tribunal · color más intenso = más espera", font=dict(size=15)),
                              coloraxis_colorbar=dict(title="", tickformat=".0%" if col_m != "mediana" else "",
                                                      len=0.6, thickness=12))
            st.plotly_chart(fig, **ANCHO)
            if FUERA_DEL_MAPA in sub["TRIBUNAL"].values:
                ip = sub[sub["TRIBUNAL"] == FUERA_DEL_MAPA].iloc[0]
                st.caption(f"Isla de Pascua (fuera del mapa): mediana {ip['mediana']:.0f} d · "
                           f"P(> 30 d) {ip['p_demora']:.0%}.")

        with rank:
            colores = px.colors.sample_colorscale(
                ESCALA_ESPERA, ((sub[col_m] - rango[0]) / max(rango[1] - rango[0], 1e-9)).clip(0, 1).tolist())
            fig = go.Figure(go.Bar(
                y=sub["TRIB_CORTO"], x=sub["mediana"], orientation="h", marker_color=colores,
                marker_line=dict(color="#555", width=0.5),
                error_x=dict(type="data", array=(sub["mediana_ic_sup"] - sub["mediana"]).fillna(0),
                             arrayminus=(sub["mediana"] - sub["mediana_ic_inf"]).fillna(0), color="#444"),
                text=[f"{m:.0f} d" + ("  ≈" if c == "Sin diferencia clara" else "") for m, c in zip(sub["mediana"], sub["Comparación"])],
                textposition="inside", insidetextanchor="start",
                customdata=np.stack([sub["p25"], sub["p75"], sub["p_demora"], sub["n"]], axis=1),
                hovertemplate="<b>%{y}</b><br>Mediana %{x:.0f} d<br>Rango típico %{customdata[0]:.0f}–%{customdata[1]:.0f} d"
                              "<br>P(> 30 d) %{customdata[2]:.0%}<br>n = %{customdata[3]}<extra></extra>"))
            fig.update_yaxes(autorange="reversed")
            fig.update_xaxes(title="Mediana de espera 2024–2025 (días) · barra negra = IC 95 %",
                             range=[0, sub["mediana_ic_sup"].max() * 1.08])
            st.plotly_chart(layout(fig, "Ranking: del más rápido al más lento", 560), **ANCHO)
            st.caption("≈ sin diferencia clara con el más rápido")

        if len(sub) > 1:
            lento = sub.iloc[-1]
            claro = lento["Comparación"] == "Más lento"
            st.success(f"**{mas_rapido['TRIB_CORTO']}** es el más rápido para esta audiencia (mediana {mas_rapido['mediana']:.0f} d; "
                       f"{mas_rapido['p_demora']:.0%} de probabilidad de demora). Frente a **{lento['TRIB_CORTO']}** "
                       f"({lento['mediana']:.0f} d) la diferencia es de unos **{lento['mediana'] - mas_rapido['mediana']:.0f} días**"
                       + (" y es estadísticamente clara." if claro else ", pero los intervalos se cruzan."))

        tabla_c = sub[["TRIB_CORTO", "PROVINCIA", "n", "mediana", "p25", "p75", "p_rapido", "p_demora", "p_severa", "Comparación"]].copy()
        tabla_c["Rango típico"] = tabla_c["p25"].map("{:.0f}".format) + "–" + tabla_c["p75"].map("{:.0f}".format) + " d"
        tabla_c = tabla_c.drop(columns=["p25", "p75"]).rename(columns={
            "TRIB_CORTO": "Tribunal", "PROVINCIA": "Provincia", "n": "Audiencias", "mediana": "Mediana (d)",
            "p_rapido": "P(≤ 15 d)", "p_demora": "P(> 30 d)", "p_severa": "P(> 60 d)"})
        with st.expander("Ver tabla detallada"):
            st.dataframe(tabla_c.style.format({"Mediana (d)": "{:.0f}", "P(≤ 15 d)": "{:.0%}", "P(> 30 d)": "{:.0%}",
                                               "P(> 60 d)": "{:.0%}"})
                         .background_gradient(subset=["Mediana (d)"], cmap="YlOrRd"),
                         hide_index=True, **ANCHO)

# =============================================================================
# 5 · Conclusiones
# =============================================================================
with tabs[4]:
    def ll_val(receta_et, calibrado):
        t = TAB_T[(TAB_T["receta"] == receta_et) & (TAB_T["conjunto"] == VALID) & (TAB_T["tipo"] == "Modelo")
                  & (TAB_T["calibrado"] == calibrado)]
        return t["log_loss"].min()

    rc_c, rc_r = R["recetas"]["Completa"], R["recetas"]["Reciente"]
    ab = pd.DataFrame(R["ablacion"])
    ab = ab[ab["conjunto"] == PRUEBA].set_index("variables")["log_loss"]
    prep = G[(G["TIPO_PROCEDIMIENTO"] == "CONTENCIOSA") & (G["TIPO_AUDIENCIA"] == "AUDIENCIA PREPARATORIA") & (G["n"] >= 30)]

    c1, c2, c3 = st.columns(3)
    with c1.container(border=True):
        st.markdown("#### Hallazgos")
        st.markdown(
            f"1. **Las probabilidades sirven**: log-loss {F_T['log_loss']:.3f} vs. {BASE_GLOBAL['log_loss']:.3f} sin variables; "
            f"accuracy {F_T['accuracy']:.0%} vs. {MAYOR['accuracy']:.0%} de la clase mayoritaria.\n"
            "2. **Un modelo simple basta**: Gradient Boosting rinde casi igual que el bayesiano jerárquico. "
            "Casi todo el valor está en *qué tribunal y qué audiencia*.\n"
            f"3. **Los datos recientes pesan más que el algoritmo**: en validación, log-loss {ll_val(rc_r, False):.3f} con la "
            f"ventana reciente vs. {ll_val(rc_c, False):.3f} con la completa. Calibrar solo ayuda a la ventana completa "
            f"({ll_val(rc_c, True):.3f}).\n"
            f"4. **Más variables no ayudan**: modalidad, calendario o congestión empeoran la prueba "
            f"({ab.iloc[0]:.3f} → {ab.iloc[1]:.3f} y {ab.iloc[2]:.3f}).\n"
            f"5. **La alerta de espera severa funciona**: ROC-AUC {F_S['roc_auc']:.2f}; PR-AUC {F_S['pr_auc']:.2f}.\n"
            f"6. **La brecha entre tribunales es grande**: en preparatorias contenciosas la mediana va de "
            f"{prep['mediana'].min():.0f} a {prep['mediana'].max():.0f} días.")
    with c2.container(border=True):
        st.markdown("#### Limitaciones")
        st.markdown(
            "- **Solo audiencias realizadas**: las suspendidas no están en la fuente.\n"
            "- **No vemos al juez, a la defensa ni el contenido** de la causa: explican parte de la variación.\n"
            "- **Una jurisdicción y una materia** (Familia, C.A. Valparaíso).\n"
            "- **Las probabilidades envejecen**: hay tribunales que cambian bruscamente de un año a otro, "
            "así que el modelo debe reentrenarse con datos recientes.\n"
            "- **Comparar tribunales muestra asociación, no causa**: un tribunal puede recibir causas más complejas.")
    with c3.container(border=True):
        st.markdown("#### Uso responsable")
        st.markdown(
            "- El comparador sirve para **elegir entre opciones legales**, no para forzar la competencia.\n"
            "- La rapidez es **un criterio más**: distancia, costos y comparecencia telemática también pesan.\n"
            "- Si todos eligieran el tribunal más rápido, **la congestión se trasladaría**.\n"
            "- Se muestra siempre el **N de casos** y la incertidumbre para no sobrevender la precisión.")

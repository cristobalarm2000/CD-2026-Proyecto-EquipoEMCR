"""
Página 5 · EDA y Hallazgos (Pregunta P1: ¿de qué depende la espera para una audiencia?)

Reproduce de forma interactiva las secciones 1 a 11 del notebook
`03_EDA_audienciasparquet_temp.ipynb`. Todo se calcula desde el parquet
`audiencias_preparadas_modelo.parquet`; los textos de lectura y los hallazgos
provienen del notebook.

Requisitos: streamlit, pandas, numpy, plotly, pyarrow.
Nota: `st.set_page_config` ya se define en Inicio.py, por eso no se repite aquí.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# -----------------------------------------------------------------------------
# Constantes
# -----------------------------------------------------------------------------
NOMBRE_PARQUET = "audiencias_preparadas_modelo.parquet"
Y = "PLAZO_AGENDAMIENTO"
COLOR = "#2E6F95"    # color base
COLOR2 = "#C2571A"   # color de contraste
COLOR_P75 = "#BCD4E6"

COLUMNAS = [
    "COD_TRIBUNAL", "TRIBUNAL", "ID_CAUSA_RIT", "TIPO_PROCEDIMIENTO", "TIPO_AUDIENCIA",
    "FECHA_AUDIENCIA", "PLAZO_AGENDAMIENTO", "ANO_AUDIENCIA", "VIDEOCONFERENCIA",
    "DIA_SEMANA_AUDIENCIA", "DURACION_MINUTOS", "BLOQUE_HORARIO", "FLG_AUDIENCIA_FRUSTRADA",
    "DIAS_TRAMITACION_PREVIA", "DIAS_DESPACHO_AGENDAMIENTO", "TRAMO_AGENDAMIENTO",
    "ORDEN_AUDIENCIA_CAUSA", "TOTAL_AUDIENCIAS_CAUSA", "MACRO_MATERIA", "EPOCA_NORMATIVA",
]
ORDEN_EPOCA = [
    "Pre-Pandemia (Presencial)",
    "Emergencia Sanitaria (Ley 21.226)",
    "Régimen Permanente Híbrido (Ley 21.394)",
]
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
TOP_AUDIENCIAS = [
    "AUDIENCIA PREPARATORIA", "AUDIENCIA DE JUICIO",
    "CONTINUACION AUDIENCIA DE JUICIO", "AUDIENCIA",
]
SECCIONES = [
    "1 · Reconocimiento",
    "2-3 · Distribución de la espera",
    "4 · Categóricas",
    "5-6 · Relaciones y correlación",
    "7 · Comparación por grupos",
    "8 · Tribunal × tramo y tipo",
    "9 · Multivariado",
    "10 · Tiempo",
    "11 · Hallazgos",
]


# `use_container_width` fue reemplazado por `width="stretch"` en Streamlit recientes
_VER = tuple(int(x) for x in st.__version__.split(".")[:2])
ANCHO = {"width": "stretch"} if _VER >= (1, 50) else {"use_container_width": True}


# -----------------------------------------------------------------------------
# Carga de datos
# -----------------------------------------------------------------------------
def _buscar_parquet() -> Path | None:
    """Busca data/processed/<parquet> subiendo por las carpetas padre de esta página."""
    base = Path(__file__).resolve()
    candidatos = [Path.cwd() / "data" / "processed" / NOMBRE_PARQUET]
    candidatos += [p / "data" / "processed" / NOMBRE_PARQUET for p in base.parents[:5]]
    return next((c for c in candidatos if c.exists()), None)


@st.cache_data(show_spinner="Cargando audiencias...")
def cargar_datos() -> pd.DataFrame | None:
    ruta = _buscar_parquet()
    if ruta is None:
        return None
    try:
        df = pd.read_parquet(ruta, engine="pyarrow", columns=COLUMNAS)
    except ImportError:
        import duckdb  # alternativa documentada en el notebook
        df = duckdb.sql(f"select * from read_parquet('{ruta.as_posix()}')").df()[COLUMNAS]
    # Los Int64 con nulos dan problemas en gráficos: se pasan a float, como en el notebook
    for c in ["PLAZO_AGENDAMIENTO", "ANO_AUDIENCIA", "COD_TRIBUNAL", "DURACION_MINUTOS",
              "DIAS_TRAMITACION_PREVIA", "DIAS_DESPACHO_AGENDAMIENTO",
              "ORDEN_AUDIENCIA_CAUSA", "TOTAL_AUDIENCIAS_CAUSA"]:
        df[c] = df[c].astype("float64")
    # Etiquetas cortas de tribunal (igual que el notebook)
    df["TRIBUNAL_CORTO"] = (
        df["TRIBUNAL"]
        .str.replace("JUZGADO DE LETRAS Y GARANTIA DE", "LETRAS Y GARANTIA", regex=False)
        .str.replace("JUZGADO DE FAMILIA DE", "FAMILIA", regex=False)
        .str.title()
    )
    return df


# -----------------------------------------------------------------------------
# Cálculos (cacheados; `_df` no se hashea porque hay un único dataset)
# -----------------------------------------------------------------------------
def _stats_caja(s: pd.Series) -> pd.Series:
    q1, med, q3 = s.quantile([0.25, 0.5, 0.75])
    iqr = q3 - q1
    return pd.Series({
        "n": len(s), "q1": q1, "mediana": med, "q3": q3,
        "bigote_inf": s[s >= q1 - 1.5 * iqr].min(),
        "bigote_sup": s[s <= q3 + 1.5 * iqr].max(),
    })


@st.cache_data
def stats_caja(_df, col_grupo, col_y, col_hue=None):
    claves = [col_grupo] + ([col_hue] if col_hue else [])
    return _df.groupby(claves, observed=True)[col_y].apply(_stats_caja).unstack().reset_index()


@st.cache_data
def resumen_y(_df):
    y = _df[Y]
    return pd.Series({
        "media": y.mean(), "mediana": y.median(), "desv_std": y.std(), "min": y.min(),
        "Q1": y.quantile(.25), "Q3": y.quantile(.75), "P90": y.quantile(.90),
        "P95": y.quantile(.95), "P99": y.quantile(.99), "max": y.max(),
        "IQR": y.quantile(.75) - y.quantile(.25), "asimetría": y.skew(),
    })


@st.cache_data
def tabla_outliers(_df):
    y = _df[Y]
    q1, q3 = y.quantile([.25, .75])
    lim = q3 + 1.5 * (q3 - q1)
    out = _df[_df[Y] > lim]
    dist = out["TRIBUNAL_CORTO"].value_counts(normalize=True).head(5).mul(100).round(1)
    return lim, len(out), dist


@st.cache_data
def correlaciones(_df, metodo):
    cols = ["PLAZO_AGENDAMIENTO", "DURACION_MINUTOS", "DIAS_TRAMITACION_PREVIA",
            "DIAS_DESPACHO_AGENDAMIENTO", "ORDEN_AUDIENCIA_CAUSA",
            "TOTAL_AUDIENCIAS_CAUSA", "ANO_AUDIENCIA"]
    num = _df[cols].astype(float).copy()
    num["VIDEOCONFERENCIA"] = _df["VIDEOCONFERENCIA"].astype(int)
    num["FRUSTRADA"] = _df["FLG_AUDIENCIA_FRUSTRADA"].astype(int)
    return num.corr(method=metodo)


def _eta(df, cat_col, num_col):
    cat = df[cat_col].astype("category")
    x = df[num_col].astype("float64")
    medias = x.groupby(cat, observed=False).mean()
    conteos = cat.value_counts()
    gm = x.mean()
    ss_total = ((x - gm) ** 2).sum()
    ss_between = (conteos * (medias - gm) ** 2).sum()
    eta2 = ss_between / ss_total if ss_total > 0 else 0
    return float(np.sqrt(eta2)), float(eta2)


@st.cache_data
def tabla_eta(_df):
    filas = []
    for c in ["TIPO_AUDIENCIA", "EPOCA_NORMATIVA", "TIPO_PROCEDIMIENTO",
              "MACRO_MATERIA", "TRIBUNAL_CORTO", "BLOQUE_HORARIO"]:
        ew, e2w = _eta(_df, c, "PLAZO_AGENDAMIENTO")
        ed, e2d = _eta(_df, c, "DURACION_MINUTOS")
        filas.append({"Variable": c, "η Espera": ew, "Varianza espera (%)": e2w * 100,
                      "η Duración": ed, "Varianza duración (%)": e2d * 100})
    return pd.DataFrame(filas).sort_values("η Espera", ascending=False)


@st.cache_data
def resumen_por(_df, col):
    return (_df.groupby(col, observed=True)[Y]
            .agg(n="count", media="mean", mediana="median", p75=lambda s: s.quantile(.75)))


@st.cache_data
def pivote_tipo(_df, valor):
    sub = _df[_df["TIPO_AUDIENCIA"].isin(TOP_AUDIENCIAS)]
    orden = _df["TRIBUNAL_CORTO"].value_counts().index
    piv = sub.pivot_table(index="TRIBUNAL_CORTO", columns="TIPO_AUDIENCIA",
                          values=valor, aggfunc="median")
    return piv.reindex(orden)[[c for c in TOP_AUDIENCIAS if c in piv.columns]]


@st.cache_data
def mensual(_df):
    return (_df.set_index("FECHA_AUDIENCIA").resample("MS")[Y].agg(["median", "count"]))


@st.cache_data
def anual(_df):
    return _df.groupby("ANO_AUDIENCIA")[Y].agg(
        audiencias="count", mediana_dias="median",
        p75_dias=lambda s: s.quantile(0.75), media_dias="mean")


# -----------------------------------------------------------------------------
# Utilidades de gráficos
# -----------------------------------------------------------------------------
def _layout(fig, titulo=None, alto=420):
    fig.update_layout(title=titulo, height=alto, margin=dict(l=10, r=10, t=50 if titulo else 20, b=10),
                      template="plotly_white")
    return fig


def figura_cajas(st_df, col_grupo, titulo, horizontal=True, col_hue=None, alto=420):
    """Boxplots a partir de estadísticos precalculados (liviano, sin valores extremos)."""
    fig = go.Figure()
    colores = {False: COLOR, True: COLOR2}
    nombres = {False: "Presencial", True: "Remota"}
    grupos = [(None, st_df)] if col_hue is None else list(st_df.groupby(col_hue))
    for hue, sub in grupos:
        kw = dict(q1=sub["q1"], median=sub["mediana"], q3=sub["q3"],
                  lowerfence=sub["bigote_inf"], upperfence=sub["bigote_sup"],
                  marker_color=colores.get(hue, COLOR), name=nombres.get(hue, ""),
                  showlegend=col_hue is not None)
        if horizontal:
            fig.add_trace(go.Box(y=sub[col_grupo], orientation="h", **kw))
        else:
            fig.add_trace(go.Box(x=sub[col_grupo], **kw))
    if col_hue is not None:
        fig.update_layout(boxmode="group")
    return _layout(fig, titulo, alto)


def caja_hist(serie, nombre, recortar):
    s = serie.dropna()
    lim = s.quantile(.99)
    if recortar:
        s = s[s <= lim]
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Histograma", "Boxplot"))
    fig.add_trace(go.Histogram(x=s, nbinsx=35, marker_color=COLOR, name=nombre), row=1, col=1)
    fig.add_trace(go.Box(x=s, marker_color=COLOR, name="", boxpoints=False), row=1, col=2)
    fig.update_layout(showlegend=False, height=340, margin=dict(l=10, r=10, t=40, b=10),
                      template="plotly_white")
    return fig


# -----------------------------------------------------------------------------
# Secciones
# -----------------------------------------------------------------------------
def seccion_1(df):
    st.markdown("#### 1 · Reconocimiento del dataset")
    c = st.columns(5)
    c[0].metric("Audiencias (filas)", f"{len(df):,}".replace(",", "."))
    c[1].metric("Causas únicas", f"{df['ID_CAUSA_RIT'].nunique():,}".replace(",", "."))
    c[2].metric("Tribunales", df["COD_TRIBUNAL"].nunique())
    c[3].metric("Rango de fechas", f"{df['FECHA_AUDIENCIA'].min():%Y} – {df['FECHA_AUDIENCIA'].max():%Y}")
    c[4].metric("Nulos totales", int(df.isna().sum().sum()))
    st.markdown(
        "- **Unidad de análisis:** una audiencia realizada. Varias filas pertenecen a la misma causa "
        "(`ID_CAUSA_RIT`), por lo que **no son independientes**: al modelar se debe separar por causa o por tiempo.\n"
        "- **Y:** `PLAZO_AGENDAMIENTO` (días entre la programación y la realización de la audiencia).\n"
        "- **Ojo con fugas de información:** `DIAS_TRAMITACION_PREVIA` y `DIAS_DESPACHO_AGENDAMIENTO` "
        "se calculan con fechas que incluyen el plazo, así que no sirven para predecirlo."
    )


def seccion_2_3(df):
    st.markdown("#### 2 · Estadística descriptiva de la espera")
    r = resumen_y(df)
    cols = st.columns(6)
    for col, k in zip(cols, ["media", "mediana", "P90", "P95", "P99", "asimetría"]):
        col.metric(k.capitalize() if k != "asimetría" else "Asimetría",
                   f"{r[k]:.1f}" if k != "asimetría" else f"{r[k]:.2f}")
    st.caption("La media supera a la mediana: hay cola larga a la derecha. Para el cliente conviene informar "
               "rangos (P25 a P75) y no un solo promedio.")
    with st.expander("Ver todos los estadísticos"):
        st.dataframe(r.round(2).to_frame("valor"), **ANCHO)

    st.markdown("#### 3 · Variables numéricas")
    variables = {"Espera (PLAZO_AGENDAMIENTO)": "PLAZO_AGENDAMIENTO",
                 "Duración en minutos": "DURACION_MINUTOS",
                 "Días de tramitación previa": "DIAS_TRAMITACION_PREVIA",
                 "Audiencias por causa": "TOTAL_AUDIENCIAS_CAUSA"}
    c1, c2 = st.columns([3, 1])
    nombre = c1.selectbox("Variable", list(variables), key="num_var")
    recortar = c2.toggle("Cortar en P99", value=True, key="num_p99")
    st.plotly_chart(caja_hist(df[variables[nombre]], nombre, recortar), **ANCHO)

    lim, n_out, dist = tabla_outliers(df)
    st.markdown("**Outliers de la espera (regla 1,5·IQR)**")
    c1, c2 = st.columns([1, 2])
    c1.metric("Límite superior", f"{lim:.0f} días")
    c1.metric("Observaciones marcadas", f"{n_out:,}".replace(",", "."), f"{n_out / len(df):.1%} del total", delta_color="off")
    fig = px.bar(dist[::-1], orientation="h", color_discrete_sequence=[COLOR],
                 labels={"value": "% de los outliers", "TRIBUNAL_CORTO": ""})
    fig.update_layout(showlegend=False)
    c2.plotly_chart(_layout(fig, "¿Dónde se concentran los plazos extremos?", 260), **ANCHO)
    st.caption("Si los extremos se concentran en pocos tribunales no son ruido: son señal de congestión y se conservan.")


def seccion_4(df):
    st.markdown("#### 4 · Variables categóricas")
    cats = {"MACRO_MATERIA": "Macro materia", "EPOCA_NORMATIVA": "Época normativa",
            "BLOQUE_HORARIO": "Bloque horario", "DIA_SEMANA_AUDIENCIA": "Día de la semana",
            "TRIBUNAL_CORTO": "Tribunal", "TIPO_AUDIENCIA": "Tipo de audiencia (top 8)"}
    col = st.selectbox("Variable", list(cats), format_func=cats.get, key="cat_var")
    tabla = df[col].value_counts()
    if col == "TIPO_AUDIENCIA":
        st.caption(f"Tipos de audiencia en total: {df[col].nunique()}")
        tabla = tabla.head(8)
    pct = (tabla / len(df) * 100).round(1)
    c1, c2 = st.columns([2, 1])
    fig = px.bar(tabla[::-1], orientation="h", color_discrete_sequence=[COLOR],
                 labels={"value": "N° de audiencias", col: ""})
    fig.update_layout(showlegend=False)
    c1.plotly_chart(_layout(fig, f"Frecuencia por {cats[col].lower()}", 380), **ANCHO)
    c2.dataframe(pd.DataFrame({"n": tabla, "%": pct}), **ANCHO)
    st.caption("Pocos tribunales y tipos de audiencia concentran el volumen. Los tribunales pequeños "
               "(p. ej. Isla de Pascua o Putaendo) tienen medianas con menos respaldo: cautela al modelar.")


def seccion_5_6(df):
    st.markdown("#### 5 · ¿Las audiencias que esperan más duran más?")
    n = st.slider("Tamaño de la muestra aleatoria", 500, 10000, 3000, 500, key="scatter_n")
    muestra = df.sample(min(n, len(df)), random_state=42)
    fig = px.scatter(muestra, x=Y, y="DURACION_MINUTOS", opacity=.35,
                     color_discrete_sequence=[COLOR],
                     labels={Y: "Espera (días)", "DURACION_MINUTOS": "Duración (min)"})
    fig.update_xaxes(range=[0, df[Y].quantile(.99)])
    fig.update_yaxes(range=[0, df["DURACION_MINUTOS"].quantile(.99)])
    st.plotly_chart(_layout(fig, None, 380), **ANCHO)
    st.markdown(
        "- Nube sin pendiente: la espera y la duración en sala son estadísticamente independientes.\n"
        "- Las bandas horizontales corresponden a bloques de agenda preestablecidos (15, 30, 45, 60 min).\n"
        "- El plazo mide la **congestión de la agenda** del tribunal, no la complejidad del caso: no debe "
        "usarse como proxy de complejidad jurídica."
    )

    st.markdown("#### 6 · Correlación")
    metodo = st.radio("Método", ["pearson", "spearman"], horizontal=True,
                      format_func=str.capitalize, key="corr_metodo")
    corr = correlaciones(df, metodo)
    c1, c2 = st.columns([1, 2])
    comp = pd.DataFrame({"Pearson": correlaciones(df, "pearson")[Y],
                         "Spearman": correlaciones(df, "spearman")[Y]})
    comp = comp.drop(index=Y).sort_values("Pearson", key=abs, ascending=False)
    c1.markdown("**Correlación con la espera**")
    c1.dataframe(comp.round(2), **ANCHO)
    fig = px.imshow(corr, color_continuous_scale="RdBu_r", zmin=-1, zmax=1, text_auto=".2f", aspect="auto")
    c2.plotly_chart(_layout(fig, f"Matriz de correlación ({metodo.capitalize()})", 480), **ANCHO)
    st.markdown(
        "- `DIAS_TRAMITACION_PREVIA` y `DIAS_DESPACHO_AGENDAMIENTO` se construyen con las mismas fechas que el "
        "plazo: son **fuga de información** y no deben entrar a un modelo que lo prediga.\n"
        "- `VIDEOCONFERENCIA` y `ANO_AUDIENCIA` se parecen porque la modalidad remota solo existe desde 2020 "
        "(antes se imputó `False`): relación en parte artificial.\n"
        "- Baja correlación lineal no implica ausencia de relación (puede ser no lineal o aparecer solo dentro de grupos)."
    )

    st.markdown("**Asociación categórica vs numérica: Correlation Ratio (η)**")
    eta = tabla_eta(df)
    c1, c2 = st.columns([1, 1])
    c1.dataframe(eta.set_index("Variable").round(2), **ANCHO)
    fig = px.bar(eta[::-1], x="η Espera", y="Variable", orientation="h", color_discrete_sequence=[COLOR])
    c2.plotly_chart(_layout(fig, "Fuerza de asociación con la espera (η)", 300), **ANCHO)
    st.caption("η va de 0 (sin relación) a 1; η² es el % de la variabilidad explicado por el grupo. "
               "Las causas de la espera son de procedimiento, tipo de acto y jurisdicción.")


def seccion_7(df):
    st.markdown("#### 7 · ¿Cambia la espera según el grupo?")
    vista = st.radio("Comparar por", ["Macro materia", "Tribunal", "Época y modalidad"],
                     horizontal=True, key="s7_vista")

    if vista == "Macro materia":
        resumen = resumen_por(df, "MACRO_MATERIA").sort_values("mediana")
        cajas = stats_caja(df, "MACRO_MATERIA", Y).set_index("MACRO_MATERIA").loc[resumen.index].reset_index()
        st.plotly_chart(figura_cajas(cajas, "MACRO_MATERIA", "Espera según macro materia (sin valores extremos)", True, None, 380),
                        **ANCHO)
        st.dataframe(resumen.round(1), **ANCHO)

    elif vista == "Tribunal":
        min_n = st.slider("Mínimo de audiencias por tribunal", 100, 5000, 500, 100, key="s7_minn")
        t = resumen_por(df, "TRIBUNAL_CORTO").query("n >= @min_n").sort_values("mediana")
        fig = go.Figure()
        fig.add_trace(go.Bar(y=t.index, x=t["p75"], orientation="h", name="P75", marker_color=COLOR_P75))
        fig.add_trace(go.Bar(y=t.index, x=t["mediana"], orientation="h", name="Mediana", marker_color=COLOR))
        fig.add_vline(x=df[Y].median(), line_dash="dash", line_color="black")
        fig.update_layout(barmode="overlay", xaxis_title="Días de espera")
        st.plotly_chart(_layout(fig, f"Espera por tribunal (≥ {min_n} audiencias; línea = mediana global)", 520),
                        **ANCHO)
        st.caption("La mediana es la espera típica; el P75 es el umbral del 25 % de audiencias con mayores demoras.")
        st.dataframe(t.round(1), **ANCHO)

    else:
        por_epoca = df.groupby(["EPOCA_NORMATIVA", "VIDEOCONFERENCIA"])[Y].agg(
            n="size", mediana="median", p75=lambda s: s.quantile(.75))
        cajas = stats_caja(df, "EPOCA_NORMATIVA", Y, "VIDEOCONFERENCIA")
        cajas["EPOCA_NORMATIVA"] = pd.Categorical(cajas["EPOCA_NORMATIVA"], ORDEN_EPOCA, ordered=True)
        cajas = cajas.sort_values("EPOCA_NORMATIVA")
        st.plotly_chart(figura_cajas(cajas, "EPOCA_NORMATIVA", "Espera por época normativa y modalidad (sin valores extremos)",
                                     horizontal=False, col_hue="VIDEOCONFERENCIA", alto=420),
                        **ANCHO)
        st.dataframe(por_epoca.round(1), **ANCHO)
        st.markdown(
            "**Las audiencias remotas esperan más que las presenciales.** Dos factores:\n"
            "1. **Sesgo de composición (paradoja de Simpson):** el 38,6 % de las audiencias remotas son Juicios y "
            "Continuaciones, frente a solo 18,0 % en las presenciales (donde predominan las Preparatorias breves, 56,7 %).\n"
            "2. **Requisitos procesales bajo la Ley 21.394:** coordinación previa, verificación técnica y "
            "«salas virtuales habilitadas» con cupos más acotados."
        )


def seccion_8(df):
    st.markdown("#### 8 · Categórica vs categórica")
    vista = st.radio("Vista", ["Tribunal × tramo de espera", "Tribunal × tipo de audiencia"],
                     horizontal=True, key="s8_vista")

    if vista == "Tribunal × tramo de espera":
        tabla = pd.crosstab(df["TRIBUNAL_CORTO"], df["TRAMO_AGENDAMIENTO"], normalize="index") * 100
        tabla = tabla.loc[df["TRIBUNAL_CORTO"].value_counts().index]
        fig = px.imshow(tabla, color_continuous_scale="Blues", text_auto=".0f", aspect="auto",
                        labels=dict(color="% del tribunal"))
        fig.update_xaxes(tickangle=-25)
        st.plotly_chart(_layout(fig, "Distribución de la espera por tribunal (%, cada fila suma 100)", 560),
                        **ANCHO)
        st.caption("Un tribunal con color intenso a la derecha tiene casos que superan los 60 o 120 días, "
                   "aunque su mediana parezca aceptable.")
    else:
        valor = st.radio("Medida", ["Espera (días)", "Duración (min)"], horizontal=True, key="s8_valor")
        col, escala = (Y, "YlOrRd") if valor.startswith("Espera") else ("DURACION_MINUTOS", "Blues")
        piv = pivote_tipo(df, col)
        fig = px.imshow(piv, color_continuous_scale=escala, text_auto=".0f", aspect="auto",
                        labels=dict(color="Mediana"))
        fig.update_xaxes(tickangle=-20)
        st.plotly_chart(_layout(fig, f"Mediana de {valor.lower()} · Tribunal × tipo de audiencia", 560),
                        **ANCHO)

    st.info(
        "**Hallazgos de negocio inmediatos**\n\n"
        "- **Cuello de botella en juicio:** mientras en Limache o Los Andes una audiencia de juicio se agenda en ~31 días, "
        "en **Casablanca (62)** y **Viña del Mar (56)** el plazo se duplica.\n"
        "- **Lentitud en La Ligua y Quintero:** en preparatorias, La Ligua (39) y Quintero (42) cuadruplican a "
        "Limache (13) e Isla de Pascua (13).\n"
        "- **Duración en sala:** las continuaciones de juicio en **Limache (65 min)** y **Quillota (57)** duran el doble "
        "que en **Quintero (25)** o **Viña del Mar (31)**; útil para planificar agendas y horas facturables."
    )


def seccion_9(df):
    st.markdown("#### 9 · Multivariado")
    vista = st.radio("Vista", ["Espera por año y materia", "Carga por día y bloque horario"],
                     horizontal=True, key="s9_vista")
    if vista == "Espera por año y materia":
        materias = sorted(df["MACRO_MATERIA"].unique())
        sel = st.multiselect("Macro materias", materias, default=materias, key="s9_mat")
        d = (df[df["MACRO_MATERIA"].isin(sel)]
             .groupby(["ANO_AUDIENCIA", "MACRO_MATERIA"])[Y].median().reset_index())
        fig = px.line(d, x="ANO_AUDIENCIA", y=Y, color="MACRO_MATERIA", markers=True,
                      labels={"ANO_AUDIENCIA": "Año", Y: "Días (mediana)", "MACRO_MATERIA": ""})
        fig.add_vline(x=2020, line_dash="dash", line_color="gray")
        fig.update_layout(legend=dict(orientation="h", y=-0.25))
        st.plotly_chart(_layout(fig, "Mediana de espera por año y macro materia", 440), **ANCHO)
        st.caption("Si todas las líneas se mueven juntas, el cambio es del sistema; si una se separa, "
                   "el problema es específico de esa materia.")
    else:
        carga = pd.crosstab(df["DIA_SEMANA_AUDIENCIA"], df["BLOQUE_HORARIO"])
        carga = carga.reindex([d for d in DIAS if d in carga.index])
        fig = px.imshow(carga, color_continuous_scale="Blues", text_auto=",d", aspect="auto",
                        labels=dict(color="Audiencias"))
        st.plotly_chart(_layout(fig, "Audiencias por día de la semana y bloque horario", 380), **ANCHO)
        st.caption("Muestra los bloques saturados y los vacíos: útil para proponer horarios de reunión con clientes.")


def seccion_10(df):
    st.markdown("#### 10 · Componente temporal")
    m = mensual(df)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                        subplot_titles=("Audiencias realizadas por mes", "Espera mediana por mes"))
    fig.add_trace(go.Scatter(x=m.index, y=m["count"], line_color=COLOR, name="Audiencias"), row=1, col=1)
    fig.add_trace(go.Scatter(x=m.index, y=m["median"], line_color=COLOR2, name="Mediana (días)"), row=2, col=1)
    hitos = {"Ley 21.226": pd.Timestamp("2020-03-18"), "Ley 21.394": pd.Timestamp("2022-10-01")}
    for nombre, fecha in hitos.items():
        for fila in (1, 2):
            fig.add_vline(x=fecha.timestamp() * 1000, line_dash="dash", line_color="gray", row=fila, col=1)
        fig.add_annotation(x=fecha, y=1.0, yref="y domain", xref="x", text=nombre, showarrow=False,
                           xanchor="left", font=dict(size=11, color="gray"))
    fig.update_layout(showlegend=False)
    st.plotly_chart(_layout(fig, None, 500), **ANCHO)

    a = anual(df)
    st.markdown("**Evolución anual del sistema**")
    st.dataframe(a.round(1), **ANCHO)
    st.markdown(
        "**¿Quedó el sistema «aletargado» desde 2020?**\n"
        "- **En volumen: no.** Tras la caída de 2020 (suspensiones legales) el sistema recuperó el nivel de "
        "audiencias anuales previo a la pandemia.\n"
        "- **En tiempos de espera: sí hay mayor lentitud.** Mediana y P75 se mantienen por sobre los niveles "
        "pre-2020 (ver tabla). Causas señaladas: arrastre de inventario (*backlog*) tras 2020–2022 y nuevas "
        "reformas de alta demanda en Familia."
    )


def seccion_11(df):
    st.markdown("#### 11 · Hallazgos principales para el estudio jurídico")

    # Evidencia calculada desde los datos (misma lógica que el notebook)
    t = resumen_por(df, "TRIBUNAL_CORTO").query("n >= 500").sort_values("mediana")
    rapido, lento = t.index[0], t.index[-1]
    c = st.columns(3)
    c[0].metric("Tribunal más rápido", rapido, f"{t['mediana'].iloc[0]:.0f} días de mediana", delta_color="off")
    c[1].metric("Tribunal más lento", lento, f"{t['mediana'].iloc[-1]:.0f} días de mediana", delta_color="off")
    c[2].metric("Razón lento / rápido", f"{t['mediana'].iloc[-1] / max(t['mediana'].iloc[0], 1):.1f}x")
    st.dataframe(resumen_por(df, "EPOCA_NORMATIVA").loc[ORDEN_EPOCA].round(1), **ANCHO)

    with st.container(border=True):
        st.markdown("**1 · Brecha de eficiencia territorial.** El tribunal donde ingresa la causa determina de forma "
                    "decisiva la espera: hay una brecha de casi 3x entre el más ágil y el más lento.")
        st.markdown("*Evidencia:* Familia Quilpué y Limache tienen medianas de 13 a 15 días; Familia La Ligua y "
                    "Quintero, de 37 a 42 días en preparatorias (secciones 7 y 8).")
        st.markdown("*Acción:* ajustar la promesa de plazos al cliente según la jurisdicción y priorizar solicitudes "
                    "de agilización en juzgados congestionados.")
        with st.expander("Interpretación"):
            st.write("La lentitud no responde solo al volumen de ingresos (Viña del Mar tramita el mayor volumen pero es "
                     "más rápido en preparatorias que La Ligua): hay cuellos de botella operativos y de capacidad de sala.")

    with st.container(border=True):
        st.markdown("**2 · El tipo de audiencia manda.** `TIPO_AUDIENCIA` es la variable individual que más varianza "
                    "explica del plazo (η = 0,33; η² = 10,9 %).")
        st.markdown("*Evidencia:* las audiencias cautelares o inmediatas se fijan en menos de 10 días; las de juicio "
                    "son el principal embudo, con hasta 56–62 días en Viña del Mar y Casablanca.")
        st.markdown("*Acción:* anticipar que una causa que no llega a acuerdo en la preparatoria sumará al menos "
                    "2 meses de espera antes de rendir prueba en juicio.")
        with st.expander("Interpretación"):
            st.write("Las salas prolongadas para juicio son el recurso más escaso de la judicatura de familia.")

    with st.container(border=True):
        st.markdown("**3 · Capacidad recuperada, mayor inercia.** Tras 2020 (Ley 21.226) el sistema recuperó su "
                    "volumen de audiencias pero mantiene un desplazamiento al alza en los tiempos de espera.")
        st.markdown("*Evidencia:* ~44.000 audiencias anuales en 2024–2025; la mediana subió ~20 % (de 24 a 29 días) "
                    "y el P75 ~50 % (de 35 a 50–53 días).")
        st.markdown("*Acción:* calcular los plazos de referencia con holguras de 20 % a 50 % sobre las históricas "
                    "pre-pandemia.")
        with st.expander("Interpretación"):
            st.write("No hay parálisis de capacidad, pero sí «aletargamiento estructural» por arrastre de inventario "
                     "y mayor carga incidental de reformas recientes en familia y alimentos.")


SECCION_FN = {
    SECCIONES[0]: seccion_1, SECCIONES[1]: seccion_2_3, SECCIONES[2]: seccion_4,
    SECCIONES[3]: seccion_5_6, SECCIONES[4]: seccion_7, SECCIONES[5]: seccion_8,
    SECCIONES[6]: seccion_9, SECCIONES[7]: seccion_10, SECCIONES[8]: seccion_11,
}

# -----------------------------------------------------------------------------
# Página
# -----------------------------------------------------------------------------
st.title("🔍 EDA y Hallazgos")
st.caption("Pregunta P1: ¿qué variables se asocian con la **espera** para una audiencia y cómo cambia según "
           "tribunal, materia y época? · Familia, C.A. Valparaíso, 2015–2025")

df = cargar_datos()
if df is None:
    st.error(f"No se encontró `{NOMBRE_PARQUET}`. Debe estar en una carpeta `data/processed/` "
             "dentro del proyecto (junto a la app o en una carpeta superior).")
    st.stop()

seccion = st.radio("Sección", SECCIONES, horizontal=True, label_visibility="collapsed", key="eda_seccion")
st.divider()
SECCION_FN[seccion](df)
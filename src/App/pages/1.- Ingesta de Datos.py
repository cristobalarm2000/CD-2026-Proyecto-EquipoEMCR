import json
import time
import unicodedata
import re
from pathlib import Path
from typing import Dict, List, Optional

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# -----------------------------------------------------------------------------
# 1. Configuración de la Página
# -----------------------------------------------------------------------------
try:
    st.set_page_config(
        page_title="1.- Ingesta de Datos",
        page_icon="📥",
        layout="wide",
        initial_sidebar_state="expanded"
    )
except Exception:
    pass

# -----------------------------------------------------------------------------
# 2. Rutas y Detección de Archivos
# -----------------------------------------------------------------------------
CURRENT_DIR = Path(__file__).resolve().parent

# Detección dinámica y robusta de la raíz del proyecto
BASE_DIR = None
for p in [CURRENT_DIR] + list(CURRENT_DIR.parents):
    if (p / "data").exists() and (p / "src").exists():
        BASE_DIR = p
        break
if BASE_DIR is None:
    BASE_DIR = Path(r"C:\Users\frero\CD-2026-Proyecto-EquipoEMCR")

# Configurar sys.path para importar desde src
import sys
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.Api_Caller import (
    PJUDClient,
    ENDPOINTS_MAP,
    COMPETENCIAS_MAP,
    MAPA_COMPETENCIAS_INVERSO,
    norm_col,
    cargar_catalogo_cortes as api_cargar_cortes,
    cargar_catalogo_tribunales as api_cargar_tribunales
)

API_CALLER_DIR = BASE_DIR / "src" / "Api_Caller"
DATA_RAW_DIR = BASE_DIR / "data" / "raw"

# Carpetas de datos crudos (JSON) y Parquet
RAW_DIR = DATA_RAW_DIR / "05_muestras"
if not RAW_DIR.exists():
    fallback_raw = BASE_DIR / "notebooks" / "Explorador_API" / "S2" / "PJUD_FAMILIA" / "05_muestras"
    if fallback_raw.exists():
        RAW_DIR = fallback_raw
    else:
        RAW_DIR.mkdir(parents=True, exist_ok=True)

PARQUET_DIR = DATA_RAW_DIR / "parquet"
if not PARQUET_DIR.exists():
    fallback_pq = BASE_DIR / "notebooks" / "Explorador_API" / "S2" / "PJUD_FAMILIA" / "parquet"
    if fallback_pq.exists():
        PARQUET_DIR = fallback_pq
    else:
        PARQUET_DIR.mkdir(parents=True, exist_ok=True)

# Catálogos y metadatos centralizados
CORTES_PATH = API_CALLER_DIR / "cortes.csv"
TRIBUNALES_PATH = API_CALLER_DIR / "tribunales.csv"
SWAGGER_PATH = API_CALLER_DIR / "swagger.json"

MANIFIESTO_PATH = DATA_RAW_DIR / "03_pruebas_api.csv"
if not MANIFIESTO_PATH.exists():
    MANIFIESTO_PATH = API_CALLER_DIR / "03_pruebas_api.csv"

# -----------------------------------------------------------------------------
# 3. Utilidades y Wrappers con Caché
# -----------------------------------------------------------------------------

def norm_col(c: str) -> str:
    c = unicodedata.normalize("NFKD", str(c)).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "_", c.strip().upper()).strip("_")

@st.cache_data(show_spinner=False)
def cargar_catalogo_cortes() -> pd.DataFrame:
    return api_cargar_cortes(CORTES_PATH)

@st.cache_data(show_spinner=False)
def cargar_catalogo_tribunales() -> pd.DataFrame:
    return api_cargar_tribunales(TRIBUNALES_PATH)

@st.cache_data(show_spinner=False)
def cargar_dataset_parquet(endpoint: str) -> pd.DataFrame:
    parquet_path = PARQUET_DIR / f"{endpoint}.parquet"
    if parquet_path.exists():
        df = pd.read_parquet(parquet_path)
        return df
    return pd.DataFrame()

def obtener_resumen_archivos_raw():
    archivos = list(RAW_DIR.glob("*.json"))
    total_bytes = sum(f.stat().st_size for f in archivos)
    return len(archivos), round(total_bytes / (1024 * 1024), 2)

def obtener_resumen_archivos_parquet():
    archivos = list(PARQUET_DIR.glob("*.parquet"))
    total_bytes = sum(f.stat().st_size for f in archivos)
    total_filas = 0
    for f in archivos:
        try:
            import pyarrow.parquet as pq
            total_filas += pq.read_metadata(f).num_rows
        except Exception:
            pass
    return len(archivos), round(total_bytes / (1024 * 1024), 2), total_filas

# -----------------------------------------------------------------------------
# 4. Barra Lateral (Sidebar)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/Poder_Judicial_de_Chile_%28logo%29.svg/1200px-Poder_Judicial_de_Chile_%28logo%29.svg.png", width=140)
    st.title("Configuración de Ingesta")
    st.markdown("---")

    df_cortes = cargar_catalogo_cortes()
    opciones_cortes = {f"{row['corte']} - {row['glosa_corte']}": row['corte'] for _, row in df_cortes.iterrows()}
    corte_sel_label = st.selectbox(
        "🏛️ Corte de Apelaciones",
        options=list(opciones_cortes.keys()),
        index=list(opciones_cortes.values()).index(30) if 30 in opciones_cortes.values() else 0
    )
    cod_corte = opciones_cortes[corte_sel_label]

    st.markdown("### ⚖️ Materias Jurídicas")
    competencias_seleccionadas = st.multiselect(
        "Seleccione materias a incluir:",
        options=list(COMPETENCIAS_MAP.keys()),
        default=["Familia"]
    )

    st.markdown("### 📅 Rango de Años")
    anio_min, anio_max = st.slider("Años a consultar:", min_value=2015, max_value=2025, value=(2015, 2025))
    anios_seleccionados = list(range(anio_min, anio_max + 1))

    st.markdown("### 🎯 Endpoints Objetivos")
    default_eps = ["audiencias_realizadas_competencia_detalle"] if "audiencias_realizadas_competencia_detalle" in ENDPOINTS_MAP else list(ENDPOINTS_MAP.keys())
    endpoints_seleccionados = st.multiselect(
        "Seleccione microdatos a extraer:",
        options=list(ENDPOINTS_MAP.keys()),
        default=default_eps,
        format_func=lambda x: f"{ENDPOINTS_MAP[x]} ({x})"
    )

    st.markdown("---")
    st.markdown("### ⚙️ Opciones Avanzadas")
    force_refresh = st.checkbox("Forzar re-descarga desde API (ignorar caché)", value=False)
    sleep_delay = st.slider("Pausa entre peticiones (seg)", min_value=0.2, max_value=2.0, value=0.5, step=0.1)

# -----------------------------------------------------------------------------
# 5. Encabezado y KPIs Principales
# -----------------------------------------------------------------------------
st.title("📥 Ingesta de Datos: Poder Judicial de Chile (PJUD)")
materias_str = ", ".join(competencias_seleccionadas) if competencias_seleccionadas else "Familia"
st.markdown(
    "Pipeline integral de **extracción, validación, tipificación y compresión** de microdatos estadísticos "
    f"para la **Corte de Apelaciones de Valparaíso (Código {cod_corte})** en **Audiencias Realizadas** "
    f"({materias_str}, {anio_min}-{anio_max})."
)

n_raw, mb_raw = obtener_resumen_archivos_raw()
n_parquet, mb_parquet, total_filas_pq = obtener_resumen_archivos_parquet()
compresion_ratio = round(((mb_raw - mb_parquet) / mb_raw * 100), 1) if mb_raw > 0 else 0.0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📦 Archivos JSON Crudos", f"{n_raw} archivos", f"{mb_raw:,.1f} MB en disco")
with col2:
    filas_info = f"{total_filas_pq:,} filas" if total_filas_pq > 0 else "Snappy"
    st.metric("⚡ Datasets Parquet", f"{n_parquet} consolidado{'s' if n_parquet != 1 else ''}", f"{mb_parquet:,.1f} MB ({filas_info})")
with col3:
    st.metric("🚀 Reducción de Espacio", f"{compresion_ratio}%", "Compresión columnar")
with col4:
    st.metric("🏛️ Jurisdicción", f"Corte {cod_corte}", f"{materias_str} ({anio_min}-{anio_max})")

st.markdown("---")

# -----------------------------------------------------------------------------
# 6. Pestañas Principales
# -----------------------------------------------------------------------------
tab_exploracion, tab_consola, tab_catalogos = st.tabs([
    "📊 1. Exploración y Análisis Comparativo",
    "🚀 2. Ejecutor de Ingesta en Vivo",
    "📋 3. Catálogos y Documentación Técnica"
])

# =============================================================================
# TAB 1: EXPLORACIÓN Y ANÁLISIS
# =============================================================================
with tab_exploracion:
    st.subheader("Análisis Estadístico de Microdatos Consolidados")

    col_ep, col_comp = st.columns([2, 1])
    with col_ep:
        ep_keys = list(ENDPOINTS_MAP.keys())
        default_ep_idx = ep_keys.index("audiencias_realizadas_competencia_detalle") if "audiencias_realizadas_competencia_detalle" in ep_keys else 0
        ep_analisis = st.selectbox(
            "Seleccione el dataset a explorar:",
            options=ep_keys,
            index=default_ep_idx,
            format_func=lambda x: f"📁 {ENDPOINTS_MAP[x]} ({x})"
        )
    with col_comp:
        opciones_comp_filtro = ["Todas"] + list(COMPETENCIAS_MAP.keys())
        default_comp_filtro = ["Familia"] if "Familia" in opciones_comp_filtro else ["Todas"]
        filtro_comp = st.multiselect(
            "Filtrar por Materia:",
            options=opciones_comp_filtro,
            default=default_comp_filtro
        )

    df_dataset = cargar_dataset_parquet(ep_analisis)

    if df_dataset.empty:
        st.warning(f"⚠️ El dataset {ep_analisis}.parquet no se encuentra procesado aún. Ejecuta la ingesta o consolidación.")
    else:
        # Filtrado por competencia si no es Todas
        if "Todas" not in filtro_comp and filtro_comp:
            cods_comp = [COMPETENCIAS_MAP[c] for c in filtro_comp if c in COMPETENCIAS_MAP]
            if "COMPETENCIA" in df_dataset.columns:
                df_dataset = df_dataset[df_dataset["COMPETENCIA"].isin(cods_comp)]

        st.caption(f"Visualizando **{len(df_dataset):,}** registros consolidados | {len(df_dataset.columns)} columnas.")

        # --- Gráficos Comparativos ---
        c_graf1, c_graf2 = st.columns(2)

        with c_graf1:
            st.markdown("##### 📈 Evolución Temporal por Materia")
            col_anio_nombre = "ANO_INGRESO" if "ANO_INGRESO" in df_dataset.columns else "ANO_PROCESO" if "ANO_PROCESO" in df_dataset.columns else "ANO"
            
            if col_anio_nombre in df_dataset.columns and "COMPETENCIA" in df_dataset.columns:
                df_temp = df_dataset.dropna(subset=[col_anio_nombre]).copy()
                df_temp[col_anio_nombre] = pd.to_numeric(df_temp[col_anio_nombre], errors="coerce")
                df_temp = df_temp.dropna(subset=[col_anio_nombre])
                df_temp[col_anio_nombre] = df_temp[col_anio_nombre].astype(int)
                
                # Filtrar años razonables
                df_temp = df_temp[(df_temp[col_anio_nombre] >= anio_min) & (df_temp[col_anio_nombre] <= anio_max)]
                
                pivote_anios = df_temp.groupby([col_anio_nombre, "COMPETENCIA"]).size().reset_index(name="Total")
                pivote_anios["Materia"] = pivote_anios["COMPETENCIA"].map(MAPA_COMPETENCIAS_INVERSO).fillna(pivote_anios["COMPETENCIA"])

                fig_line = px.line(
                    pivote_anios,
                    x=col_anio_nombre,
                    y="Total",
                    color="Materia",
                    markers=True,
                    labels={col_anio_nombre: "Año", "Total": "Cantidad de Registros"},
                    title=f"Volumen Anual ({ENDPOINTS_MAP[ep_analisis]})",
                    color_discrete_sequence=["#1f77b4", "#ff7f0e", "#2ca02c"]
                )
                fig_line.update_layout(hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("Columna temporal no identificada para este endpoint.")

        with c_graf2:
            st.markdown("##### 🏛️ Distribución por Tribunal")
            col_trib_nombre = "TRIBUNAL" if "TRIBUNAL" in df_dataset.columns else "GLOSA_TRIBUNAL"
            if col_trib_nombre in df_dataset.columns:
                top_tribunales = df_dataset[col_trib_nombre].value_counts().head(12).reset_index()
                top_tribunales.columns = ["Tribunal", "Registros"]
                
                fig_bar = px.bar(
                    top_tribunales,
                    x="Registros",
                    y="Tribunal",
                    orientation="h",
                    title="Top 12 Tribunales con Mayor Volumen",
                    color="Registros",
                    color_continuous_scale="Blues"
                )
                fig_bar.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("Columna de tribunal no disponible en este dataset.")

        # --- Gráfico de Materias Específicas o Tipos de Audiencia si aplica ---
        if "ingresos_materia" in ep_analisis or "terminos_materia" in ep_analisis:
            col_materia = "MATERIA" if "MATERIA" in df_dataset.columns else "GLOSA_MATERIA"
            if col_materia in df_dataset.columns:
                st.markdown("##### ⚖️ Top 10 Materias Específicas más Demandadas")
                top_mat = df_dataset[col_materia].value_counts().head(10).reset_index()
                top_mat.columns = ["Materia", "Causas"]
                fig_mat = px.bar(
                    top_mat,
                    x="Causas",
                    y="Materia",
                    orientation="h",
                    color="Causas",
                    color_continuous_scale="Viridis",
                    title="Distribución de Causas por Materia Jurídica"
                )
                fig_mat.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
                st.plotly_chart(fig_mat, use_container_width=True)

        if "audiencias_realizadas" in ep_analisis:
            col_tipo_aud = "TIPO_AUDIENCIA" if "TIPO_AUDIENCIA" in df_dataset.columns else None
            if col_tipo_aud:
                st.markdown("##### 🎙️ Top 10 Tipos de Audiencias más Realizadas")
                top_aud = df_dataset[col_tipo_aud].value_counts().head(10).reset_index()
                top_aud.columns = ["Tipo de Audiencia", "Total Audiencias"]
                fig_aud = px.bar(
                    top_aud,
                    x="Total Audiencias",
                    y="Tipo de Audiencia",
                    orientation="h",
                    color="Total Audiencias",
                    color_continuous_scale="Purples",
                    title="Distribución de Audiencias por Tipo de Audiencia"
                )
                fig_aud.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
                st.plotly_chart(fig_aud, use_container_width=True)

        # --- Explorador de Tabla ---
        st.markdown("##### 📄 Vista Previa de Microdatos")
        st.dataframe(df_dataset.head(100), use_container_width=True, height=350)

        # Botón de Descarga de Muestra
        csv_sample = df_dataset.head(5000).to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Descargar muestra filtrada (CSV)",
            data=csv_sample,
            file_name=f"muestra_{ep_analisis}.csv",
            mime="text/csv"
        )

# =============================================================================
# TAB 2: CONSOLA DE INGESTA
# =============================================================================
with tab_consola:
    st.subheader("Ejecutor de Ingesta desde API PJUD")
    st.markdown(
        "Utiliza el cliente HTTP para consultar los endpoints del PJUD, gestionar reintentos, almacenar los JSONs en disco "
        "y normalizarlos hacia Apache Parquet."
    )

    # Estado del servidor PJUD
    c_status1, c_status2 = st.columns([1, 3])
    with c_status1:
        if st.button("🔍 Probar Conexión con PJUD"):
            try:
                t0 = time.time()
                r = requests.get("https://estadisticaservices.pjud.cl/swagger.json", timeout=10)
                dur = round(time.time() - t0, 2)
                if r.status_code == 200:
                    st.success(f"🟢 Servidor en línea (HTTP 200 - {dur}s)")
                else:
                    st.warning(f"🟡 Respuesta inesperada: HTTP {r.status_code}")
            except Exception as e:
                st.error(f"🔴 No se pudo conectar: {e}")

    with c_status2:
        st.info(
            f"Parámetros actuales: **Corte {cod_corte}** | "
            f"**Materias:** {', '.join(competencias_seleccionadas)} | "
            f"**Años:** {anio_min} a {anio_max} ({len(anios_seleccionados)} años) | "
            f"**Endpoints:** {len(endpoints_seleccionados)}"
        )

    # Botón de Ejecución Masiva
    total_llamadas = len(competencias_seleccionadas) * len(anios_seleccionados) * len(endpoints_seleccionados)
    st.markdown(f"**Total de combinaciones a procesar:** `{total_llamadas}` consultas")

    btn_iniciar = st.button("🚀 Iniciar / Actualizar Ingesta Masiva", type="primary")

    if btn_iniciar:
        client = PJUDClient(timeout=60, sleep_delay=sleep_delay)
        barra_progreso = st.progress(0)
        status_box = st.empty()
        
        resultados_ejecucion = []
        contador = 0

        for comp_nombre in competencias_seleccionadas:
            comp_api = COMPETENCIAS_MAP[comp_nombre]
            for anio in anios_seleccionados:
                for ep in endpoints_seleccionados:
                    contador += 1
                    pct = contador / total_llamadas
                    barra_progreso.progress(pct)
                    status_box.markdown(f"⏳ **[{contador}/{total_llamadas}] Descargando:** `{comp_nombre}` | `{ep}` ({anio})...")

                    res = client.descargar(
                        endpoint=ep,
                        anio=anio,
                        corte=cod_corte,
                        tribunal=0,
                        competencia_api=comp_api,
                        force_refresh=force_refresh,
                        raw_dir=RAW_DIR
                    )
                    resultados_ejecucion.append(res)

        status_box.success("🎉 ¡Descarga masiva de JSONs completada!")
        st.toast("Descarga finalizada con éxito", icon="✅")

        # Consolidar a Parquet
        st.info("🔄 Consolidando y tipificando datasets hacia formato Apache Parquet...")
        with st.spinner("Procesando datasets en Parquet..."):
            for ep in endpoints_seleccionados:
                dfs = []
                for comp_nombre in competencias_seleccionadas:
                    comp_api = COMPETENCIAS_MAP[comp_nombre]
                    for anio in anios_seleccionados:
                        p = RAW_DIR / f"{ep}__{cod_corte}_0_{comp_api}_{anio}.json"
                        if p.exists():
                            try:
                                data = json.loads(p.read_bytes())
                                if data:
                                    df_a = pd.json_normalize(data)
                                    df_a.columns = [c.replace("_id.", "") for c in df_a.columns]
                                    df_a.columns = [norm_col(c) for c in df_a.columns]
                                    if "COMPETENCIA" not in df_a.columns:
                                        df_a["COMPETENCIA"] = comp_api
                                    if "ANO_PROCESO" not in df_a.columns and "ANO" not in df_a.columns:
                                        df_a["ANO_PROCESO"] = anio
                                    dfs.append(df_a)
                            except Exception:
                                pass
                if dfs:
                    df_consolidado = pd.concat(dfs, ignore_index=True)
                    # Parsear fechas
                    for c in df_consolidado.columns:
                        if any(kw in c for kw in ["FECHA", "FEC_"]):
                            s = df_consolidado[c].astype(str).str.strip()
                            df_consolidado[c] = pd.to_datetime(s, format="%Y-%m-%d", errors="coerce").fillna(
                                pd.to_datetime(s, format="%d-%m-%Y", errors="coerce")
                            )
                    # IDs numéricos seguros
                    for id_col in ["ID_CAUSA", "COD_CORTE", "COD_TRIBUNAL", "ID_AUDIENCIA", "TOTAL_TERMINOS", "TOTAL_CAUSAS", "TOTAL_AUDIENCIAS"]:
                        if id_col in df_consolidado.columns:
                            df_consolidado[id_col] = pd.to_numeric(df_consolidado[id_col], errors="coerce").astype("Int64")
                    # Armonizar tipos object
                    for col in df_consolidado.columns:
                        if df_consolidado[col].dtype == "object":
                            tipos = set(type(x) for x in df_consolidado[col].dropna())
                            if len(tipos) > 1:
                                df_consolidado[col] = df_consolidado[col].astype(str).str.replace(r"\.0$", "", regex=True)

                    df_consolidado.to_parquet(PARQUET_DIR / f"{ep}.parquet", engine="pyarrow", index=False, compression="snappy")

        st.success("✅ ¡Archivos Parquet actualizados exitosamente!")
        st.cache_data.clear()

    # Tabla resumen de manifiesto
    if MANIFIESTO_PATH.exists():
        st.markdown("##### 📜 Trazabilidad de Consultas Realizadas")
        df_man = pd.read_csv(MANIFIESTO_PATH)
        st.dataframe(df_man.tail(50), use_container_width=True, height=250)

# =============================================================================
# TAB 3: CATÁLOGOS Y DOCUMENTACIÓN
# =============================================================================
with tab_catalogos:
    st.subheader("Catálogos Institucionales del PJUD")

    col_cat1, col_cat2 = st.columns(2)

    with col_cat1:
        st.markdown("##### 🏛️ Cortes de Apelaciones (`cortes.csv`)")
        st.dataframe(cargar_catalogo_cortes(), use_container_width=True, height=300)

    with col_cat2:
        st.markdown(f"##### 📋 Tribunales en C.A. Valparaíso (`tribunales.csv`)")
        df_trib = cargar_catalogo_tribunales()
        if not df_trib.empty and "corte" in df_trib.columns:
            trib_valpo = df_trib[df_trib["corte"] == cod_corte].reset_index(drop=True)
            st.dataframe(trib_valpo, use_container_width=True, height=300)
        else:
            st.info("Catálogo de tribunales no encontrado.")

    st.markdown("---")
    st.markdown("### 💻 Modo de Uso por Consola (CLI)")
    st.markdown("Para ejecutar la ingesta de forma desatendida o programada en un entorno de producción:")
    st.code(
        f"""python src/Api_Caller/explorar_pjud.py \\
  --swagger src/Api_Caller/swagger.json \\
  --competencia Familia Laboral "Oral en lo Penal" \\
  --corte {cod_corte} \\
  --tribunal 0 \\
  --desde {anio_min} \\
  --hasta {anio_max} \\
  --out data/raw \\
  --endpoints {" ".join(endpoints_seleccionados)}""",
        language="bash"
    )

    st.markdown("### 📁 Archivos Parquet Generados")
    archivos_pq = list(PARQUET_DIR.glob("*.parquet"))
    if archivos_pq:
        datos_pq = []
        for p in archivos_pq:
            datos_pq.append({
                "Archivo": p.name,
                "Tamaño (MB)": round(p.stat().st_size / (1024 * 1024), 2),
                "Ruta Absoluta": str(p)
            })
        st.table(pd.DataFrame(datos_pq))

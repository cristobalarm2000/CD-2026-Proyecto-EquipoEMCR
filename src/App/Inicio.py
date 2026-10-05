import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------------------------------------------------------
# 1. Configuración global de la aplicación
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Poder Judicial - Estudio de Audiencias (MVP Familia)",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 2. Definición de la página de Inicio
# -----------------------------------------------------------------------------
def pagina_inicio():
    st.title("⚖️ Poder Judicial de Chile")
    st.subheader("Plataforma de Inteligencia Judicial & Eficiencia Procesal (Equipo EMCR)")

    st.markdown("""
    Esta plataforma está orientada al **estudio, auditoría y análisis exploratorio integral de las Audiencias Realizadas** 
    en el **Poder Judicial de Chile (PJUD)**. Actualmente, el proyecto opera en modalidad **Producto Mínimo Viable (MVP)**, 
    focalizado en la competencia de **Familia** para la **Corte de Apelaciones de Valparaíso (Código 30)**.

    ---
    ### 🎯 Enfoque Estratégico del MVP
    El propósito central de esta fase es **validar de extremo a extremo la metodología y los pipelines** de extracción vía API, 
    tipificación estricta, compresión columnar (Apache Parquet) y auditoría de calidad de datos sobre una materia de alta 
    demanda ciudadana como es **Familia** (2015–2025).

    **Meta de Escalamiento:** Conforme a los resultados y validaciones técnicas obtenidas en este MVP, la metodología 
    se extenderá progresivamente para aplicar este mismo análisis de audiencias a la **mayor cantidad de materias judiciales** 
    posibles (Laboral, Penal/TOP y Civil) a nivel regional y nacional.
    """)

    # Ficha técnica y métricas del MVP
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("🏛️ Jurisdicción MVP", "Corte Valparaíso", "Código 30 (34 tribunales)")
    with c2:
        st.metric("📅 Horizonte Temporal", "2015 – 2025", "11 períodos anuales")
    with c3:
        st.metric("📊 Audiencias Auditadas", "466,178 filas", "128,401 causas únicas")
    with c4:
        st.metric("⚡ Compresión Parquet", "96.8% de ahorro", "238.9 MB → 7.71 MB")

    st.markdown("---")

    col_izq, col_der = st.columns(2)
    with col_izq:
        st.info("""
        #### 🧪 Alcance Actual: Validación en Familia
        - **Entidad:** `audiencias_realizadas_competencia_detalle`.
        - **Cobertura Territorial:** 34 juzgados con competencia de Familia en la V Región (Viña del Mar, Valparaíso, Quillota, etc.).
        - **Pipeline Validado:** Ingesta REST con política de reintentos, tipado fuerte (`Int64`, `datetime64[ns]`) y detección forense de inconsistencias.
        - **Integridad Verificada:** 0 duplicados exactos (0,0%) y 12 variables con 100% de exhaustividad.
        """)

    with col_der:
        st.success("""
        #### 🚀 Hoja de Ruta: Expansión Multi-Materia
        - **Paso 1 (Actual):** Consolidación de ETL, auditoría y análisis exploratorio (EDA) en **Familia**.
        - **Paso 2:** Replicar pipeline de audiencias en **Laboral** (Juzgados de Letras del Trabajo).
        - **Paso 3:** Adaptar modelos a **Penal** (Tribunales de Juicio Oral en lo Penal - TOP y Garantía).
        - **Paso 4:** Integrar materia **Civil** y construir el comparador transversal de eficiencia procesal.
        """)

    st.markdown("""
    ---
    ### 🧭 Cómo Navegar por la Plataforma
    Usa el **menú en la barra lateral izquierda** para acceder a los módulos del proyecto:
    - **`Inicio`**: Portada institucional, contexto estratégico del MVP y hoja de ruta de escalamiento.
    - **`1.- Ingesta de Datos`**: Módulo interactivo de extracción desde la API estadística del PJUD, monitoreo de descargas y consolidación a Parquet.
    - **`2.- ETL`**: Publicación interactiva fiel del cuaderno técnico [`01 ETL_audienciasparquet.ipynb`](notebooks), que comprende la carga del Parquet y la auditoría exhaustiva de calidad (dimensiones, perfiles de nulos, frecuencias categóricas, variables numéricas/temporales y missingness).
    """)

# -----------------------------------------------------------------------------
# 3. Configuración de Navegación Multi-página (Streamlit Navigation)
# -----------------------------------------------------------------------------
pagina_home = st.Page(pagina_inicio, title="Inicio", icon="🏠", default=True)
pagina_ingesta = st.Page("pages/1.- Ingesta de Datos.py", title="1.- Ingesta de Datos", icon="📥")
pagina_etl = st.Page("pages/2.- ETL.py", title="2.- ETL", icon="📊")

pg = st.navigation({
    "Menú Principal": [pagina_home, pagina_ingesta, pagina_etl]
})

# -----------------------------------------------------------------------------
# 4. Información institucional en la barra lateral común
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🏛️ Poder Judicial")
    st.caption("Jurisdicción Valparaíso (Corte 30)")
    st.caption("**Modo MVP:** Competencia Familia")
    st.caption("Objetivo: Expansión Multi-Materia")
    st.markdown("---")

pg.run()
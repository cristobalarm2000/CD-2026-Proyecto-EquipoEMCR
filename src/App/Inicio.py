import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------------------------------------------------------
# 1. Configuración global de la aplicación
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Poder Judicial - Estudio de Audiencias (Nacional Familia)",
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
    en el **Poder Judicial de Chile (PJUD)**. En esta versión a **Escala Nacional**, el pipeline abarca la totalidad de las 
    **17 Cortes de Apelaciones del país** en la competencia de **Familia**, procesando la serie histórica completa (2015–2025).

    ---
    ### 🎯 Enfoque Estratégico Nacional
    El propósito central de esta fase es **escalar la metodología y los pipelines validados en el MVP** (extracción vía API, 
    tipificación estricta, cruce oficial con estadísticas PJUD, compresión columnar Apache Parquet y auditoría forense de calidad) 
    a nivel de **todo el territorio nacional** para la materia de alta demanda ciudadana **Familia**.

    **Meta de Expansión:** Con la cobertura nacional de Familia consolidada (3.52 millones de audiencias), 
    la arquitectura está preparada para extenderse hacia las materias **Laboral, Penal/TOP y Civil**.
    """)

    # Ficha técnica y métricas Nacionales
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("🏛️ Cobertura Nacional", "17 Cortes de Apelaciones", "141 tribunales de Familia")
    with c2:
        st.metric("📅 Horizonte Temporal", "2015 – 2025", "11 períodos anuales")
    with c3:
        st.metric("📊 Audiencias Auditadas", "3,526,516 filas", "2,266,379 causas únicas")
    with c4:
        st.metric("⚡ Almacenamiento Parquet", "82.5 MB en disco", "36 variables (100% completitud)")

    st.markdown("---")

    col_izq, col_der = st.columns(2)
    with col_izq:
        st.info("""
        #### 🧪 Alcance Consolidado: Nivel Nacional Familia
        - **Entidad:** `audiencias_realizadas_competencia_detalle`.
        - **Cobertura Territorial:** 141 juzgados canónicos con competencia de Familia en las 16 regiones de Chile (Arica a Punta Arenas).
        - **Pipeline Validado:** Cruce del lote anómalo 2023 con fuente oficial PJUD (350.149 causas recuperadas), resolución de formatos horarios, coherencia cronológica y tipado fuerte (`Int64`, `datetime64[ns]`).
        - **Integridad Verificada:** 0 duplicados exactos (0,0%) y 36 variables de modelo con 100% de exhaustividad (0 nulos).
        """)

    with col_der:
        st.success("""
        #### 🚀 Hoja de Ruta: Expansión Multi-Materia
        - **Paso 1 (Consolidado):** ETL, auditoría y análisis exploratorio (EDA) de **Familia a Nivel Nacional**.
        - **Paso 2:** Replicar pipeline de audiencias en **Laboral** (Juzgados de Letras del Trabajo).
        - **Paso 3:** Adaptar modelos a **Penal** (Tribunales de Juicio Oral en lo Penal - TOP y Garantía).
        - **Paso 4:** Integrar materia **Civil** y construir el comparador transversal de eficiencia procesal.
        """)

    st.markdown("""
    ---
    ### 🧭 Cómo Navegar por la Plataforma
    Usa el **menú en la barra lateral izquierda** para acceder a los módulos del proyecto:
    - **`Inicio`**: Portada institucional, contexto estratégico nacional y hoja de ruta de escalamiento.
    - **`1.- Ingesta de Datos`**: Módulo interactivo de extracción desde la API estadística del PJUD, monitoreo de descargas y consolidación a Parquet.
    - **`2.- Notebook ETL`**: Publicación interactiva del cuaderno técnico [`01 ETL_audienciasparquet.ipynb`](notebooks) con el código ejecutable de las 7 fases de limpieza, imputación y persistencia nacional.
    - **`3.- Informe ETL`**: Informe ejecutivo interactivo enfocado en los **hallazgos forenses y decisiones estratégicas** adoptadas durante el saneamiento del dataset nacional.
    - **`4.- Dashboard BI`**: Tablero ejecutivo de Business Intelligence orientado a estudios jurídicos (con filtros por Corte, Tribunal, Macro-materia, año y modalidad telemática).
    """)

# -----------------------------------------------------------------------------
# 3. Configuración de Navegación Multi-página (Streamlit Navigation)
# -----------------------------------------------------------------------------
pagina_home = st.Page(pagina_inicio, title="Inicio", icon="🏠", default=True)
pagina_ingesta = st.Page("pages/1.- Ingesta de Datos.py", title="1.- Ingesta de Datos", icon="📥")
pagina_notebook_etl = st.Page("pages/2.- Notebook ETL.py", title="2.- Notebook ETL", icon="📊")
pagina_informe_etl = st.Page("pages/3.- Informe ETL.py", title="3.- Informe ETL", icon="📋")
pagina_dashboard = st.Page("pages/4.- Dashboard BI.py", title="4.- Dashboard BI", icon="📈")

pg = st.navigation({
    "Menú Principal": [pagina_home, pagina_ingesta, pagina_notebook_etl, pagina_informe_etl, pagina_dashboard]
})

# -----------------------------------------------------------------------------
# 4. Información institucional en la barra lateral común
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🏛️ Poder Judicial")
    st.caption("Jurisdicción Nacional (17 Cortes)")
    st.caption("**Competencia:** Familia (2015–2025)")
    st.caption("Objetivo: Expansión Multi-Materia")
    st.markdown("---")

pg.run()
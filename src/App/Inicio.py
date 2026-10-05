import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. Configuración global de la aplicación
st.set_page_config(
    page_title="Poder Judicial - Estudio de Audiencias",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Definición de la página de Inicio
def pagina_inicio():
    st.title("⚖️ Poder Judicial de Chile")
    st.subheader("Plataforma de Analítica de Audiencias Judiciales (Equipo EMCR)")

    st.markdown("""
    Esta plataforma está orientada al **estudio, auditoría y análisis exploratorio integral de las Audiencias Realizadas** 
    en el **Poder Judicial de Chile (PJUD)**, enfocado en la **Corte de Apelaciones de Valparaíso (Código 30)**.

    ---
    ### 🎯 Objetivos Estratégicos del Proyecto
    - **Demanda y Carga Procesal:** Cuantificar el volumen histórico de audiencias por tribunal y materia (Familia, Laboral y Penal TOP).
    - **Eficiencia y Tiempos:** Evaluar los plazos de agendamiento y la duración efectiva de las audiencias.
    - **Adopción Tecnológica:** Analizar el impacto de la virtualidad (videoconferencias) y la presencialidad entre 2015 y 2025.
    """)

    col1, col2 = st.columns(2)
    with col1:
        st.info("""
        #### 📥 Ingesta y Exploración de Microdatos
        - **Fuente:** API oficial de estadísticas del PJUD (`/pjen/audiencias_realizadas_...`).
        - **Jurisdicción:** Corte de Apelaciones de Valparaíso (34 tribunales).
        - **Cobertura:** 2015 a 2025 (serie histórica continua).
        - **Formato:** Apache Parquet optimizado (Snappy).
        """)

    with col2:
        st.success("""
        #### 📊 Inteligencia y Análisis del Negocio
        - **Monitoreo de Congestión:** Comparativas directas entre tribunales de la región.
        - **Patrones de Programación:** Plazos de espera entre ingreso, programación y realización.
        - **Perfiles por Materia:** Análisis granular por tipo de procedimiento y audiencia.
        """)

    st.markdown("""
    ---
    ### 🚀 Cómo Navegar
    - Usa el **menú en la barra lateral izquierda**:
      - `1.- Ingesta de Datos`: Para consultar microdatos desde la API PJUD, gestionar descargas y explorar el dataset Parquet consolidado en tiempo real.
    """)

# 3. Configuración de Navegación Multi-página (Streamlit Navigation)
pagina_home = st.Page(pagina_inicio, title="Inicio", icon="🏠", default=True)
pagina_ingesta = st.Page("pages/1.- Ingesta de Datos.py", title="1.- Ingesta de Datos", icon="📥")

pg = st.navigation({
    "Menú Principal": [pagina_home, pagina_ingesta]
})

# 4. Información institucional en la barra lateral común
with st.sidebar:
    st.markdown("### 🏛️ Poder Judicial")
    st.caption("Jurisdicción Valparaíso (Corte 30)")
    st.caption("Estudio Focalizado: Audiencias")
    st.markdown("---")

pg.run()
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Configuración de la página
st.set_page_config(
    page_title="Poder Judicial - Ciencia de Datos",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Poder Judicial de Chile")
st.subheader("Plataforma de Analítica y Ciencia de Datos Judicial (Equipo EMCR)")

st.markdown("""
Esta plataforma permite explorar, analizar y modelar los datos abiertos del **Poder Judicial de Chile (PJUD)**.
Comprende la extracción de microdatos estadísticos de causas, audiencias y términos a través de la API oficial del PJUD.

---
### 📌 Módulos Disponibles en la Barra Lateral
""")

col1, col2 = st.columns(2)
with col1:
    st.info("""
    #### 📥 1.- Ingesta de Datos
    - **Extracción automatizada** desde la API de estadísticas del PJUD.
    - **Jurisdicción:** Corte de Apelaciones de Valparaíso (Código 30).
    - **Materias:** Familia, Laboral y Oral en lo Penal (TOP).
    - **Período:** 2020 a 2025 (más de 3.67 millones de registros).
    - **Compresión columnar:** Apache Parquet de alto rendimiento.
    """)

with col2:
    st.success("""
    #### 🚀 Cómo Navegar
    - Usa el **menú de páginas en la barra lateral izquierda** para ingresar al módulo `1.- Ingesta de Datos`.
    - Podrás explorar gráficos temporales interactivos, filtrar por tribunal o materia, probar la conexión de la API y descargar los microdatos consolidados.
    """)
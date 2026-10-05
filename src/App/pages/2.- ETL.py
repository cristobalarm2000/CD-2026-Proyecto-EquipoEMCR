from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# -----------------------------------------------------------------------------
# Configuración de Página
# -----------------------------------------------------------------------------
try:
    st.set_page_config(
        page_title="2.- ETL Audiencias",
        page_icon="⚖️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
except Exception:
    pass

# -----------------------------------------------------------------------------
# Localización del Dataset
# -----------------------------------------------------------------------------
CURRENT_DIR = Path(__file__).resolve().parent
BASE_DIR = None
for p in [CURRENT_DIR] + list(CURRENT_DIR.parents):
    if (p / "data").exists() and (p / "src").exists():
        BASE_DIR = p
        break
if BASE_DIR is None:
    BASE_DIR = Path(r"C:\Users\frero\CD-2026-Proyecto-EquipoEMCR")

PARQUET_PATH = BASE_DIR / "data" / "raw" / "parquet" / "audiencias_realizadas_competencia_detalle.parquet"

@st.cache_data(show_spinner=False)
def cargar_datos():
    if PARQUET_PATH.exists():
        return pd.read_parquet(PARQUET_PATH)
    return pd.DataFrame()

df = cargar_datos()

# -----------------------------------------------------------------------------
# Barra Lateral
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/Poder_Judicial_de_Chile_%28logo%29.svg/1200px-Poder_Judicial_de_Chile_%28logo%29.svg.png", width=140)
    st.title("Notebook ETL")
    st.caption("Origen: `01 ETL_audienciasparquet.ipynb`")
    st.caption("Materia: **Familia** (Corte 30 Valparaíso)")
    st.markdown("---")
    st.markdown("""
    **Índice del Cuaderno:**
    - 1.- Carga de Datos
    - 2.- Auditoría de Datos
      - 2.1.- Dimensión, tipos y duplicados
      - 2.2.- Perfil de Calidad
      - 2.3.- Auditoría de inconsistencias
      - 2.4.- Auditoría numéricas y fechas
      - 2.5.- Visualización de % Nulos
    """)

# -----------------------------------------------------------------------------
# 1.- Carga de Datos
# -----------------------------------------------------------------------------
st.title("1.- Carga de Datos")
st.markdown("Carga de archivo **audiencias_realizadas_competencia_detalle.parquet**, consolidado de consultas mediante Api PJUD.")

st.code(f"""import pandas as pd

df = pd.read_parquet(r"{PARQUET_PATH}")
df.head()""", language="python")

if df.empty:
    st.error(f"No se encontró el archivo Parquet en: `{PARQUET_PATH}`. Verifique la ruta de descarga.")
    st.stop()

st.dataframe(df.head(), use_container_width=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# 2.- Auditoría de Datos
# -----------------------------------------------------------------------------
st.title("2.- Auditoría de Datos")
st.markdown("""
Revisión técnica de la calidad, integridad y consistencia del dataset consolidado de audiencias. Comprende la verificación de dimensiones y duplicados, perfil de valores nulos, auditoría de variables categóricas, validación de variables numéricas y formatos de fecha, y visualización final de exhaustividad.
""")

# -----------------------------------------------------------------------------
# 2.1.- Dimensión, tipos de datos y duplicados exactos
# -----------------------------------------------------------------------------
st.header("### 2.1.- Dimensión, tipos de datos y duplicados exactos")

col_dim1, col_dim2, col_dim3, col_dim4 = st.columns(4)
with col_dim1:
    st.metric("Filas (Shape)", f"{df.shape[0]:,}")
with col_dim2:
    st.metric("Columnas (Shape)", f"{df.shape[1]}")
with col_dim3:
    st.metric("Duplicados exactos", f"{df.duplicated().sum()}")
with col_dim4:
    st.metric("RIT repetidos", f"{df['RIT'].duplicated().sum():,}")

st.markdown("**Tipos detectados por pandas (`df.dtypes.to_frame('dtype')`):**")
st.dataframe(df.dtypes.to_frame("dtype"), use_container_width=True, height=320)

st.markdown("---")

# -----------------------------------------------------------------------------
# 2.2.- Perfil de Calidad
# -----------------------------------------------------------------------------
st.header("### 2.2.- Perfil de Calidad")
st.markdown("Perfil rápido de calidad (ordenado descendentemente por `% nulos`):")

perfil = pd.DataFrame({
    "dtype": df.dtypes.astype(str),
    "nulos": df.isna().sum(),
    "% nulos": (df.isna().mean() * 100).round(1),
    "n_unicos": df.nunique(dropna=True)
}).sort_values("% nulos", ascending=False)

st.dataframe(perfil, use_container_width=True, height=450)

st.markdown("---")

# -----------------------------------------------------------------------------
# 2.3.- Auditoría de inconsistencias y frecuencias de valores
# -----------------------------------------------------------------------------
st.header("### 2.3.- Auditoría de inconsistencias y frecuencias de valores")
st.markdown("Inspección de las columnas seleccionadas para auditoría (`value_counts(dropna=False).head(15)`):")

columnas_revision = [
    "CORTE", "TRIBUNAL", "RIT", "TIPO_PROCEDIMIENTO",
    "TIPO_AUDIENCIA", "HORA_INICIO", "HORA_FIN",
    "COMPETENCIA", "RUC", "VIDEOCONFERENCIA"
]

# Modo interactivo y pestañas por variable
col_tabs = st.tabs([f"📌 {col}" for col in columnas_revision])

for idx, col in enumerate(columnas_revision):
    with col_tabs[idx]:
        st.subheader(f"Columna: `{col}`")
        conteos = df[col].value_counts(dropna=False).head(15).reset_index()
        conteos.columns = [col, "count"]
        st.dataframe(conteos, use_container_width=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# 2.4.- Auditoría de columnas numéricas y consistencia de fechas (datetime64[ns])
# -----------------------------------------------------------------------------
st.header("### 2.4.- Auditoría de columnas numéricas y consistencia de fechas (datetime64[ns])")

# 1. Auditoría de columnas numéricas (Int64, int64, float64)
st.markdown("#### 1. Auditoría de columnas numéricas (`Int64`, `int64`, `float64`)")
cols_numericas = df.select_dtypes(include=['number']).columns.tolist()

resumen_num = pd.DataFrame({
    'dtype': df[cols_numericas].dtypes.astype(str),
    'nulos': df[cols_numericas].isna().sum(),
    'min': df[cols_numericas].min(),
    'max': df[cols_numericas].max(),
    'valores_unicos': df[cols_numericas].nunique(),
    'tiene_decimales': [
        (df[c].dropna() % 1 != 0).any() if df[c].dtype == 'float64' else False
        for c in cols_numericas
    ]
})

st.dataframe(resumen_num, use_container_width=True)

# 2. Auditoría de columnas datetime64[ns]
st.markdown("#### 2. Auditoría de columnas `datetime64[ns]`")
cols_fechas = df.select_dtypes(include=['datetime64[ns]']).columns.tolist()

resumen_fechas = []
for col in cols_fechas:
    serie = df[col].dropna()
    tiene_hora = (serie.dt.hour != 0) | (serie.dt.minute != 0) | (serie.dt.second != 0)
    resumen_fechas.append({
        'columna': col,
        'dtype': str(df[col].dtype),
        'nulos': df[col].isna().sum(),
        '% nulos': round(df[col].isna().mean() * 100, 2),
        'fecha_min': serie.min(),
        'fecha_max': serie.max(),
        'tiene_horas': bool(tiene_hora.any()),
        'ejemplo_iso': str(serie.iloc[0]) if len(serie) > 0 else 'N/A'
    })

st.dataframe(pd.DataFrame(resumen_fechas), use_container_width=True)

# 3. Muestra de fechas en formato ISO y formato dd-mm-aaaa
st.markdown("#### 3. Comparación de Formato: ISO (estándar pandas) vs DD-MM-AAAA")
fechas_muestra = df[cols_fechas].dropna().head(5)

col_f_iso, col_f_dd = st.columns(2)
with col_f_iso:
    st.markdown("**Formato ISO (estándar pandas):**")
    st.dataframe(fechas_muestra, use_container_width=True)

with col_f_dd:
    st.markdown("**Representación explícita en `dd-mm-aaaa`:**")
    st.dataframe(fechas_muestra.apply(lambda s: s.dt.strftime('%d-%m-%Y')), use_container_width=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# 2.5.- Visualización de % Nulos por Columna
# -----------------------------------------------------------------------------
st.header("### 2.5.- Visualización de % Nulos por Columna")

missing = df.isna().mean().sort_values(ascending=False) * 100
missing = missing[missing > 0]

fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(missing.index, missing.values, color="#1f77b4")
ax.set_ylabel("% de valores faltantes")
plt.xticks(rotation=35, ha="right")
ax.set_title("Missingness por variable")
plt.tight_layout()

st.pyplot(fig)

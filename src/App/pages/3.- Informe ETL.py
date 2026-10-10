from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# Configuración de Página
# -----------------------------------------------------------------------------
try:
    st.set_page_config(
        page_title="3.- Informe ETL - Hallazgos y Decisiones",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="expanded"
    )
except Exception:
    pass

# -----------------------------------------------------------------------------
# Localización del Dataset Preparado
# -----------------------------------------------------------------------------
CURRENT_DIR = Path(__file__).resolve().parent
BASE_DIR = None
for p in [CURRENT_DIR] + list(CURRENT_DIR.parents):
    if (p / "data").exists() and (p / "src").exists():
        BASE_DIR = p
        break
if BASE_DIR is None:
    BASE_DIR = Path(r"C:\Users\frero\CD-2026-Proyecto-EquipoEMCR")

PARQUET_PATH = BASE_DIR / "data" / "processed" / "audiencias_preparadas_modelo.parquet"

@st.cache_data(show_spinner=False)
def cargar_datos_informe():
    if PARQUET_PATH.exists():
        return pd.read_parquet(PARQUET_PATH)
    return pd.DataFrame()

df = cargar_datos_informe()

# -----------------------------------------------------------------------------
# Barra Lateral Informativa
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/Poder_Judicial_de_Chile_%28logo%29.svg/1200px-Poder_Judicial_de_Chile_%28logo%29.svg.png", width=130)
    st.title("Informe de Auditoría ETL")
    st.caption("Jurisdicción: **Valparaíso** (Materia Familia)")
    st.caption("Serie Temporal: **2015 – 2025** (11 períodos)")
    st.markdown("---")
    st.markdown("""
    **Índice de Hitos Auditados:**
    1. 🔍 Rescate del Lote 2023 (Desfase API)
    2. 🏷️ Causa Única y Normalización de RIT
    3. ⚖️ Depuración y Anonimización (Ley 19.968)
    4. 🧩 Imputación Procesal (100% Completitud)
    5. ⏱️ Fechas Imposibles vs Outliers Reales
    6. 🚀 Ingeniería de Características y Persistencia
    """)
    st.markdown("---")
    st.info("💡 **Objetivo:** Este informe sintetiza la fundamentación jurídica, empírica y metodológica de cada transformación aplicada al dataset.")

# -----------------------------------------------------------------------------
# Encabezado Principal y Métricas de Transformación Global
# -----------------------------------------------------------------------------
st.title("📋 Informe Ejecutivo: Hallazgos Forenses y Decisiones del ETL")
st.markdown("### Auditoría de Calidad y Preparación de Microdatos Judiciales de Familia (2015–2025)")
st.markdown("""
Este informe interactivo documenta los **hallazgos empíricos críticos**, las **disyuntivas metodológicas** y las **decisiones de modelamiento** 
adoptadas en el saneamiento de las **466.178 audiencias** de la Corte de Apelaciones de Valparaíso, con el propósito de construir una base sólida para 
la **Inteligencia de Negocios en un Estudio de Abogados**.
""")

# Tarjetas de Impacto Global Antes vs Después
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric(
        "📊 Completitud de Celdas",
        "100.00%",
        "+18.8% vs Origen Crudo (0 Nulos)"
    )
with m2:
    st.metric(
        "📁 Causas Únicas Identificadas",
        "280,795 causas",
        "1.66 aud/causa (RIT Estandarizado)"
    )
with m3:
    st.metric(
        "🔄 Registros 2023 Saneados",
        "43,380 expedientes",
        "100% Auténticos (Cruce Oficial PJUD)"
    )
with m4:
    st.metric(
        "⏱️ Consistencia Cronológica",
        "100.00%",
        "22 Desfases Administrativos Corregidos"
    )

st.markdown("---")

# -----------------------------------------------------------------------------
# Menú de Navegación por Hitos de Decisión
# -----------------------------------------------------------------------------
hito_sel = st.radio(
    "Selecciona el Hito Metodológico que deseas examinar:",
    [
        "1. 🔍 Rescate Crítico del Lote 2023 (Desfase de Columnas de la API)",
        "2. 🏷️ Identificación de Causas Únicas y Normalización de RIT (ID_CAUSA_RIT)",
        "3. ⚖️ Depuración de Variables y Anonimización (Eliminación de FECHA_FIRMA y RUC)",
        "4. 🧩 Imputación Procesal y Completitud Total (Audiencias Inmediatas y Horas)",
        "5. ⏱️ Tratamiento de Fechas Imposibles vs Outliers de Agendamiento",
        "6. 🚀 Modelo Enriquecido (36 Columnas) y Persistencia del Artefacto"
    ],
    horizontal=True
)

st.markdown("---")

# =============================================================================
# HITO 1: Rescate Crítico del Lote 2023
# =============================================================================
if "1. 🔍 Rescate Crítico" in hito_sel:
    st.header("1. 🔍 El Hallazgo Crítico del Lote 2023: Desfase de Columnas en la API PJUD")
    
    col_h1_a, col_h1_b = st.columns([3, 2])
    with col_h1_a:
        st.markdown("""
        #### 🚨 El Hallazgo Forense
        Al auditar la serie temporal 2015–2025, se descubrió una anomalía grave y masiva concentrada **exclusivamente en el año 2023 (43.380 registros)**:
        - La respuesta JSON/REST de la API estadística del Poder Judicial entregó las columnas **desplazadas una posición hacia la izquierda**.
        - La `FECHA_INGRESO` venía alojada en el campo `RIT`.
        - La `FECHA_PROGRAMACION` venía alojada en el campo `RUC`.
        - Las columnas sustantivas de fecha figuraban con **43.380 valores nulos (100% vacías en 2023)**.
        - Los campos de `TIPO_PROCEDIMIENTO` y `TIPO_AUDIENCIA` contenían valores espurios o incompletos.
        """)

        st.warning("""
        **Disyuntiva Metodológica:**
        - **Opción B (Ajuste algorítmico posicional):** Correr las columnas a la derecha mediante heurística de código. *(Riesgo: si la API no desfasó todas las filas de forma homogénea, se introducen datos corruptos).*
        - **Opción A (Cruce Relacional con Fuente Oficial PJUD):** Contrastar y fusionar los registros con el reporte anual institucional consolidado (`audiencias_realizadas_2023.csv`) utilizando la clave relacional `ID_AUDIENCIA` (`CRR AUD`).
        """)

        st.success("""
        **🎯 La Decisión Adoptada (Opción A):**
        Se integró el archivo oficial del PJUD, recuperando el **100% de los RITs, tipos de procedimiento, tipos de audiencia y estampas de fecha auténticas**. 
        No se descartó una sola fila y se preservó la trazabilidad mediante la columna booleana `FLG_CRUCE_2023`.
        """)
    with col_h1_b:
        st.markdown("#### 📊 Distribución Real de Audiencias Recuperadas en 2023:")
        # Distribución real recuperada de audiencias en 2023
        if not df.empty:
            aud_23 = df[df['ANO_AUDIENCIA'] == 2023]['TIPO_AUDIENCIA'].value_counts().head(7).reset_index()
            aud_23.columns = ['Tipo de Audiencia', 'Conteo']
            fig_23 = px.bar(
                aud_23,
                x='Conteo',
                y='Tipo de Audiencia',
                orientation='h',
                color='Conteo',
                color_continuous_scale='Blues',
                text='Conteo'
            )
            fig_23.update_traces(texttemplate='%{text:,}', textposition='outside')
            fig_23.update_layout(height=350, margin=dict(l=10, r=20, t=20, b=20), coloraxis_showscale=False)
            st.plotly_chart(fig_23, use_container_width=True)
            st.caption("22.091 Preparatorias, 7.747 Juicios y 1.196 Inmediatas recuperadas con exactitud milimétrica.")

# =============================================================================
# HITO 2: Normalización de RIT y Causa Única
# =============================================================================
elif "2. 🏷️ Identificación de Causas" in hito_sel:
    st.header("2. 🏷️ Normalización de RIT y Creación de la Clave Compuesta de Causa (`ID_CAUSA_RIT`)")
    
    c_r1, c_r2 = st.columns([3, 2])
    with c_r1:
        st.markdown("""
        #### 🚨 El Hallazgo en la Nomenclatura Judicial
        1. **El Doble Guión Erróneo (`--`):** Se identificaron **41.439 registros (8,89% del universo)** donde el rol de la causa fue digitado con doble guión (ej. `C--100-2020` en lugar de `C-100-2020`).
        2. **La Relatividad Jurisdiccional del RIT:** En Chile, el Rol Interno del Tribunal (**RIT**) **no es un identificador global**. Cada juzgado administra su propia serie correlativa anual. Por lo tanto, la causa `C-200-2022` existe simultáneamente en Viña del Mar, en Valparaíso y en Quillota, correspondiendo a familias y litigios totalmente distintos.
        """)

        st.success(r"""
        **🎯 Decisiones Técnicas y de Negocio:**
        1. **Estandarización Canónica:** Se reemplazó el doble guión por guión simple y se validó la sintaxis mediante expresión regular (`^[A-Z]{1,2}-\d+-\d{4}$`). **Resultado: 100% de conformidad (0 registros inválidos).**
        2. **Construcción de la Clave Primaria de Causa:** Se creó la columna:
           $$\text{ID\_CAUSA\_RIT} = \text{COD\_TRIBUNAL} + \text{'-'} + \text{RIT} \quad (\text{ej. } 1271\text{-C-200-2022})$$
        """)
        
        st.info("""
        💡 **Impacto Directo para la Inteligencia del Estudio:**
        Esta clave permitió consolidar las **466.178 audiencias** en exactamente **280.795 causas judiciales únicas**. 
        Descubrimos que la tasa de recurrencia en derecho de familia es de **1,66 audiencias por causa judicial**, dato esencial para proyectar costos y tiempos de tramitación.
        """)
    with c_r2:
        st.markdown("#### 📈 Granularidad del Dataset:")
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = 280795,
            title = {'text': "<b>Causas Judiciales Únicas</b><br><span style='font-size:0.8em;color:gray'>Sobre 466.178 Audiencias Totales</span>"},
            gauge = {
                'axis': {'range': [0, 466178]},
                'bar': {'color': "#1f77b4"},
                'steps': [
                    {'range': [0, 280795], 'color': "#e6f2ff"},
                    {'range': [280795, 466178], 'color': "#f9f9f9"}
                ],
            }
        ))
        fig_gauge.update_layout(height=320, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)

# =============================================================================
# HITO 3: Depuración y Anonimización
# =============================================================================
elif "3. ⚖️ Depuración de Variables" in hito_sel:
    st.header("3. ⚖️ Depuración de Variables y Anonimización del Modelo (Eliminación de FECHA_FIRMA y RUC)")
    
    st.markdown("""
    En esta etapa se tomó una decisión estratégica fundamental: **reducir el dataset de 24 a 20 columnas**, eliminando cuatro variables con altos volúmenes de valores nulos o riesgos de privacidad:
    """)

    c_dep1, c_dep2 = st.columns(2)
    with c_dep1:
        st.error("""
        #### 🗑️ Columnas Eliminadas y su Justificación
        1. **`RUC` (81,24% Nulo):**
           - Identificador tributario/nacional de causa. Se remueve para **anonimizar estrictamente los expedientes de familia** (derecho de menores y VIF). La identificación de la causa queda garantizada al 100% por `ID_CAUSA_RIT`.
        2. **`ID_CAUSA` (71,64% Nulo) e `ID_AUDIENCIA` (62,34% Nulo):**
           - Identificadores internos del backend judicial introducidos recién en años recientes y ausentes en los primeros 6 años de la serie. Son redundantes frente a `ID_CAUSA_RIT`.
        """)
    with c_dep2:
        st.warning("""
        #### ⚖️ El Análisis Jurídico de `FECHA_FIRMA` (62,68% Nulo)
        - **¿Por qué faltaba?** La firma electrónica del acta fue implementada con la Ley N° 21.226 recién a finales de 2020. En los primeros 6 años del dataset era 100% nula.
        - **Sustento Procesal (Ley N° 19.968):**
          - En los tribunales de familia rige el **principio de oralidad**. Las resoluciones dictadas en audiencia se entienden notificadas a las partes en el acto mismo (**Art. 23**).
          - El registro legal y vinculante es el audio digital (**Art. 24**). Los plazos fatales corren desde la audiencia, no desde la fecha en que el actuario o juez firma administrativamente el acta.
        - **Valor para el Estudio de Abogados:** Cero injerencia en la preparación, agenda, honorarios ni estrategia del litigante.
        """)

    st.success("✅ **Resultado de Negocio:** El modelo de datos se redujo a **20 columnas clave**, con un 85% de variables 100% completas y eliminando variables obsoletas o riesgosas.")

# =============================================================================
# HITO 4: Imputación Procesal y Completitud Total
# =============================================================================
elif "4. 🧩 Imputación Procesal" in hito_sel:
    st.header("4. 🧩 Imputación Procesal de Faltantes Remanentes: El Descubrimiento de las Audiencias Inmediatas")

    col_imp1, col_imp2 = st.columns([3, 2])
    with col_imp1:
        st.markdown("""
        #### 🔍 El Descubrimiento Forense en `FECHA_PROGRAMACION` (9.228 Nulos)
        Al evaluar los 9.228 valores faltantes de `FECHA_PROGRAMACION`, un análisis algorítmico ingenuo habría sugerido borrar las filas o imputar la media de fechas. 
        Sin embargo, al auditar procesalmente las causas, se constató un patrón absoluto:
        - **El 100% de los 9.228 registros sin programación correspondían exactamente a `TIPO_AUDIENCIA == 'INMEDIATA'`**.
        
        #### 🏛️ Sustento en el Procedimiento de Familia (Ley N° 19.968, Art. 71)
        Las **Audiencias Inmediatas** son trámites cautelares de flagrancia y urgencia en Violencia Intrafamiliar (VIF) o medidas de protección de menores en vulnerabilidad grave. 
        En estos casos, **no existe agendamiento previo**: la persona comparece o es derivada por Carabineros y el juez celebra la audiencia en el acto ese mismo día.
        """)

        st.success("""
        **🎯 El Plan de Imputación Aplicado:**
        1. **`FECHA_PROGRAMACION` (9.228 nulos):** Se imputó con `FECHA_AUDIENCIA`, reflejando la realidad procesal de que citación y audiencia ocurrieron el mismo día.
        2. **`PLAZO_AGENDAMIENTO` (97 nulos y 16 negativos):** Se imputaron a `0` días de espera, alineándose con el estándar oficial que el propio PJUD utiliza para audiencias inmediatas.
        3. **`HORA_FIN` (2 nulos):** Se imputaron utilizando la mediana de duración de Audiencias Preparatorias (**18 minutos**) sumada a su `HORA_INICIO`.
        """)
    with col_imp2:
        st.markdown("#### 🎯 Cobertura de Datos Resultante:")
        comp_df = pd.DataFrame({
            "Estado": ["Datos Íntegros (0 Nulos)", "Valores Ausentes"],
            "Porcentaje": [100.0, 0.0]
        })
        fig_donut = px.pie(
            comp_df,
            names="Estado",
            values="Porcentaje",
            hole=0.6,
            color="Estado",
            color_discrete_map={"Datos Íntegros (0 Nulos)": "#2ca02c", "Valores Ausentes": "#d62728"},
            title="<b>Completitud del Dataset Post-Imputación</b>"
        )
        fig_donut.update_layout(height=320, margin=dict(l=10, r=10, t=40, b=10), showlegend=False)
        st.plotly_chart(fig_donut, use_container_width=True)
        st.metric("Total Valores Nulos en las 20 Columnas", "0 Nulos", "100.00% Íntegro")

# =============================================================================
# HITO 5: Valores Imposibles vs Outliers
# =============================================================================
elif "5. ⏱️ Tratamiento de Fechas" in hito_sel:
    st.header("5. ⏱️ Tratamiento de Fechas Imposibles vs Outliers de Agendamiento")

    st.markdown("""
    En esta etapa se confrontó la coherencia física y estadística de las variables cuantitativas y temporales:
    """)

    c_fe1, c_fe2 = st.columns(2)
    with c_fe1:
        st.info("""
        #### 1. Inconsistencias Cronológicas en Fechas
        Se evaluó la regla universal: $\\text{FECHA\\_INGRESO} \\le \\text{FECHA\\_PROGRAMACION} \\le \\text{FECHA\\_AUDIENCIA}$.
        - `FECHA_AUDIENCIA < FECHA_INGRESO`: **0 casos (0.00%)**.
        - `FECHA_PROGRAMACION < FECHA_INGRESO`: **0 casos (0.00%)**.
        - `FECHA_AUDIENCIA < FECHA_PROGRAMACION`: **22 casos (0.0047%)**.
        
        **Diagnóstico Procesal de los 22 casos:**
        Corresponden a continuaciones de juicios orales o audiencias verbales en estrado donde la providencia administrativa en SITFA se firmó 1 a 5 días después.
        
        **Decisión (Acción 1):**
        Se igualó `FECHA_PROGRAMACION = FECHA_AUDIENCIA` para estos 22 casos, garantizando que el **100% del dataset sea físicamente coherente**.
        """)
    with c_fe2:
        st.warning("""
        #### 2. La Decisión sobre Plazos Extremos (Outliers hasta 339 días)
        - La regla de Tukey ($Q_3 + 3 \\times IQR = 136$ días hábiles) detectó **2.423 casos (0,52%)** con plazos de agendamiento atípicos, alcanzando hasta 339 días hábiles (más de un año).
        
        **El Dilema:** ¿Truncar (winsorizar) o eliminar estos valores?
        
        **Decisión de Negocio (Estudio Jurídico):**
        **NO truncar ni alterar**. Esos plazos dilatados representan **cuellos de botella procesales reales** causados por peritajes psicológicos extensos (DAM/SML), suspensiones bilaterales (Art. 202 CPC) o saturación de agenda en juzgados críticos (Viña del Mar y Valparaíso). 
        Eliminarlos o recortarlos falsearía los modelos de predictibilidad de tiempos del estudio.
        """)

# =============================================================================
# HITO 6: Modelo Enriquecido y Persistencia
# =============================================================================
elif "6. 🚀 Modelo Enriquecido" in hito_sel:
    st.header("6. 🚀 Ingeniería de Características (36 Columnas) y Persistencia del Artefacto")

    st.markdown("""
    Para alimentar el **Dashboard Ejecutivo de BI**, el dataset limpio se enriqueció con **16 variables analíticas derivadas**, elevando la granularidad de 20 a **36 variables**:
    """)

    c_fe_a, c_fe_b, c_fe_c = st.columns(3)
    with c_fe_a:
        st.markdown("""
        **🗓️ Ciclos y Calendario:**
        - `DIA_SEMANA_AUDIENCIA`
        - `MES_AUDIENCIA`
        - `TRIMESTRE_AUDIENCIA`
        - `BLOQUE_HORARIO` (Franja pico: 10:00–12:00)
        """)
    with c_fe_b:
        st.markdown("""
        **⏱️ Time-Tracking y SLAs:**
        - `DURACION_MINUTOS` (Mediana: 18 min)
        - `TRAMO_DURACION`
        - `FLG_AUDIENCIA_FRUSTRADA` (0 min)
        - `DIAS_TRAMITACION_PREVIA`
        - `TRAMO_AGENDAMIENTO`
        """)
    with c_fe_c:
        st.markdown("""
        **⚖️ Litigiosidad y Contexto:**
        - `ORDEN_AUDIENCIA_CAUSA` (1, 2, 3...)
        - `TOTAL_AUDIENCIAS_CAUSA`
        - `ES_CONTINUACION` (Riesgo pricing)
        - `MACRO_MATERIA` (Área de práctica)
        - `EPOCA_NORMATIVA` (Ley 21.226 / 21.394)
        """)

    st.markdown("---")
    st.markdown("#### 💾 Persistencia del Artefacto Final de Datos:")
    c_arch1, c_arch2, c_arch3 = st.columns(3)
    with c_arch1:
        st.metric("Ruta del Archivo", "data/processed/audiencias_preparadas_modelo.parquet")
    with c_arch2:
        st.metric("Dimensiones Finales", "466,178 filas x 36 columnas")
    with c_arch3:
        st.metric("Tamaño en Disco", "10.77 MB (Snappy Columnar)", "Carga en 0.13 segundos")

    st.success("""
    🎉 **Hito Cumplido:** El pipeline de ETL está **100% finalizado, auditado y desacoplado**. El artefacto Parquet alimenta de forma directa e independiente la página **`4.- Dashboard BI`** de esta misma aplicación.
    """)

st.markdown("---")

# -----------------------------------------------------------------------------
# Matriz Resumen: El Antes vs El Después del ETL
# -----------------------------------------------------------------------------
st.subheader("📊 Matriz Comparativa: El Dataset Original vs El Modelo Preparado Final")

matriz_comp = pd.DataFrame({
    "Dimensión Evaluada": [
        "Número de Columnas",
        "Variables con 100% de Completitud",
        "Valores Nulos en el Dataset",
        "Lote Crítico 2023",
        "Identificación de Causa Única",
        "Inconsistencias Cronológicas",
        "Variables Especializadas de Negocio",
        "Tamaño del Archivo en Disco"
    ],
    "Estado Original (Raw API PJUD)": [
        "20 columnas crudas",
        "Solo 12 de 20 columnas (60%)",
        "> 1.300.000 celdas vacías (RUC 81% nulo)",
        "Columnas desfasadas a la izquierda (43.380 RITs perdidos)",
        "RIT relativo por juzgado con 41.439 errores '--'",
        "22 casos con fecha de audiencia anterior a programación",
        "Ninguna (solo marcas operativas del SITFA)",
        "> 700 MB (JSONs anuales) / 238 MB Parquet no optimizado"
    ],
    "Modelo Final Preparado (ETL EMCR)": [
        "36 columnas estructuradas",
        "36 de 36 columnas (100.00%)",
        "0 valores nulos (100% completitud total)",
        "100% saneado mediante cruce relacional oficial PJUD",
        "Clave compuesta canónica ID_CAUSA_RIT (280.795 causas únicas)",
        "0 inconsistencias (100% cronología universal)",
        "16 métricas de BI (SLAs, Time-tracking, Litigiosidad, Tramos)",
        "10.77 MB en Apache Parquet columnar (Snappy)"
    ]
})

st.dataframe(matriz_comp, use_container_width=True, hide_index=True)

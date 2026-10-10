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
        page_title="4.- Dashboard BI - Inteligencia Judicial",
        page_icon="⚖️",
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
def cargar_datos_bi():
    if PARQUET_PATH.exists():
        return pd.read_parquet(PARQUET_PATH)
    return pd.DataFrame()

df_raw = cargar_datos_bi()

if df_raw.empty:
    st.error(f"⚠️ No se encontró el dataset preparado en: `{PARQUET_PATH}`. Por favor ejecuta el pipeline ETL previamente.")
    st.stop()

# -----------------------------------------------------------------------------
# Barra Lateral: Filtros Interactivos del Dashboard
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/Poder_Judicial_de_Chile_%28logo%29.svg/1200px-Poder_Judicial_de_Chile_%28logo%29.svg.png", width=130)
    st.title("Filtros Ejecutivos BI")
    st.caption("Jurisdicción: **Corte de Valparaíso** (Materia Familia)")
    st.markdown("---")

    # 1. Rango de Años
    anios_disponibles = sorted(df_raw['ANO_AUDIENCIA'].dropna().unique().tolist())
    anios_sel = st.multiselect(
        "📅 Años de Análisis:",
        options=anios_disponibles,
        default=anios_disponibles,
        help="Selecciona uno o más años del horizonte 2015-2025"
    )

    # 2. Macro Materia
    materias_disponibles = sorted(df_raw['MACRO_MATERIA'].dropna().unique().tolist())
    materias_sel = st.multiselect(
        "📂 Macro-Materia Jurídica:",
        options=materias_disponibles,
        default=materias_disponibles,
        help="Área de práctica legal en derecho de familia"
    )

    # 3. Tribunal
    tribunales_disponibles = sorted(df_raw['TRIBUNAL'].dropna().unique().tolist())
    sel_all_trib = st.checkbox("Seleccionar todos los tribunales", value=True)
    if sel_all_trib:
        tribunales_sel = tribunales_disponibles
    else:
        tribunales_sel = st.multiselect(
            "🏛️ Tribunales:",
            options=tribunales_disponibles,
            default=tribunales_disponibles[:3]
        )

    # 4. Modalidad
    modalidad_opt = st.radio(
        "💻 Modalidad de Comparecencia:",
        options=["Todas", "Presencial", "Telemática (Videoconferencia)"],
        index=0
    )

    st.markdown("---")
    st.info("💡 **Uso para Estudio Jurídico:** Los filtros recalculan instantáneamente los SLAs, tasas de litigiosidad y costos de sala.")

# -----------------------------------------------------------------------------
# Aplicación de Filtros
# -----------------------------------------------------------------------------
mask = pd.Series(True, index=df_raw.index)

if anios_sel:
    mask &= df_raw['ANO_AUDIENCIA'].isin(anios_sel)
if materias_sel:
    mask &= df_raw['MACRO_MATERIA'].isin(materias_sel)
if tribunales_sel:
    mask &= df_raw['TRIBUNAL'].isin(tribunales_sel)
if modalidad_opt == "Presencial":
    mask &= (df_raw['VIDEOCONFERENCIA'] == False)
elif modalidad_opt == "Telemática (Videoconferencia)":
    mask &= (df_raw['VIDEOCONFERENCIA'] == True)

df_filtrado = df_raw[mask].copy()

if df_filtrado.empty:
    st.warning("⚠️ No se encontraron registros para los filtros seleccionados. Ajusta los parámetros en la barra lateral.")
    st.stop()

# -----------------------------------------------------------------------------
# Encabezado Principal y KPIs de Alto Nivel
# -----------------------------------------------------------------------------
st.title("⚖️ Dashboard Ejecutivo de Inteligencia de Negocios (BI)")
st.markdown("### Plataforma de Inteligencia Judicial y Gestión Estratégica para Estudios de Abogados")
st.caption(f"Visualizando **{len(df_filtrado):,} audiencias** de un universo total de {len(df_raw):,} registros (2015–2025).")

# Fila de Métricas Clave
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
with kpi1:
    st.metric(
        "🏛️ Total Audiencias",
        f"{len(df_filtrado):,}",
        f"{len(df_filtrado)/len(df_raw)*100:.1f}% del total"
    )
with kpi2:
    n_causas = df_filtrado['ID_CAUSA_RIT'].nunique()
    st.metric(
        "📁 Causas Únicas",
        f"{n_causas:,}",
        f"{len(df_filtrado)/n_causas:.2f} aud/causa"
    )
with kpi3:
    med_plazo = df_filtrado['PLAZO_AGENDAMIENTO'].median()
    st.metric(
        "⏱️ SLA Mediana Agendamiento",
        f"{med_plazo:.0f} días hábiles",
        f"P90: {df_filtrado['PLAZO_AGENDAMIENTO'].quantile(0.9):.0f} días"
    )
with kpi4:
    med_dur = df_filtrado[df_filtrado['DURACION_MINUTOS'] > 0]['DURACION_MINUTOS'].median()
    st.metric(
        "🕒 Mediana Duración Sala",
        f"{med_dur:.0f} minutos",
        f"Horas: {df_filtrado['DURACION_MINUTOS'].sum()/60:,.0f} hrs"
    )
with kpi5:
    pct_tele = (df_filtrado['VIDEOCONFERENCIA'].mean() * 100)
    st.metric(
        "💻 Tasa Telemática",
        f"{pct_tele:.1f}%",
        f"{df_filtrado['VIDEOCONFERENCIA'].sum():,} telemáticas"
    )

st.markdown("---")

# -----------------------------------------------------------------------------
# Navegación por Pestañas Estratégicas
# -----------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "⏱️ 1. SLAs y Predictibilidad de Plazos",
    "⚖️ 2. Litigiosidad y Riesgo de Costos",
    "🕒 3. Capacidad de Sala y Time-Tracking",
    "💻 4. Virtualidad y Productividad",
    "📑 5. Explorador de Microdatos"
])

# =============================================================================
# TAB 1: SLAs y Predictibilidad de Plazos
# =============================================================================
with tab1:
    st.subheader("⏱️ Gestión de Plazos y Cuellos de Botella Procesales")
    st.markdown("""
    **Objetivo de Negocio:** Comprometer plazos realistas con clientes, fundamentar solicitudes de pronto despacho y predecir tiempos de espera según tribunal y materia.
    """)

    c_sla1, c_sla2 = st.columns([3, 2])
    with c_sla1:
        # Benchmark de Tribunales por Mediana de Plazo
        bench_trib = df_filtrado.groupby('TRIBUNAL')['PLAZO_AGENDAMIENTO'].agg(['median', 'count']).reset_index()
        bench_trib = bench_trib.sort_values('median', ascending=True)

        fig_bench = px.bar(
            bench_trib,
            x='median',
            y='TRIBUNAL',
            orientation='h',
            title='<b>Benchmark de Juzgados: Mediana de Plazo de Agendamiento (Días Hábiles)</b>',
            labels={'median': 'Días Hábiles Judiciales (Mediana)', 'TRIBUNAL': 'Juzgado'},
            color='median',
            color_continuous_scale='Tealgrn',
            text='median'
        )
        fig_bench.update_traces(texttemplate='%{text:.0f} d', textposition='outside')
        fig_bench.update_layout(height=480, margin=dict(l=10, r=20, t=40, b=20), coloraxis_showscale=False)
        st.plotly_chart(fig_bench, use_container_width=True)

    with c_sla2:
        # Distribución por Tramo de Agendamiento
        tramo_dist = df_filtrado['TRAMO_AGENDAMIENTO'].value_counts().reset_index()
        tramo_dist.columns = ['Tramo', 'Conteo']
        tramo_dist = tramo_dist.sort_values('Tramo')

        fig_tramos = px.pie(
            tramo_dist,
            names='Tramo',
            values='Conteo',
            title='<b>Distribución por Tramos de Nivel de Servicio (SLA)</b>',
            hole=0.45,
            color_discrete_sequence=px.colors.diverging.Spectral
        )
        fig_tramos.update_layout(height=480, margin=dict(l=10, r=10, t=40, b=20), legend=dict(orientation="h", yanchor="bottom", y=-0.2))
        st.plotly_chart(fig_tramos, use_container_width=True)

    # Evolución Anual de Plazos
    evo_plazo = df_filtrado.groupby(['ANO_AUDIENCIA', 'MACRO_MATERIA'])['PLAZO_AGENDAMIENTO'].median().reset_index()
    fig_evo = px.line(
        evo_plazo,
        x='ANO_AUDIENCIA',
        y='PLAZO_AGENDAMIENTO',
        color='MACRO_MATERIA',
        markers=True,
        title='<b>Evolución Histórica de la Mediana de Agendamiento por Materia (2015–2025)</b>',
        labels={'ANO_AUDIENCIA': 'Año de Audiencia', 'PLAZO_AGENDAMIENTO': 'Mediana Días Hábiles', 'MACRO_MATERIA': 'Área Legal'}
    )
    fig_evo.update_layout(height=380, margin=dict(l=10, r=20, t=40, b=20))
    st.plotly_chart(fig_evo, use_container_width=True)

    st.info("""
    📌 **Conclusión Estratégica para el Estudio:** 
    Los juzgados más saturados (como La Ligua, Quintero y Viña del Mar) presentan medianas de espera de **31 a 40 días hábiles** (~1,5 a 2 meses corridos), con percentiles P90 que superan los **70 días hábiles**. 
    En materias contenciosas complejas, el estudio debe estipular en la propuesta de servicios que la primera audiencia no se celebrará antes de 60 días desde la notificación.
    """)

# =============================================================================
# TAB 2: Litigiosidad y Riesgo de Costos (Pricing)
# =============================================================================
with tab2:
    st.subheader("⚖️ Litigiosidad, Fricción Procesal y Estrategia de Pricing")
    st.markdown("""
    **Objetivo de Negocio:** Evaluar el riesgo de escalamiento de audiencias por causa para rediseñar la estructura de honorarios (tarifa base vs recargo por continuaciones).
    """)

    cl1, cl2 = st.columns([1, 1])
    with cl1:
        # Distribución de Audiencias por Causa
        aud_x_causa = df_filtrado.groupby('ID_CAUSA_RIT')['TOTAL_AUDIENCIAS_CAUSA'].first().value_counts().reset_index()
        aud_x_causa.columns = ['Audiencias_Totales', 'Causas']
        aud_x_causa['Categoria'] = aud_x_causa['Audiencias_Totales'].apply(lambda x: f"{x} Audiencia" if x == 1 else (f"{x} Audiencias" if x <= 4 else "5+ Audiencias"))
        cat_dist = aud_x_causa.groupby('Categoria')['Causas'].sum().reset_index()

        fig_aud_causa = px.bar(
            cat_dist,
            x='Categoria',
            y='Causas',
            title='<b>Volumen de Causas según Número Total de Audiencias Requeridas</b>',
            labels={'Categoria': 'Ciclo de Vida de la Causa', 'Causas': 'Causas Únicas'},
            text='Causas',
            color='Causas',
            color_continuous_scale='Blues'
        )
        fig_aud_causa.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig_aud_causa.update_layout(height=400, coloraxis_showscale=False)
        st.plotly_chart(fig_aud_causa, use_container_width=True)

    with cl2:
        # Tasa de Continuación de Juicio por Macro-Materia
        df_juicios = df_filtrado[df_filtrado['TIPO_AUDIENCIA'].str.contains('JUICIO', na=False)]
        tasa_cont = df_juicios.groupby('MACRO_MATERIA')['ES_CONTINUACION'].mean() * 100
        df_tasa_cont = tasa_cont.reset_index(name='Tasa_Continuacion')

        fig_cont = px.bar(
            df_tasa_cont,
            x='MACRO_MATERIA',
            y='Tasa_Continuacion',
            title='<b>Riesgo de Prolongación: Tasa de Juicios con Continuación (%)</b>',
            labels={'MACRO_MATERIA': 'Materia', 'Tasa_Continuacion': '% Audiencias de Continuación'},
            text='Tasa_Continuacion',
            color='Tasa_Continuacion',
            color_continuous_scale='Oranges'
        )
        fig_cont.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig_cont.update_layout(height=400, coloraxis_showscale=False)
        st.plotly_chart(fig_cont, use_container_width=True)

    # Tabla de Recomendación de Tarifas
    st.markdown("#### 💡 Recomendación de Modelo de Cobro para la Firma:")
    c_p1, c_p2, c_p3 = st.columns(3)
    with c_p1:
        st.success("""
        **Nivel 1: Causas Rápidas (60% de la cartera)**
        - Se resuelven en **1 sola audiencia** (Preparatoria o Avenimiento).
        - **Modalidad aconsejada:** Tarifa plana fija (*Flat Fee*).
        """)
    with c_p2:
        st.warning("""
        **Nivel 2: Litigación Estándar (25% de la cartera)**
        - Requieren **2 audiencias** (Preparatoria $+$ Juicio).
        - **Modalidad aconsejada:** Tarifa plana $+$ bono de comparecencia a juicio.
        """)
    with c_p3:
        st.error(r"""
        **Nivel 3: Alto Conflicto (15% de la cartera)**
        - Requieren **$\ge$ 3 audiencias** (Juicio extendido $+$ Continuaciones).
        - **Modalidad aconsejada:** Arancel horario o recargo por cada sesión adicional.
        """)

# =============================================================================
# TAB 3: Capacidad de Sala y Time-Tracking (Litigación)
# =============================================================================
with tab3:
    st.subheader("🕒 Capacidad de Sala, Time-Tracking y Asignación de Abogados")
    st.markdown("""
    **Objetivo de Negocio:** Planificar los turnos del equipo litigante, evitar colisiones en sala y presupuestar las horas efectivas de comparecencia.
    """)

    # Heatmap Día de la Semana vs Bloque Horario
    dias_orden = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
    bloques_orden = [
        'Mañana Temprano (08:00-09:59)',
        'Mañana Central (10:00-11:59)',
        'Mediodía (12:00-13:59)',
        'Tarde (14:00-16:59)',
        'Vespertino / Turno (>= 17:00)'
    ]
    
    matriz_sala = pd.crosstab(
        df_filtrado['DIA_SEMANA_AUDIENCIA'],
        df_filtrado['BLOQUE_HORARIO']
    ).reindex(index=dias_orden, columns=bloques_orden, fill_value=0)

    fig_heat = px.imshow(
        matriz_sala,
        labels=dict(x="Bloque Horario de Inicio", y="Día de la Semana", color="Nº Audiencias"),
        x=bloques_orden,
        y=dias_orden,
        title="<b>Matriz de Saturación de Salas: Concentración Semanal y Horaria</b>",
        color_continuous_scale="Viridis",
        aspect="auto",
        text_auto=True
    )
    fig_heat.update_layout(height=420)
    st.plotly_chart(fig_heat, use_container_width=True)

    c_tm1, c_tm2 = st.columns(2)
    with c_tm1:
        # Duración Mediana por Tipo de Audiencia
        dur_tipo = df_filtrado[df_filtrado['DURACION_MINUTOS'] > 0].groupby('TIPO_AUDIENCIA')['DURACION_MINUTOS'].agg(['median', 'count']).reset_index()
        dur_tipo = dur_tipo.sort_values('median', ascending=True)

        fig_dur = px.bar(
            dur_tipo,
            x='median',
            y='TIPO_AUDIENCIA',
            orientation='h',
            title='<b>Duración Mediana en Sala por Tipo de Audiencia (Minutos)</b>',
            labels={'median': 'Minutos en Sala (Mediana)', 'TIPO_AUDIENCIA': 'Tipo Audiencia'},
            text='median',
            color='median',
            color_continuous_scale='Purples'
        )
        fig_dur.update_traces(texttemplate='%{text:.0f} min', textposition='outside')
        fig_dur.update_layout(height=420, coloraxis_showscale=False)
        st.plotly_chart(fig_dur, use_container_width=True)

    with c_tm2:
        # Audiencias Frustradas y Duración Breve
        tramos_dur = df_filtrado['TRAMO_DURACION'].value_counts().reset_index()
        tramos_dur.columns = ['Tramo', 'Conteo']
        tramos_dur = tramos_dur.sort_values('Tramo')

        fig_pie_dur = px.pie(
            tramos_dur,
            names='Tramo',
            values='Conteo',
            title='<b>Distribución de Audiencias según Tramo de Duración Real</b>',
            hole=0.45,
            color_discrete_sequence=px.colors.sequential.Teal
        )
        fig_pie_dur.update_layout(height=420, legend=dict(orientation="h", yanchor="bottom", y=-0.25))
        st.plotly_chart(fig_pie_dur, use_container_width=True)

    st.warning("""
    ⚠️ **Protocolo Anti-Colisiones de Sala:**
    El bloque de las **10:00 a las 11:59 hrs** concentra el **40,3%** de todas las audiencias de la región. Si el estudio patrocina múltiples causas en la misma mañana, se requiere asignar procuradores de enlace o litigantes de respaldo para evitar frustraciones por falta de comparecencia simultánea.
    """)

# =============================================================================
# TAB 4: Virtualidad y Productividad
# =============================================================================
with tab4:
    st.subheader("💻 Transformación Digital, Comparecencia Remota y Ahorro Operativo")
    st.markdown("""
    **Objetivo de Negocio:** Medir la productividad del litigante bajo régimen telemático, evaluar el ahorro en viáticos de traslado y mapear juzgados reticentes a la virtualidad.
    """)

    c_v1, c_v2 = st.columns(2)
    with c_v1:
        # Evolución de la Tasa Telemática por Año
        evo_tele = df_filtrado.groupby('ANO_AUDIENCIA')['VIDEOCONFERENCIA'].mean().reset_index()
        evo_tele['Porcentaje'] = evo_tele['VIDEOCONFERENCIA'] * 100

        fig_tele_evo = px.bar(
            evo_tele,
            x='ANO_AUDIENCIA',
            y='Porcentaje',
            title='<b>Evolución de la Adopción Telemática (% Audiencias por Zoom)</b>',
            labels={'ANO_AUDIENCIA': 'Año', 'Porcentaje': '% Telemática'},
            text='Porcentaje',
            color='Porcentaje',
            color_continuous_scale='Greens'
        )
        fig_tele_evo.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig_tele_evo.update_layout(height=420, coloraxis_showscale=False)
        st.plotly_chart(fig_tele_evo, use_container_width=True)

    with c_v2:
        # Ranking de Tribunales según Tasa de Telemática
        trib_tele = df_filtrado[df_filtrado['ANO_AUDIENCIA'] >= 2021].groupby('TRIBUNAL')['VIDEOCONFERENCIA'].mean().reset_index()
        trib_tele['Porcentaje'] = (trib_tele['VIDEOCONFERENCIA'] * 100).round(1)
        trib_tele = trib_tele.sort_values('Porcentaje', ascending=True)

        fig_trib_tele = px.bar(
            trib_tele,
            x='Porcentaje',
            y='TRIBUNAL',
            orientation='h',
            title='<b>Tasa de Videoconferencia por Tribunal (Período 2021–2025)</b>',
            labels={'Porcentaje': '% Telemática', 'TRIBUNAL': 'Juzgado'},
            text='Porcentaje',
            color='Porcentaje',
            color_continuous_scale='Mint'
        )
        fig_trib_tele.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig_trib_tele.update_layout(height=420, coloraxis_showscale=False)
        st.plotly_chart(fig_trib_tele, use_container_width=True)

    st.success("""
    🌟 **Ahorro de Costos y Expansión Geográfica:**
    Bajo la Ley N° 21.394 (régimen híbrido permanente), un abogado del estudio puede asumir audiencias sucesivas en Casablanca, San Antonio y Los Andes en una sola jornada sin incurrir en 4 horas de traslado en carretera ni gastos de viáticos.
    """)

# =============================================================================
# TAB 5: Explorador de Microdatos y Exportación
# =============================================================================
with tab5:
    st.subheader("📑 Explorador de Microdatos Filtrados")
    st.markdown("Consulta y descarga de la muestra analítica filtrada según los parámetros de la barra lateral:")

    cols_export = [
        'ID_CAUSA_RIT', 'TRIBUNAL', 'MACRO_MATERIA', 'TIPO_AUDIENCIA',
        'FECHA_AUDIENCIA', 'DIA_SEMANA_AUDIENCIA', 'BLOQUE_HORARIO',
        'DURACION_MINUTOS', 'PLAZO_AGENDAMIENTO', 'TRAMO_AGENDAMIENTO',
        'ORDEN_AUDIENCIA_CAUSA', 'VIDEOCONFERENCIA', 'EPOCA_NORMATIVA'
    ]
    st.dataframe(df_filtrado[cols_export].head(100), use_container_width=True)

    csv_data = df_filtrado[cols_export].head(1000).to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 Descargar Primeras 1.000 Filas Filtradas (CSV)",
        data=csv_data,
        file_name="audiencias_filtradas_estudio_abogados.csv",
        mime="text/csv"
    )

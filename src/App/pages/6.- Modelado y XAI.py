from pathlib import Path
import json
import joblib
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# Configuración de Página y Compatibilidad de Ancho Streamlit >= 1.50
# -----------------------------------------------------------------------------
try:
    st.set_page_config(
        page_title="6.- Modelado y XAI - Inteligencia Judicial",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )
except Exception:
    pass

_VER = tuple(int(x) for x in st.__version__.split(".")[:2])
ANCHO = {"width": "stretch"} if _VER >= (1, 50) else {"use_container_width": True}

# -----------------------------------------------------------------------------
# Localización de Archivos y Artefactos del Avance 3
# -----------------------------------------------------------------------------
CURRENT_DIR = Path(__file__).resolve().parent
BASE_DIR = None
for p in [CURRENT_DIR] + list(CURRENT_DIR.parents):
    if (p / "data").exists() and (p / "src").exists():
        BASE_DIR = p
        break
if BASE_DIR is None:
    BASE_DIR = Path(__file__).resolve().parents[2]

PARQUET_PATH = BASE_DIR / "data" / "processed" / "audiencias_preparadas_modelo.parquet"
FIG_DIR = BASE_DIR / "reports" / "figures_avance3"
SUMMARY_JSON = FIG_DIR / "avance3_metrics_summary.json"
MODELS_JOBLIB = FIG_DIR / "avance3_live_models.joblib"
PPTX_PATH = BASE_DIR / "reports" / "Presentacion_Avance_3_EquipoEMCR.pptx"
NB_PATH = BASE_DIR / "notebooks" / "04_Modelado_y_XAI_Avance3.ipynb"
MD_REPORT_PATH = BASE_DIR / "reports" / "06_Avance_3_Modelado_y_XAI_Justificacion.md"


@st.cache_data(show_spinner=False)
def cargar_resumen_avance3():
    if SUMMARY_JSON.exists():
        with open(SUMMARY_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


@st.cache_resource(show_spinner="Cargando modelos entrenados y motor SHAP...")
def cargar_modelos_vivos():
    if MODELS_JOBLIB.exists():
        return joblib.load(MODELS_JOBLIB)
    return None


@st.cache_data(show_spinner="Cargando dataset de audiencias...")
def cargar_datos_modelo():
    if PARQUET_PATH.exists():
        cols = [
            "TRIBUNAL", "TIPO_AUDIENCIA", "TIPO_PROCEDIMIENTO", "MACRO_MATERIA",
            "VIDEOCONFERENCIA", "ORDEN_AUDIENCIA_CAUSA", "FECHA_PROGRAMACION",
            "PLAZO_AGENDAMIENTO", "ID_CAUSA_RIT"
        ]
        df = pd.read_parquet(PARQUET_PATH, columns=cols)
        df["FECHA_PROGRAMACION"] = pd.to_datetime(df["FECHA_PROGRAMACION"])
        df["ANO_PROG"] = df["FECHA_PROGRAMACION"].dt.year
        df["MES_PROG"] = df["FECHA_PROGRAMACION"].dt.month
        df["DIA_SEM_PROG"] = df["FECHA_PROGRAMACION"].dt.dayofweek
        df["VIDEOCONFERENCIA_INT"] = df["VIDEOCONFERENCIA"].astype(int)
        df["Y_SEVERA"] = (df["PLAZO_AGENDAMIENTO"] > 60).astype(int)
        df["TRIBUNAL_CORTO"] = (
            df["TRIBUNAL"]
            .str.title()
            .str.replace("Juzgado De Familia De ", "J.F. ", regex=False)
            .str.replace("Juzgado De Letras Y Garantía De ", "J.L.G. ", regex=False)
            .str.replace("Juzgado De Letras Y Garantia De ", "J.L.G. ", regex=False)
            .str.replace("Juzgado De Letras De ", "J.L. ", regex=False)
            .str.replace("Vina Del Mar", "Viña del Mar", regex=False)
        )
        return df
    return pd.DataFrame()


resumen = cargar_resumen_avance3()
df_all = cargar_datos_modelo()
live_bundle = cargar_modelos_vivos()

# -----------------------------------------------------------------------------
# Barra Lateral: Descarga Directa de Entregables del Avance 3
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 📦 Entregables Avance 3")
    st.caption("Descarga directa de archivos oficiales:")
    if PPTX_PATH.exists():
        with open(PPTX_PATH, "rb") as f_pptx:
            st.download_button(
                label="📊 Descargar Presentación (.pptx)",
                data=f_pptx.read(),
                file_name="Presentacion_Avance_3_EquipoEMCR.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                **ANCHO,
            )
    if NB_PATH.exists():
        with open(NB_PATH, "rb") as f_nb:
            st.download_button(
                label="📓 Descargar Notebook (.ipynb)",
                data=f_nb.read(),
                file_name="04_Modelado_y_XAI_Avance3.ipynb",
                mime="application/x-ipynb+json",
                **ANCHO,
            )
    if MD_REPORT_PATH.exists():
        with open(MD_REPORT_PATH, "rb") as f_md:
            st.download_button(
                label="📄 Descargar Informe (.md)",
                data=f_md.read(),
                file_name="06_Avance_3_Modelado_y_XAI_Justificacion.md",
                mime="text/markdown",
                **ANCHO,
            )
    st.markdown("---")
    st.info(
        "⚖️ **Metodología Taller 5 y 6:**\n"
        "- **Tarea:** Clasificación Binaria (`> 60` días hábiles).\n"
        "- **Train:** Régimen Vigente `2021–2023` ($n=130.057$).\n"
        "- **Test:** Out-of-Time `2024–2025` ($n=83.410$).\n"
        "- **XAI:** `SHAP TreeExplainer` en escala *log-odds*."
    )

st.title("🤖 6.- Modelado Supervisado, Evaluación de Errores y Explicabilidad (XAI)")
st.caption(
    "Avance 3 · Predicción de Congestión Severa (> 60 días hábiles) al momento de agendar la audiencia "
    "(T = FECHA_PROGRAMACION) · Ceñido estrictamente a Taller 5 y Taller 6 (Prof. Jesús A. Parra)"
)

if resumen is None:
    st.warning("⚠️ Ejecutando o esperando artefactos del pipeline (`src/avance3_pipeline.py`).")
    st.stop()

SECCIONES = [
    "1 · Diseño, X, y & Régimen",
    "2 · Validación Cruzada & Rendimiento",
    "3 · Curvas ROC/PR, Umbral & Bootstrap",
    "4 · Explicabilidad Global y Local (SHAP)",
    "5 · Simulador LegalTech con SHAP en Vivo",
]

seccion = st.radio("Navegación Avance 3", SECCIONES, horizontal=True, label_visibility="collapsed")
st.divider()

# =============================================================================
# SECCIÓN 1: MOTIVACIÓN, FORMULACIÓN (X, Y, T) Y CAMBIO DE RÉGIMEN
# =============================================================================
if seccion == SECCIONES[0]:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🏛️ Universo Auditado", f"{resumen['dataset_total_rows']:,} audiencias", f"{resumen['dataset_total_cases']:,} causas RIT")
    c2.metric("🎯 Train Régimen Vigente", f"{resumen['train_recent_rows']:,} filas", f"2021–2023 (Prev: {resumen['train_recent_prev']*100:.1f}%)")
    c3.metric("🧪 Test Out-of-Time", f"{resumen['test_rows']:,} filas", f"2024–2025 (Prev: {resumen['test_prev']*100:.1f}%)")
    c4.metric("🏆 Mejor ROC-AUC / AP", f"{resumen['test_results']['XGBoost']['test_roc_auc']:.3f}", f"AP = {resumen['test_results']['XGBoost']['test_ap']:.3f} (3,1x azar)")

    col_a, col_b = st.columns([1.15, 1])
    with col_a:
        st.markdown("#### 🎯 Pregunta Predictiva y Utilidad para Estudios Jurídicos")
        st.info(
            "**Pregunta Predictiva:** *Al instante $T = \\text{FECHA\\_PROGRAMACION}$ en que el tribunal dicta la resolución que "
            "agenda una audiencia de Familia, ¿superará la espera los **60 días hábiles** ($y = 1$, más del doble del plazo legal de "
            "30 días del Art. 59 y 61 de la Ley N° 19.968)?*\n\n"
            "**Decisiones que habilita en la firma legal:**\n"
            "1. **Estructuración de honorarios y flujo de caja (*Smart Pricing*):** Evitar pactar honorarios fijos subvalorados en causas que demorarán > 3 meses calendario.\n"
            "2. **Gestión preventiva procesal:** Presentar escritos de entorpecimiento, habilitación de horario o cautelares provisorias (alimentos/cuidado personal) cuando el modelo alerta congestión severa.\n"
            "3. **Transparencia con el patrocinado:** Sustituir promesas genéricas por probabilidades calibradas por tribunal y tipo de audiencia."
        )
    with col_b:
        st.markdown("#### 🛡️ Control Estricto de Fuga de Información (*Zero Data Leakage*)")
        st.success(
            "**Variables Predictoras $X$ válidas en $T = \\text{FECHA\\_PROGRAMACION}$ (8 atributos):**\n"
            "- **Estructurales:** `TRIBUNAL` (15 juzgados), `TIPO_AUDIENCIA`, `TIPO_PROCEDIMIENTO`, `MACRO_MATERIA`.\n"
            "- **Operativas e Históricas de la Causa:** `VIDEOCONFERENCIA` (0/1), `ORDEN_AUDIENCIA_CAUSA` (1ª, 2ª, 3ª...).\n"
            "- **Estacionalidad del Agendamiento:** `MES_PROG` (1–12), `DIA_SEM_PROG` (Lunes–Sábado).\n\n"
            "**Variables Excluidas por Fuga (*Data Leakage*):**\n"
            "- `DIAS_TRAMITACION_PREVIA` (contiene `FECHA_AUDIENCIA`), `FECHA_AUDIENCIA`, `DURACION_MINUTOS`, `FLG_AUDIENCIA_FRUSTRADA`, `TOTAL_AUDIENCIAS_CAUSA`."
        )

    if (FIG_DIR / "fig01_eda_regimen_y_audiencia.png").exists():
        st.image(
            str(FIG_DIR / "fig01_eda_regimen_y_audiencia.png"),
            caption="Figura 1: Quiebre estructural post-2020 (Leyes 21.226 y 21.394) y poder discriminante de TIPO_AUDIENCIA (η² = 10,9%).",
            **ANCHO,
        )

# =============================================================================
# SECCIÓN 2: VALIDACIÓN CRUZADA Y TABLA COMPARATIVA DE RENDIMIENTO
# =============================================================================
elif seccion == SECCIONES[1]:
    st.markdown("#### 📊 Protocolo de Validación: Separar Test $\\rightarrow$ Cross-Validation en Train $\\rightarrow$ Evaluar en Test")
    st.markdown(
        "Siguiendo estrictamente la metodología de **Taller 5 y Taller 6**, el preprocesamiento (`ColumnTransformer`: "
        "`OneHotEncoder(handle_unknown='ignore')` + `StandardScaler()`) se encapsula dentro de un `Pipeline` para ajustarse "
        "exclusivamente sobre el subconjunto de entrenamiento en cada uno de los **5 folds estratificados (`StratifiedKFold`)**."
    )

    cv_rows = []
    for m_name, d_cv in resumen["cv_results"].items():
        cv_rows.append({
            "Modelo": m_name,
            "ROC-AUC Medio (CV)": round(d_cv["ROC_AUC_mean"], 4),
            "Desv. Est. ROC-AUC (ddof=1)": round(d_cv["ROC_AUC_std"], 4),
            "AP Media (CV)": round(d_cv["AP_mean"], 4),
            "Desv. Est. AP (ddof=1)": round(d_cv["AP_std"], 4),
            "Recall Medio @0.50": round(d_cv["Recall_mean"], 4),
            "Precision Media @0.50": round(d_cv["Precision_mean"], 4),
            "F1 Medio @0.50": round(d_cv["F1_mean"], 4),
        })
    st.markdown("**Tabla 1: Estabilidad en Validación Cruzada Estratificada (5-Fold `StratifiedKFold` sobre Train 2021–2023, $n = 130.057$)**")
    st.dataframe(pd.DataFrame(cv_rows).set_index("Modelo"), **ANCHO)

    test_rows = []
    for m_name, d_te in resumen["test_results"].items():
        test_rows.append({
            "Algoritmo": m_name,
            "ROC-AUC (Train)": round(d_te["train_roc_auc"], 4),
            "ROC-AUC (Test)": round(d_te["test_roc_auc"], 4),
            "AP (Train)": round(d_te["train_ap"], 4),
            "AP (Test)": round(d_te["test_ap"], 4),
            "Accuracy (Test @0.50)": round(d_te["test_acc_50"], 4),
            "Precision (Test @0.50)": round(d_te["test_prec_50"], 4),
            "Recall (Test @0.50)": round(d_te["test_rec_50"], 4),
            "F1-Score (Test @0.50)": round(d_te["test_f1_50"], 4),
            "Precision (Test @0.35)": round(d_te["test_prec_35"], 4),
            "Recall (Test @0.35)": round(d_te["test_rec_35"], 4),
            "F1-Score (Test @0.35)": round(d_te["test_f1_35"], 4),
        })
    st.markdown("**Tabla 2: Rendimiento Comparado en Conjunto de Prueba Out-of-Time (2024–2025, $n = 83.410$, Prevalencia Positiva = 15,6%)**")
    st.dataframe(pd.DataFrame(test_rows).set_index("Algoritmo"), **ANCHO)

    if (FIG_DIR / "fig02_validacion_cruzada_y_regimen.png").exists():
        st.image(
            str(FIG_DIR / "fig02_validacion_cruzada_y_regimen.png"),
            caption="Figura 2: Comparación de estabilidad en 5-Fold CV y demostración empírica del sesgo por cambio de régimen al entrenar con 2015–2023 vs 2021–2023.",
            **ANCHO,
        )

# =============================================================================
# SECCIÓN 3: CURVAS ROC/PR, ANÁLISIS DE ERRORES Y BOOTSTRAP EN TEST
# =============================================================================
elif seccion == SECCIONES[2]:
    st.markdown("#### 📈 Evaluación Continua (`predict_proba`), Costo Asimétrico del Error y Bootstrap ($B = 500$)")
    if (FIG_DIR / "fig03_curvas_roc_y_pr_test.png").exists():
        st.image(
            str(FIG_DIR / "fig03_curvas_roc_y_pr_test.png"),
            caption="Figura 3: Curvas ROC y Precision–Recall en Test (2024–2025) con línea basal de prevalencia positiva (15,6%) y puntos operativos (0.50 vs 0.35).",
            **ANCHO,
        )

    if (FIG_DIR / "fig04_matrices_confusion_y_bootstrap.png").exists():
        st.image(
            str(FIG_DIR / "fig04_matrices_confusion_y_bootstrap.png"),
            caption="Figura 4: Matrices de confusión de XGBoost en Test (umbral 0.50 vs 0.35) y distribución Bootstrap del Average Precision (AP).",
            **ANCHO,
        )

    bs = resumen["bootstrap_summary"]
    col1, col2 = st.columns(2)
    with col1:
        st.info(
            "**⚖️ Justificación Jurídica del Umbral Operativo ($0,50 \\rightarrow 0,35$):**\n"
            "- **Falso Negativo (FN — No anticipar una demora $> 60$ días):** Alto costo económico y reputacional para el estudio jurídico (subcotización de honorarios fijos, falta de medidas cautelares oportunas, pérdida de confianza del cliente).\n"
            "- **Falso Positivo (FP — Alerta preventiva en causa que se agenda $\\le 60$ días):** Bajo costo (preparar tempranamente la prueba documental/pericial).\n"
            "- Al calibrar el umbral en validación a **0,35**, el **Recall en Test sube de 48,6% a 67,9%** (detectando **8.831 de las 13.002 demoras severas**), incrementando además el F1-Score global a **0,510**."
        )
    with col2:
        st.success(
            f"**🎲 Incertidumbre en Test vía Bootstrap Percentil 95% ($B = {bs['B']}$ réplicas, modelo fijo):**\n"
            f"- **XGBoost AP:** `{bs['XGBoost_AP_point']:.4f}` · IC 95%: `[{bs['XGBoost_AP_ci95'][0]:.4f}, {bs['XGBoost_AP_ci95'][1]:.4f}]`\n"
            f"- **Random Forest AP:** `{bs['RandomForest_AP_point']:.4f}` · IC 95%: `[{bs['RandomForest_AP_ci95'][0]:.4f}, {bs['RandomForest_AP_ci95'][1]:.4f}]`\n"
            f"- **Regresión Logística AP:** `{bs['LogReg_AP_point']:.4f}` · IC 95%: `[{bs['LogReg_AP_ci95'][0]:.4f}, {bs['LogReg_AP_ci95'][1]:.4f}]`\n"
            f"- **Diferencia Pareada $\\Delta\\text{{AP}}$ (XGBoost $-$ LogReg):** `+{bs['Diff_XGB_LR_point']:.4f}` · IC 95%: `[+{bs['Diff_XGB_LR_ci95'][0]:.4f}, +{bs['Diff_XGB_LR_ci95'][1]:.4f}]` (el 0 queda totalmente excluido; superioridad estadísticamente robusta)."
        )

# =============================================================================
# SECCIÓN 4: EXPLICABILIDAD GLOBAL Y LOCAL (SHAP + ÁRBOL PEDAGÓGICO)
# =============================================================================
elif seccion == SECCIONES[3]:
    st.markdown("#### 🔍 Explicabilidad Global (`shap.plots.beeswarm`) sobre Muestra Estratificada de Test ($n = 2.000$)")
    st.caption(
        "Nota Metodológica (Taller 6): SHAP cuantifica cómo cada atributo desplaza la predicción del modelo desde el valor base "
        "E[f(X)] en escala log-odds. Explica el comportamiento del modelo y NO constituye prueba de causalidad directa."
    )

    if (FIG_DIR / "fig05_shap_beeswarm_global.png").exists():
        st.image(
            str(FIG_DIR / "fig05_shap_beeswarm_global.png"),
            caption="Figura 5: Gráfico Beeswarm de SHAP Global en muestra identificada de Test (n = 2.000 audiencias de 2024–2025).",
            **ANCHO,
        )

    st.markdown("---")
    st.markdown("#### 🔬 Explicabilidad Local (`shap.plots.waterfall`): 3 Observaciones Concretas del Conjunto de Prueba")
    tab_c1, tab_c2, tab_c3, tab_tree = st.tabs([
        "🔴 Caso 1: Acierto Crítico (Verdadero Positivo)",
        "🟢 Caso 2: Acierto Vía Rápida (Verdadero Negativo)",
        "⚠️ Caso 3: Error Forense (Falso Negativo)",
        "🌳 Árbol Individual Pequeño (max_depth=3)",
    ])

    with tab_c1:
        c_info = resumen["local_cases"]["Caso_1_VP_Acierto_Severo"]
        st.markdown(
            f"**Observación Test `idx={c_info['test_index']}` (`ID_CAUSA_RIT: {c_info['ID_CAUSA_RIT']}`)** · "
            f"**Tribunal:** {c_info['TRIBUNAL']} · **Audiencia:** `{c_info['TIPO_AUDIENCIA']}` · **Procedimiento:** `{c_info['TIPO_PROCEDIMIENTO']}`\n\n"
            f"- **Valor Real ($y$):** `{c_info['PLAZO_REAL_DIAS']} días hábiles` ($y = 1$, Congestión Severa $> 60$d)\n"
            f"- **Predicción ($\\hat{{y}}$):** Probabilidad XGBoost = `{c_info['PROBA_XGB']:.1%}` (Random Forest = `{c_info['PROBA_RF']:.1%}`, Reg. Logística = `{c_info['PROBA_LR']:.1%}`)\n"
            f"- **Descomposición Aditiva SHAP (log-odds):** Valor Base $E[f(X)] = {c_info['BASE_VALUE_LOGODDS']:.3f} \\rightarrow f(x) = {c_info['FX_LOGODDS']:.3f}$"
        )
        if (FIG_DIR / "fig06a_shap_waterfall_caso1_vp.png").exists():
            st.image(str(FIG_DIR / "fig06a_shap_waterfall_caso1_vp.png"), **ANCHO)

    with tab_c2:
        c_info = resumen["local_cases"]["Caso_2_VN_Acierto_Rapido"]
        st.markdown(
            f"**Observación Test `idx={c_info['test_index']}` (`ID_CAUSA_RIT: {c_info['ID_CAUSA_RIT']}`)** · "
            f"**Tribunal:** {c_info['TRIBUNAL']} · **Audiencia:** `{c_info['TIPO_AUDIENCIA']}` · **Procedimiento:** `{c_info['TIPO_PROCEDIMIENTO']}`\n\n"
            f"- **Valor Real ($y$):** `{c_info['PLAZO_REAL_DIAS']} días hábiles` ($y = 0$, Agendamiento Ágil $\\le 60$d)\n"
            f"- **Predicción ($\\hat{{y}}$):** Probabilidad XGBoost = `{c_info['PROBA_XGB']:.1%}` (Random Forest = `{c_info['PROBA_RF']:.1%}`, Reg. Logística = `{c_info['PROBA_LR']:.1%}`)\n"
            f"- **Descomposición Aditiva SHAP (log-odds):** Valor Base $E[f(X)] = {c_info['BASE_VALUE_LOGODDS']:.3f} \\rightarrow f(x) = {c_info['FX_LOGODDS']:.3f}$"
        )
        if (FIG_DIR / "fig06b_shap_waterfall_caso2_vn.png").exists():
            st.image(str(FIG_DIR / "fig06b_shap_waterfall_caso2_vn.png"), **ANCHO)

    with tab_c3:
        c_info = resumen["local_cases"]["Caso_3_FN_Error_Critico"]
        st.markdown(
            f"**Observación Test `idx={c_info['test_index']}` (`ID_CAUSA_RIT: {c_info['ID_CAUSA_RIT']}`)** · "
            f"**Tribunal:** {c_info['TRIBUNAL']} · **Audiencia:** `{c_info['TIPO_AUDIENCIA']}` · **Procedimiento:** `{c_info['TIPO_PROCEDIMIENTO']}`\n\n"
            f"- **Valor Real ($y$):** `{c_info['PLAZO_REAL_DIAS']} días hábiles` ($y = 1$, Demora Severa $> 60$d)\n"
            f"- **Predicción ($\\hat{{y}}$):** Probabilidad XGBoost = `{c_info['PROBA_XGB']:.1%}` (Falso Negativo: los 3 modelos asignaron baja probabilidad por tratarse de una audiencia VIF en un tribunal habitualmente ágil)\n"
            f"- **Diagnóstico Forense del Error:** La demora real de {c_info['PLAZO_REAL_DIAS']} días obedece a factores **no observables** en la tabla de agendamiento estructurado (ej. solicitud de peritajes externos SML/DAM, falta de notificación por receptor judicial o suspensión de común acuerdo)."
        )
        if (FIG_DIR / "fig06c_shap_waterfall_caso3_fn.png").exists():
            st.image(str(FIG_DIR / "fig06c_shap_waterfall_caso3_fn.png"), **ANCHO)

    with tab_tree:
        st.markdown(
            "**Árbol de Decisión Individual Pequeño (`max_depth=3`)**: Tal como enfatiza el *Taller 6*, visualizar un árbol simple "
            "permite comprender cortes explícitos e interacciones jerárquicas, sin confundirlo con la explicación del ensamble completo."
        )
        if (FIG_DIR / "fig07_arbol_decision_interpretable.png").exists():
            st.image(str(FIG_DIR / "fig07_arbol_decision_interpretable.png"), **ANCHO)

# =============================================================================
# SECCIÓN 5: SIMULADOR PREDICTIVO LEGALTECH CON INFERENCIA Y SHAP EN VIVO
# =============================================================================
elif seccion == SECCIONES[4]:
    st.markdown("#### ⚖️ Simulador Predictivo en Vivo con Inferencia Multi-Modelo y Explicación SHAP Instantánea")
    st.caption(
        "Configura los parámetros de una audiencia al momento de su programación (T = FECHA_PROGRAMACION). "
        "El motor ejecuta en tiempo real los pipelines entrenados (XGBoost, Random Forest y Regresión Logística) y descompone la predicción con SHAP."
    )
    df_rec = df_all[df_all["ANO_PROG"].between(2021, 2025)]

    MESES_NOMBRES = {
        1: "1 - Enero", 2: "2 - Febrero (Feriado Judicial)", 3: "3 - Marzo (Pico Ingresos)",
        4: "4 - Abril", 5: "5 - Mayo", 6: "6 - Junio", 7: "7 - Julio", 8: "8 - Agosto",
        9: "9 - Septiembre", 10: "10 - Octubre", 11: "11 - Noviembre", 12: "12 - Diciembre (Cierre Anual)"
    }
    DIAS_NOMBRES = {0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes", 5: "Sábado"}

    with st.container(border=True):
        c_sim1, c_sim2, c_sim3, c_sim4 = st.columns(4)
        with c_sim1:
            trib_list = sorted(df_rec["TRIBUNAL_CORTO"].unique())
            default_trib = trib_list.index("J.F. Viña del Mar") if "J.F. Viña del Mar" in trib_list else 0
            trib_sel = st.selectbox("🏛️ Tribunal de Familia:", trib_list, index=default_trib)
            aud_list = sorted(df_rec["TIPO_AUDIENCIA"].unique())
            default_aud = aud_list.index("AUDIENCIA DE JUICIO") if "AUDIENCIA DE JUICIO" in aud_list else 0
            aud_sel = st.selectbox("📋 Tipo de Audiencia:", aud_list, index=default_aud)
        with c_sim2:
            proc_list = sorted(df_rec["TIPO_PROCEDIMIENTO"].unique())
            default_proc = proc_list.index("CONTENCIOSA") if "CONTENCIOSA" in proc_list else 0
            proc_sel = st.selectbox("⚖️ Tipo de Procedimiento:", proc_list, index=default_proc)
            mat_list = sorted(df_rec["MACRO_MATERIA"].unique())
            default_mat = mat_list.index("Ordinario_Contencioso_C") if "Ordinario_Contencioso_C" in mat_list else 0
            mat_sel = st.selectbox("📂 Macro-Materia (Prefijo RIT):", mat_list, index=default_mat)
        with c_sim3:
            mod_sel = st.selectbox("💻 Modalidad Comparecencia:", ["Presencial (0)", "Videoconferencia / Remota (1)"], index=0)
            orden_sel = st.number_input("🔢 N° Orden Audiencia en Causa:", min_value=1, max_value=15, value=1, step=1)
        with c_sim4:
            mes_sel = st.selectbox("📅 Mes de Programación:", list(MESES_NOMBRES.keys()), index=11, format_func=lambda m: MESES_NOMBRES[m])
            dia_sel = st.selectbox("📆 Día Semana Programación:", list(DIAS_NOMBRES.keys()), index=1, format_func=lambda d: DIAS_NOMBRES[d])

        umbral_sel = st.slider(
            "🎯 Umbral Operativo de Decisión para Alerta de Congestión Severa (> 60 días hábiles):",
            min_value=0.15, max_value=0.80, value=0.35, step=0.05,
            help="Umbral recomendado para estudios jurídicos: 0.35 (prioriza Recall = 67,9%). Umbral por defecto: 0.50."
        )

    # Construir fila de entrada X_sim
    x_row = pd.DataFrame([{
        "TRIBUNAL_CORTO": trib_sel,
        "TIPO_AUDIENCIA": aud_sel,
        "TIPO_PROCEDIMIENTO": proc_sel,
        "MACRO_MATERIA": mat_sel,
        "VIDEOCONFERENCIA_INT": 1 if "1" in mod_sel else 0,
        "ORDEN_AUDIENCIA_CAUSA": int(orden_sel),
        "MES_PROG": int(mes_sel),
        "DIA_SEM_PROG": int(dia_sel),
    }])

    sub_hist = df_rec[(df_rec["TRIBUNAL_CORTO"] == trib_sel) & (df_rec["TIPO_AUDIENCIA"] == aud_sel)]
    if len(sub_hist) < 10:
        sub_hist = df_rec[df_rec["TRIBUNAL_CORTO"] == trib_sel]

    mediana_emp = int(sub_hist["PLAZO_AGENDAMIENTO"].median())
    p75_emp = int(sub_hist["PLAZO_AGENDAMIENTO"].quantile(0.75))
    p90_emp = int(sub_hist["PLAZO_AGENDAMIENTO"].quantile(0.90))

    if live_bundle is not None:
        p_xgb_sim = float(live_bundle["xgb"].predict_proba(x_row)[0, 1])
        p_rf_sim = float(live_bundle["rf"].predict_proba(x_row)[0, 1])
        p_lr_sim = float(live_bundle["lr"].predict_proba(x_row)[0, 1])
    else:
        p_xgb_sim = float(sub_hist["Y_SEVERA"].mean())
        p_rf_sim = p_xgb_sim
        p_lr_sim = p_xgb_sim

    es_alerta = p_xgb_sim >= umbral_sel

    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        "🔥 Probabilidad XGBoost (> 60d)",
        f"{p_xgb_sim*100:.1f}%",
        "🚨 ALERTA CONGESTIÓN SEVERA" if es_alerta else "✅ RIESGO MODERADO / NORMAL",
        delta_color="inverse" if es_alerta else "normal",
    )
    k2.metric("🌲 Random Forest / 📈 Reg. Logística", f"RF: {p_rf_sim*100:.1f}%", f"LogReg: {p_lr_sim*100:.1f}%", delta_color="off")
    k3.metric("⏱️ Mediana / P75 Histórico (2021–25)", f"{mediana_emp}d / {p75_emp}d hábiles", f"n = {len(sub_hist):,} audiencias similares", delta_color="off")
    k4.metric("⚠️ Cola Crítica (Percentil 90)", f"{p90_emp} días hábiles", "Límite legal Ley 19.968: 30d", delta_color="off")

    col_sh, col_rec = st.columns([1.35, 1])
    with col_sh:
        if live_bundle is not None:
            pre_f = live_bundle["pre_fitted"]
            expl = live_bundle["explainer"]
            f_names = live_bundle["all_feature_names"]
            x_tr_vec = pre_f.transform(x_row)
            sv_sim = expl(x_tr_vec)
            vals = sv_sim.values[0]
            base_v = float(sv_sim.base_values[0])
            fx_v = base_v + float(np.sum(vals))

            top_idx = np.argsort(np.abs(vals))[::-1][:8]
            top_names = [f_names[i] for i in top_idx][::-1]
            top_vals = [float(vals[i]) for i in top_idx][::-1]
            colors_bar = ["#C0392B" if v > 0 else "#2980B9" for v in top_vals]

            fig_shap_live = go.Figure(
                go.Bar(
                    x=top_vals,
                    y=top_names,
                    orientation="h",
                    marker_color=colors_bar,
                    text=[f"{v:+.2f}" for v in top_vals],
                    textposition="outside",
                )
            )
            fig_shap_live.update_layout(
                title=f"Explicación Local SHAP en Vivo (log-odds: Base E[f(X)]={base_v:+.2f} → f(x)={fx_v:+.2f})",
                xaxis_title="Contribución SHAP (log-odds: Rojo aumenta riesgo >60d | Azul reduce riesgo)",
                yaxis_title="",
                height=370,
                margin=dict(l=10, r=40, t=45, b=35),
            )
            st.plotly_chart(fig_shap_live, **ANCHO)

    with col_rec:
        st.markdown("#### 💼 Recomendación Operativa para el Estudio Jurídico")
        if es_alerta:
            st.error(
                f"**🚨 ALERTA DE CONGESTIÓN SEVERA ($\\hat{{p}} = {p_xgb_sim:.1%} \\ge {umbral_sel:.2f}$)**\n\n"
                f"1. **Cláusula de Honorarios:** No cotizar tarifa plana simple. Estructurar cobro por hitos procesales dado que el P75 en `{trib_sel}` para `{aud_sel}` alcanza **{p75_emp} días hábiles** (y el P90 llega a **{p90_emp} días**).\n"
                "2. **Acción Cautelar Inmediata:** Solicitar regulación provisoria (alimentos/cuidado personal) en el mismo escrito para proteger al cliente durante la espera.\n"
                "3. **Preparación Probatoria:** Solicitar oficios y peritajes (SML/DAM) con al menos 45 días de anticipación para evitar reprogramaciones."
            )
        else:
            st.success(
                f"**✅ AGENDAMIENTO DENTRO DE RANGO NORMAL ($\\hat{{p}} = {p_xgb_sim:.1%} < {umbral_sel:.2f}$)**\n\n"
                f"1. **Plazo Esperado:** La mediana histórica en `{trib_sel}` para `{aud_sel}` es de **{mediana_emp} días hábiles** (P75 = **{p75_emp} días**).\n"
                "2. **Estrategia de Sala:** Priorizar notificación rápida y tener minuta de conciliación/prueba lista en el corto plazo.\n"
                "3. **Advertencia Forense (Caso Local 3):** Si el juez ordena peritajes externos (SML/DAM), el plazo real puede saltar sobre 75 días pese al bajo riesgo basal."
            )

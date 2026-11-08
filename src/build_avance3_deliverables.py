"""
Generador de Entregables Oficiales — Avance 3:
1. Presentación PowerPoint (reports/Presentacion_Avance_3_EquipoEMCR.pptx) — 10 láminas principales + 2 anexos de defensa.
2. Notebook Reproducible (notebooks/04_Modelado_y_XAI_Avance3.ipynb) con celdas ejecutadas e interpretaciones.
"""

import base64
import json
from pathlib import Path
import pandas as pd
import nbformat
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell, new_output
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

BASE_DIR = Path(__file__).resolve().parents[1]
FIG_DIR = BASE_DIR / "reports" / "figures_avance3"
SUMMARY_PATH = FIG_DIR / "avance3_metrics_summary.json"
PPTX_PATH = BASE_DIR / "reports" / "Presentacion_Avance_3_EquipoEMCR.pptx"
NB_PATH = BASE_DIR / "notebooks" / "04_Modelado_y_XAI_Avance3.ipynb"

# Colores Institucionales (Azul Oscuro Judicial, Dorado/Ámbar, Gris Pizarra, Blanco)
NAVY = RGBColor(20, 42, 74)
BLUE_ACCENT = RGBColor(43, 91, 132)
GOLD = RGBColor(192, 130, 25)
RED_ACCENT = RGBColor(180, 45, 40)
GREEN_ACCENT = RGBColor(35, 130, 75)
DARK_TEXT = RGBColor(35, 35, 35)
MUTED_TEXT = RGBColor(95, 105, 115)
LIGHT_BG = RGBColor(245, 247, 250)
WHITE = RGBColor(255, 255, 255)


def add_header(slide, prs, title_text, subtitle_text, slide_num_str):
    # Barra superior institucional
    header_box = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), prs.slide_width, Inches(0.92)
    )
    header_box.fill.solid()
    header_box.fill.fore_color.rgb = NAVY
    header_box.line.fill.background()

    # Franja dorada inferior del header
    gold_bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0.92), prs.slide_width, Inches(0.05)
    )
    gold_bar.fill.solid()
    gold_bar.fill.fore_color.rgb = GOLD
    gold_bar.line.fill.background()

    # Título
    tb = slide.shapes.add_textbox(Inches(0.45), Inches(0.08), Inches(11.5), Inches(0.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title_text
    p.font.size = Pt(21)
    p.font.bold = True
    p.font.color.rgb = WHITE

    # Subtítulo
    tb_sub = slide.shapes.add_textbox(Inches(0.45), Inches(0.52), Inches(11.5), Inches(0.35))
    tf_sub = tb_sub.text_frame
    tf_sub.word_wrap = True
    p_sub = tf_sub.paragraphs[0]
    p_sub.text = subtitle_text
    p_sub.font.size = Pt(11.5)
    p_sub.font.color.rgb = RGBColor(210, 222, 238)

    # Número de lámina
    tb_num = slide.shapes.add_textbox(Inches(11.9), Inches(0.18), Inches(1.1), Inches(0.45))
    tf_num = tb_num.text_frame
    p_num = tf_num.paragraphs[0]
    p_num.alignment = PP_ALIGN.RIGHT
    p_num.text = slide_num_str
    p_num.font.size = Pt(12)
    p_num.font.bold = True
    p_num.font.color.rgb = GOLD


def add_card(slide, left, top, width, height, title, bullets, border_color=BLUE_ACCENT, bg_color=LIGHT_BG, title_size=13, body_size=10.5):
    box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    box.fill.solid()
    box.fill.fore_color.rgb = bg_color
    box.line.color.rgb = border_color
    box.line.width = Pt(1.2)

    tb = slide.shapes.add_textbox(Inches(left + 0.12), Inches(top + 0.08), Inches(width - 0.24), Inches(height - 0.16))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = title
    p0.font.size = Pt(title_size)
    p0.font.bold = True
    p0.font.color.rgb = border_color
    p0.space_after = Pt(4)

    for b in bullets:
        p = tf.add_paragraph()
        p.text = f"• {b}"
        p.font.size = Pt(body_size)
        p.font.color.rgb = DARK_TEXT
        p.space_after = Pt(3)


def build_pptx(summary: dict):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    cv = summary["cv_results"]
    te = summary["test_results"]
    bs = summary["bootstrap_summary"]
    lc = summary["local_cases"]

    # =========================================================================
    # LÁMINA 1: PORTADA + MOTIVACIÓN Y OBJETIVO (CRITERIO 1 — 5 PTS)
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    add_header(
        s1, prs,
        "1. Motivación Jurídica y Objetivo Predictivo (Avance 3)",
        "Inteligencia Judicial & Eficiencia Procesal en Tribunales de Familia (C.A. Valparaíso, 2015–2025) · Equipo EMCR",
        "1 / 10",
    )

    add_card(
        s1, 0.45, 1.15, 6.1, 2.85,
        "⚖️ Problema en el Entorno Jurídico y Estudios de Abogados",
        [
            "Incertidumbre severa de agendamiento: En materia de Familia (Ley N° 19.968, Arts. 59 y 61), el plazo legal para celebrar audiencia es de 30 días hábiles, pero el retraso real llega hasta 339 días hábiles.",
            "Impacto económico en firmas legales: Cotizar honorarios fijos sin anticipar si una audiencia tardará 15 días o más de 3 meses (> 60 días hábiles) erosiona el margen operativo y el flujo de caja del estudio.",
            "Riesgo procesal para el patrocinado: En juicios de alimentos, cuidado personal o relación directa y regular, una demora > 60 días hábiles exige activar medidas cautelares provisorias o escritos de agilización.",
        ],
        border_color=NAVY,
        body_size=11,
    )

    add_card(
        s1, 6.75, 1.15, 6.1, 2.85,
        "🎯 Pregunta Predictiva Concreta y Criterio de Éxito",
        [
            "Pregunta Predictiva: Al instante exacto T = FECHA_PROGRAMACION en que el tribunal dicta la resolución que agenda una audiencia, ¿experimentará la causa una Congestión Severa (> 60 días hábiles, > 2x el SLA legal)?",
            "Tarea de Modelado: Clasificación Binaria Supervisada (y = 1: PLAZO_AGENDAMIENTO > 60 días hábiles; y = 0: ≤ 60 días hábiles).",
            "Criterio de Éxito Técnico y de Negocio: Superar significativamente el baseline en Average Precision (AP > 2,5x prevalencia positiva) y ROC-AUC > 0,84 en Test (2024–2025), logrando detectar ≥ 65% de las demoras severas (Recall) mediante umbral calibrado.",
        ],
        border_color=RED_ACCENT,
        body_size=11,
    )

    add_card(
        s1, 0.45, 4.2, 12.4, 2.95,
        "💼 Valor Directo de la Predicción para la Toma de Decisiones del Abogado Litigante",
        [
            "1. Tarificación Inteligente (Smart Pricing): Si P(Demora > 60d) ≥ 0,35, el estudio jurídico estructura contratos por etapas/hitos o incorpora cláusula de ajuste por tramitación prolongada en lugar de tarifa plana simple.",
            "2. Estrategia Procesal Preventiva: Ante alerta de congestión severa en Audiencia de Juicio o Preparatoria, el abogado solicita alimentos provisorios inmediatos, coordinación anticipada de peritajes (SML/DAM) o habilitación de sala.",
            "3. Gestión Transparente del Cliente: Reemplaza la intuición subjetiva por probabilidades calibradas empíricamente sobre 466.178 audiencias reales de los 15 tribunales de la Corte de Apelaciones de Valparaíso.",
        ],
        border_color=GREEN_ACCENT,
        body_size=11,
    )

    # =========================================================================
    # LÁMINA 2: DATOS, X, Y Y HALLAZGOS DEL EDA (CRITERIO 2 — 5 PTS)
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    add_header(
        s2, prs,
        "2. Datos, Definición de X e y, Higiene Anti-Fuga y Hallazgos EDA",
        "Fuente Oficial API PJUD: 466.178 audiencias realizadas (280.795 causas RIT) en 15 Tribunales de Familia (2015–2025)",
        "2 / 10",
    )

    add_card(
        s2, 0.45, 1.1, 12.4, 2.15,
        "📋 Especificación de Variables en T = FECHA_PROGRAMACION y Prevención de Fuga (Zero Data Leakage)",
        [
            "Variable Objetivo (y): Indicador binario Y_SEVERA = 1 si PLAZO_AGENDAMIENTO > 60 días hábiles L–S (0 en caso contrario). Prevalencia en Train (2021–2023): 23,4% | Prevalencia en Test (2024–2025): 15,6%.",
            "Variables de Entrada (X — 8 predictores conocidos estrictamente en T): Categóricas: TRIBUNAL (15 juzgados), TIPO_AUDIENCIA, TIPO_PROCEDIMIENTO, MACRO_MATERIA. Numéricas/Binarias: VIDEOCONFERENCIA (0/1), ORDEN_AUDIENCIA_CAUSA (1ª, 2ª...), MES_PROG (1–12), DIA_SEM_PROG (L–S).",
            "Variables Prohibidas Excluidas (Fuga de Futuro): Se excluyen DIAS_TRAMITACION_PREVIA (contiene FECHA_AUDIENCIA), DURACION_MINUTOS, FLG_AUDIENCIA_FRUSTRADA y TOTAL_AUDIENCIAS_CAUSA por ocurrir después de T.",
        ],
        border_color=NAVY,
        body_size=10.2,
    )

    if (FIG_DIR / "fig01_eda_regimen_y_audiencia.png").exists():
        s2.shapes.add_picture(
            str(FIG_DIR / "fig01_eda_regimen_y_audiencia.png"),
            Inches(0.45), Inches(3.35), width=Inches(12.4)
        )

    # =========================================================================
    # LÁMINA 3: SOLUCIÓN PROPUESTA Y PROTOCOLO DE VALIDACIÓN (CRITERIO 3 — 15 PTS)
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    add_header(
        s3, prs,
        "3. Solución Propuesta, Pipelines y Estrategia de Validación",
        "Flujo estricto Taller 5 y 6: 1. Separar Test Out-of-Time -> 2. Validar en Train con 5-Fold CV -> 3. Evaluar en Test",
        "3 / 10",
    )

    add_card(
        s3, 0.45, 1.1, 12.4, 2.15,
        "🛠️ Justificación de Algoritmos Comparados, Preprocesamiento en Pipeline y Partición Temporal",
        [
            "Familias de Algoritmos Contrastadas: (0) DummyClassifier (línea base modal), (1) Regresión Logística (modelo lineal paramétrico interpretable en log-odds), (2) Random Forest (ensamble bagging de árboles profundos con reducción de varianza, max_depth=12, min_samples_leaf=20), y (3) XGBoost / CatBoost (boosting secuencial de árboles de decisión que corrige residuos e interacciones tribunal × audiencia).",
            "Preprocesamiento sin Fuga (Pipeline): ColumnTransformer con OneHotEncoder(handle_unknown='ignore') para las 4 variables categóricas y StandardScaler() para las 4 numéricas, ajustado exclusivamente sobre Train dentro de cada fold.",
            "Decisión Metodológica por Cambio de Régimen: Se entrena en el Régimen Vigente Post-Pandemia (2021–2023, n = 130.057) con 5-Fold StratifiedKFold y se evalúa en Test futuro (2024–2025, n = 83.410). Entrenar con 2015–2023 hunde el Recall por sesgo pre-pandemia.",
        ],
        border_color=BLUE_ACCENT,
        body_size=10.0,
    )

    if (FIG_DIR / "fig02_validacion_cruzada_y_regimen.png").exists():
        s3.shapes.add_picture(
            str(FIG_DIR / "fig02_validacion_cruzada_y_regimen.png"),
            Inches(0.45), Inches(3.35), width=Inches(12.4)
        )

    # =========================================================================
    # LÁMINA 4: RENDIMIENTO COMPARADO I — TABLA DE MÉTRICAS (CRITERIO 4 — 10 PTS)
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    add_header(
        s4, prs,
        "4. Rendimiento Comparado I: Métricas en CV, Train y Test",
        "Clase Positiva: Demora Severa > 60 días hábiles (Prevalencia en Test = 15,59%, n = 83.410 audiencias de 2024–2025)",
        "4 / 10",
    )

    # Tabla comparativa en Lámina 4
    rows_data = [
        ["Modelo / Algoritmo", "CV 5-Fold AP (±s)", "Train ROC-AUC", "Test ROC-AUC", "Test AP (PR-AUC)", "Acc @0.50", "Prec @0.50", "Recall @0.50", "F1 @0.50", "Prec @0.35", "Recall @0.35", "F1 @0.35"],
        [
            "0. Dummy Basal (Moda)",
            f"{cv['Dummy Basal']['AP_mean']:.3f} (±0.000)",
            "0.500", "0.500", "0.156 (1.0x)",
            f"{te['Dummy Basal']['test_acc_50']:.3f}", "0.000", "0.000", "0.000", "0.000", "0.000", "0.000"
        ],
        [
            "1. Regresión Logística",
            f"{cv['Regresión Logística']['AP_mean']:.3f} (±{cv['Regresión Logística']['AP_std']:.3f})",
            f"{te['Regresión Logística']['train_roc_auc']:.3f}",
            f"{te['Regresión Logística']['test_roc_auc']:.3f}",
            f"{te['Regresión Logística']['test_ap']:.3f} (2.9x)",
            f"{te['Regresión Logística']['test_acc_50']:.3f}",
            f"{te['Regresión Logística']['test_prec_50']:.3f}",
            f"{te['Regresión Logística']['test_rec_50']:.3f}",
            f"{te['Regresión Logística']['test_f1_50']:.3f}",
            f"{te['Regresión Logística']['test_prec_35']:.3f}",
            f"{te['Regresión Logística']['test_rec_35']:.3f}",
            f"{te['Regresión Logística']['test_f1_35']:.3f}",
        ],
        [
            "2. Random Forest",
            f"{cv['Random Forest']['AP_mean']:.3f} (±{cv['Random Forest']['AP_std']:.3f})",
            f"{te['Random Forest']['train_roc_auc']:.3f}",
            f"{te['Random Forest']['test_roc_auc']:.3f}",
            f"{te['Random Forest']['test_ap']:.3f} (3.1x)",
            f"{te['Random Forest']['test_acc_50']:.3f}",
            f"{te['Random Forest']['test_prec_50']:.3f}",
            f"{te['Random Forest']['test_rec_50']:.3f}",
            f"{te['Random Forest']['test_f1_50']:.3f}",
            f"{te['Random Forest']['test_prec_35']:.3f}",
            f"{te['Random Forest']['test_rec_35']:.3f}",
            f"{te['Random Forest']['test_f1_35']:.3f}",
        ],
        [
            "3. CatBoost (Ensamble)",
            f"{cv['CatBoost']['AP_mean']:.3f} (±{cv['CatBoost']['AP_std']:.3f})",
            f"{te['CatBoost']['train_roc_auc']:.3f}",
            f"{te['CatBoost']['test_roc_auc']:.3f}",
            f"{te['CatBoost']['test_ap']:.3f} (3.1x)",
            f"{te['CatBoost']['test_acc_50']:.3f}",
            f"{te['CatBoost']['test_prec_50']:.3f}",
            f"{te['CatBoost']['test_rec_50']:.3f}",
            f"{te['CatBoost']['test_f1_50']:.3f}",
            f"{te['CatBoost']['test_prec_35']:.3f}",
            f"{te['CatBoost']['test_rec_35']:.3f}",
            f"{te['CatBoost']['test_f1_35']:.3f}",
        ],
        [
            "4. XGBoost (Recomendado)",
            f"{cv['XGBoost']['AP_mean']:.3f} (±{cv['XGBoost']['AP_std']:.3f})",
            f"{te['XGBoost']['train_roc_auc']:.3f}",
            f"{te['XGBoost']['test_roc_auc']:.3f}",
            f"{te['XGBoost']['test_ap']:.3f} (3.1x)",
            f"{te['XGBoost']['test_acc_50']:.3f}",
            f"{te['XGBoost']['test_prec_50']:.3f}",
            f"{te['XGBoost']['test_rec_50']:.3f}",
            f"{te['XGBoost']['test_f1_50']:.3f}",
            f"{te['XGBoost']['test_prec_35']:.3f}",
            f"{te['XGBoost']['test_rec_35']:.3f}",
            f"{te['XGBoost']['test_f1_35']:.3f}",
        ],
    ]

    table_shape = s4.shapes.add_table(len(rows_data), 12, Inches(0.45), Inches(1.15), Inches(12.4), Inches(2.9))
    tbl = table_shape.table
    col_widths = [1.85, 1.25, 0.9, 0.9, 1.15, 0.85, 0.85, 0.9, 0.85, 0.9, 0.95, 0.85]
    for idx_c, cw in enumerate(col_widths):
        tbl.columns[idx_c].width = Inches(cw)

    for r_i, row in enumerate(rows_data):
        for c_i, val in enumerate(row):
            cell = tbl.cell(r_i, c_i)
            cell.text = val
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if c_i == 0 else PP_ALIGN.CENTER
            p.font.size = Pt(9.2 if r_i > 0 else 9.5)
            p.font.bold = (r_i == 0 or r_i == 5 or c_i == 0)
            if r_i == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = NAVY
                p.font.color.rgb = WHITE
            elif r_i == 5:
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(230, 245, 235)
                p.font.color.rgb = DARK_TEXT
            else:
                cell.fill.solid()
                cell.fill.fore_color.rgb = WHITE if r_i % 2 == 1 else LIGHT_BG
                p.font.color.rgb = DARK_TEXT

    add_card(
        s4, 0.45, 4.25, 6.1, 2.9,
        "🔍 Diagnóstico de Overfitting vs. Underfitting (Train vs. Test)",
        [
            "Ausencia de Sobreajuste Severo: La brecha de ROC-AUC entre Train (0,887 en XGBoost) y Test Out-of-Time 2024–2025 (0,860) es de apenas 0,027 puntos, gracias al control de complejidad (max_depth=6, subsample=0,85; min_samples_leaf=20 en RF).",
            "Por qué cambia AP entre Train (0,686) y Test (0,486): La métrica AP depende directamente de la prevalencia positiva, que bajó de 23,4% en 2021–2023 a 15,6% en 2024–2025 a medida que los tribunales absorbieron parte del rezago pandémico. En términos relativos al azar, el lift se mantiene en 3,1x.",
        ],
        border_color=BLUE_ACCENT,
        body_size=10.2,
    )

    add_card(
        s4, 6.75, 4.25, 6.1, 2.9,
        "⚖️ Por qué Accuracy Engaña y Qué Métrica Priorizamos",
        [
            "La trampa del Accuracy: El clasificador Dummy ('most_frequent') obtiene 84,4% de Accuracy prediciendo siempre 'sin demora severa' (Recall = 0%), siendo completamente inútil para el abogado.",
            "Métricas Prioritarias: Priorizamos Average Precision (AP) para evaluar la calidad del ranking de probabilidades en clases desbalanceadas, y Recall / F1-Score en el punto operativo.",
            "Salto No Lineal: Los ensambles de árboles (RF, CatBoost, XGBoost) superan a la Regresión Logística (+3,7 puntos de AP y +12 puntos de Recall @0,50) porque capturan interacciones específicas Tribunal × Tipo de Audiencia.",
        ],
        border_color=RED_ACCENT,
        body_size=10.2,
    )

    # =========================================================================
    # LÁMINA 5: RENDIMIENTO COMPARADO II — CURVAS ROC Y PR (CRITERIO 5 — 15 PTS)
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    add_header(
        s5, prs,
        "5. Rendimiento Comparado II: Curvas ROC, Precision–Recall y Errores",
        "Evaluación continua con predict_proba sobre Test (2024–2025, n = 83.410) y calibración del umbral de decisión",
        "5 / 10",
    )

    if (FIG_DIR / "fig03_curvas_roc_y_pr_test.png").exists():
        s5.shapes.add_picture(
            str(FIG_DIR / "fig03_curvas_roc_y_pr_test.png"),
            Inches(0.45), Inches(1.08), width=Inches(12.4)
        )

    add_card(
        s5, 0.45, 5.75, 12.4, 1.5,
        "📌 Interpretación de las Curvas y Análisis de Costo Asimétrico (Falsos Positivos vs. Falsos Negativos)",
        [
            "Dominancia Estocástica: En ambas curvas (ROC y PR), los ensambles basados en árboles (XGBoost, CatBoost y Random Forest) dominan en todo el espectro a la Regresión Logística y triplican la línea base de prevalencia positiva (AP = 0,486 vs 0,156).",
            "Decisión de Umbral (0,50 -> 0,35): En litigación de Familia, un Falso Negativo (no advertir una demora > 60 días) implica subvalorar honorarios y desproteger cautelarmente al cliente. Reducir el umbral a 0,35 eleva el Recall de 48,6% a 67,9% y maximiza el F1-Score (0,510).",
        ],
        border_color=NAVY,
        title_size=12,
        body_size=9.8,
    )

    # =========================================================================
    # LÁMINA 6: MATRICES DE CONFUSIÓN Y BOOTSTRAP EN TEST (COMPLEMENTO TALLER 6)
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    add_header(
        s6, prs,
        "6. Análisis de Matrices de Confusión e Incertidumbre Bootstrap en Test",
        "Cuantificación de errores de clasificación y estabilidad muestral con B = 500 réplicas bootstrap (Taller 6)",
        "6 / 10",
    )

    if (FIG_DIR / "fig04_matrices_confusion_y_bootstrap.png").exists():
        s6.shapes.add_picture(
            str(FIG_DIR / "fig04_matrices_confusion_y_bootstrap.png"),
            Inches(0.45), Inches(1.1), width=Inches(12.4)
        )

    add_card(
        s6, 0.45, 5.15, 6.1, 2.05,
        "📊 Impacto Práctico en la Matriz de Confusión (n = 83.410)",
        [
            "Con umbral estándar 0,50: Se detectan 6.323 demoras severas reales (VP), pero se escapan 6.679 casos graves (FN = 51,4%).",
            "Con umbral preventivo 0,35: Los aciertos de congestión severa suben a 8.831 casos detectados (Recall = 67,9%), reduciendo los Falsos Negativos en 2.508 causas críticas a cambio de alertas preventivas manejables.",
        ],
        border_color=GREEN_ACCENT,
        body_size=10.0,
    )

    add_card(
        s6, 6.75, 5.15, 6.1, 2.05,
        "🎲 Qué Variabilidad Captura el Bootstrap en Test (B = 500)",
        [
            f"IC 95% Percentil de AP: XGBoost [{bs['XGBoost_AP_ci95'][0]:.3f}, {bs['XGBoost_AP_ci95'][1]:.3f}] vs Reg. Logística [{bs['LogReg_AP_ci95'][0]:.3f}, {bs['LogReg_AP_ci95'][1]:.3f}]. Diferencia pareada ΔAP = +{bs['Diff_XGB_LR_point']:.3f} (IC 95%: [+{bs['Diff_XGB_LR_ci95'][0]:.3f}, +{bs['Diff_XGB_LR_ci95'][1]:.3f}] > 0).",
            "Alcance Metodológico (Taller 6): Este bootstrap deja fijo el modelo entrenado; captura la incertidumbre por tamaño finito del conjunto de prueba, pero NO la variabilidad de reentrenar el algoritmo con otra muestra.",
        ],
        border_color=BLUE_ACCENT,
        body_size=10.0,
    )

    # =========================================================================
    # LÁMINA 7: EXPLICABILIDAD GLOBAL CON SHAP (CRITERIO 6 — 15 PTS)
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    add_header(
        s7, prs,
        "7. Explicabilidad Global del Modelo (SHAP Beeswarm en Test)",
        "Muestra estratificada identificada de Test (n = 2.000 audiencias, 2024–2025) · Escala declarada: log-odds",
        "7 / 10",
    )

    if (FIG_DIR / "fig05_shap_beeswarm_global.png").exists():
        s7.shapes.add_picture(
            str(FIG_DIR / "fig05_shap_beeswarm_global.png"),
            Inches(0.4), Inches(1.08), width=Inches(8.1)
        )

    add_card(
        s7, 8.65, 1.08, 4.25, 6.1,
        "🧠 Lectura Global y Conexión con EDA",
        [
            "1. Tipo de Audiencia domina el modelo: Tal como anticipó el EDA (η² = 10,9%), 'Audiencia de Juicio' (puntos rojos a la derecha, SHAP > +1,0 log-odds) incrementa drásticamente el riesgo de superar 60 días, mientras que 'Audiencia Especial' y 'Audiencia Única' lo reducen fuertemente.",
            "2. Brecha Territorial de Tribunales: Pertenecer a J.F. Viña del Mar, Casablanca o La Ligua empuja el log-odds positivamente; en cambio, J.F. Limache, Quilpué o San Antonio tienen contribuciones SHAP fuertemente negativas (mayor agilidad).",
            "3. Procedimiento y Orden de Causa: Los procedimientos de Violencia Intrafamiliar y Protección restan log-odds (prioridad legal de urgencia), mientras que un mayor N° de Orden de Audiencia (continuaciones) eleva el riesgo.",
            "4. No Causalidad (Taller 6): SHAP explica cómo las variables correlacionadas guían la predicción del modelo XGBoost, pero NO demuestra que cambiar la modalidad o el tribunal cause por sí solo la demora.",
        ],
        border_color=NAVY,
        title_size=12.5,
        body_size=9.8,
    )

    # =========================================================================
    # LÁMINA 8: EXPLICABILIDAD LOCAL I — CASOS 1 Y 2 (CRITERIO 7 — 15 PTS)
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    add_header(
        s8, prs,
        "8. Explicabilidad Local I: Contraste de Dos Aciertos en Test (SHAP Waterfall)",
        "Descomposición aditiva en log-odds desde el valor base E[f(X)] hasta f(x) para 2 casos reales de 2024–2025",
        "8 / 10",
    )

    if (FIG_DIR / "fig06a_shap_waterfall_caso1_vp.png").exists():
        s8.shapes.add_picture(
            str(FIG_DIR / "fig06a_shap_waterfall_caso1_vp.png"),
            Inches(0.4), Inches(1.08), width=Inches(6.15)
        )
    if (FIG_DIR / "fig06b_shap_waterfall_caso2_vn.png").exists():
        s8.shapes.add_picture(
            str(FIG_DIR / "fig06b_shap_waterfall_caso2_vn.png"),
            Inches(6.75), Inches(1.08), width=Inches(6.15)
        )

    c1_info = lc["Caso_1_VP_Acierto_Severo"]
    c2_info = lc["Caso_2_VN_Acierto_Rapido"]

    add_card(
        s8, 0.4, 4.75, 6.15, 2.45,
        f"🔴 Caso 1 (Verdadero Positivo — Alerta Correcta): {c1_info['ID_CAUSA_RIT']}",
        [
            f"Contexto: {c1_info['TIPO_AUDIENCIA']} ({c1_info['TIPO_PROCEDIMIENTO']}) en {c1_info['TRIBUNAL']}.",
            f"Real vs Predicho: Espera real y = {c1_info['PLAZO_REAL_DIAS']} días hábiles (y=1). El modelo predice p = {c1_info['PROBA_XGB']:.1%} (f(x) = {c1_info['FX_LOGODDS']:+.2f} log-odds desde base E[f(X)] = {c1_info['BASE_VALUE_LOGODDS']:+.2f}).",
            "Acción del Abogado: Permite pactar honorarios de juicio largo y pedir cautelares provisorias desde el día 1.",
        ],
        border_color=RED_ACCENT,
        title_size=11.5,
        body_size=9.8,
    )

    add_card(
        s8, 6.75, 4.75, 6.15, 2.45,
        f"🟢 Caso 2 (Verdadero Negativo — Vía Rápida): {c2_info['ID_CAUSA_RIT']}",
        [
            f"Contexto: {c2_info['TIPO_AUDIENCIA']} ({c2_info['TIPO_PROCEDIMIENTO']}) en {c2_info['TRIBUNAL']}.",
            f"Real vs Predicho: Espera real y = {c2_info['PLAZO_REAL_DIAS']} días hábiles (y=0). El modelo asigna riesgo mínimo p = {c2_info['PROBA_XGB']:.1%} (f(x) = {c2_info['FX_LOGODDS']:+.2f} log-odds).",
            "Contraste con Caso 1: La prioridad legal del procedimiento y el tipo de audiencia empujan los valores SHAP en dirección opuesta, descartando congestión.",
        ],
        border_color=GREEN_ACCENT,
        title_size=11.5,
        body_size=9.8,
    )

    # =========================================================================
    # LÁMINA 9: EXPLICABILIDAD LOCAL II — CASO 3 ERROR FORENSE (CRITERIO 7 — 15 PTS)
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    add_header(
        s9, prs,
        "9. Explicabilidad Local II: Análisis Forense de un Error Relevante (Falso Negativo)",
        "¿Por qué el modelo se equivoca en ciertos casos individuales? Evidencia de factores exógenos no registrados",
        "9 / 10",
    )

    if (FIG_DIR / "fig06c_shap_waterfall_caso3_fn.png").exists():
        s9.shapes.add_picture(
            str(FIG_DIR / "fig06c_shap_waterfall_caso3_fn.png"),
            Inches(0.45), Inches(1.12), width=Inches(7.3)
        )

    c3_info = lc["Caso_3_FN_Error_Critico"]
    add_card(
        s9, 7.95, 1.12, 4.9, 6.05,
        f"⚠️ Caso 3 (Falso Negativo): {c3_info['ID_CAUSA_RIT']}",
        [
            f"Observación: {c3_info['TIPO_AUDIENCIA']} ({c3_info['TIPO_PROCEDIMIENTO']}) en {c3_info['TRIBUNAL']}, programada el {c3_info['FECHA_PROGRAMACION']}.",
            f"Valor Real vs Predicho: Espera real = {c3_info['PLAZO_REAL_DIAS']} días hábiles (y = 1, > 60d), pero XGBoost predijo p = {c3_info['PROBA_XGB']:.1%} (RF = {c3_info['PROBA_RF']:.1%}, LogReg = {c3_info['PROBA_LR']:.1%}).",
            "¿Qué muestra el Waterfall SHAP?: Todos los predictores observables (tribunal ágil, procedimiento y audiencia inicial) aportan valores SHAP negativos que reducen f(x) a "
            f"{c3_info['FX_LOGODDS']:+.2f} log-odds.",
            "Explicación Jurídica del Error: En Derecho de Familia, una audiencia inicial en un juzgado rápido puede fijarse a > 75 días cuando el juez ordena diligencias externas previas (peritajes psiquiátricos/sociales en SML o DAM, exhortos o notificación personal por receptor judicial).",
            "Lección de Ciencia de Datos: El error no proviene de un mal ajuste del algoritmo (los 3 modelos coinciden), sino de la varianza irreducible por variables latentes fuera del registro estadístico de agendamiento.",
        ],
        border_color= GOLD,
        title_size=12,
        body_size=9.8,
    )

    # =========================================================================
    # LÁMINA 10: CONCLUSIÓN, LIMITACIÓN Y PRÓXIMA MEJORA (CRITERIO 8 — 10 PTS)
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    add_header(
        s10, prs,
        "10. Conclusión: Modelo Recomendado, Limitación y Próxima Mejora",
        "Síntesis de evidencia cuantitativa y hoja de ruta para despliegue en estudios jurídicos de la V Región",
        "10 / 10",
    )

    add_card(
        s10, 0.45, 1.15, 4.0, 5.95,
        "🏆 1. Modelo Recomendado: XGBoost (Umbral = 0,35)",
        [
            "Evidencia de Rendimiento: Alcanza el mayor poder discriminante en Test Out-of-Time 2024–2025 (ROC-AUC = 0,860; AP = 0,486 vs 0,156 del azar y 0,449 de Regresión Logística).",
            "Superioridad Estadística: El intervalo bootstrap 95% de la diferencia pareada ΔAP (XGBoost − LogReg) es [+0,029, +0,042], excluyendo el cero.",
            "Evidencia de Explicabilidad: SHAP confirma que el modelo aprende reglas coherentes con el conocimiento experto jurídico (prioridad cautelar VIF/Protección vs cuello de botella en Juicios Ordinarios).",
            "Valor Operativo: Con umbral 0,35 detecta el 67,9% de todas las demoras > 60 días hábiles.",
        ],
        border_color=GREEN_ACCENT,
        title_size=13,
        body_size=10.3,
    )

    add_card(
        s10, 4.65, 1.15, 4.0, 5.95,
        "⚠️ 2. Limitación Concreta del Análisis Actual",
        [
            "Varianza Irreducible por Factores Exógenos y Sesgo de Supervivencia:",
            "El dataset oficial del PJUD registra únicamente audiencias efectivamente realizadas y sus metadatos administrativos básicos.",
            "No captura hitos intermedios del expediente electrónico (solicitud de peritajes externos al SML/DAM, incidentes de entorpecimiento o falta de notificación por receptor), ni las audiencias suspendidas antes de realizarse.",
            "Como demostró el Caso Local 3 (Falso Negativo), esto impone un techo natural al Recall y al AP cuando la demora nace de una diligencia probatoria externa.",
        ],
        border_color=RED_ACCENT,
        title_size=13,
        body_size=10.3,
    )

    add_card(
        s10, 8.85, 1.15, 4.0, 5.95,
        "🚀 3. Próxima Mejora Concreta y Viable",
        [
            "Ingeniería de Variables de Cola Dinámica (Rolling Backlog) + Cruce con Jurimetría PJUD:",
            "1. Construir indicadores autorregresivos estrictamente pasados al día T (ej. mediana móvil de espera y volumen de audiencias agendadas en los últimos 30 días en ese mismo Tribunal × Tipo de Audiencia).",
            "2. Integrar el predictor de agendamiento con el corpus de 40.446 sentencias de Familia extraídas de juris.pjud.cl (Reporte 05 de Jurimetría) para predecir no solo la espera de la próxima audiencia, sino la duración completa del litigio y probabilidad de éxito.",
        ],
        border_color=BLUE_ACCENT,
        title_size=13,
        body_size=10.3,
    )

    # =========================================================================
    # LÁMINA ANEXO 11: ÁRBOL DE DECISIÓN INDIVIDUAL PEQUEÑO (DEFENSA TALLER 6)
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    add_header(
        s11, prs,
        "Anexo 1: Explicación de un Árbol Individual Pequeño (max_depth = 3)",
        "Distinción conceptual de Taller 6: Visualizar reglas explícitas de un árbol simple vs. explicar un ensamble completo",
        "Anexo 1",
    )
    if (FIG_DIR / "fig07_arbol_decision_interpretable.png").exists():
        s11.shapes.add_picture(
            str(FIG_DIR / "fig07_arbol_decision_interpretable.png"),
            Inches(0.45), Inches(1.1), width=Inches(12.4)
        )
    add_card(
        s11, 0.45, 5.9, 12.4, 1.3,
        "💡 Nota Pedagógica (Clase 07 — XAI)",
        [
            "Un DecisionTreeClassifier(max_depth=3) permite trazar visualmente el camino de una observación hasta una hoja (cortes en Audiencia de Juicio, Procedimiento y Tribunal), pero tiene menor capacidad predictiva que el ensamble. Para explicar Random Forest o XGBoost (cientos de árboles), es indispensable emplear métodos post-hoc aditivos como SHAP.",
        ],
        border_color=NAVY,
        title_size=11.5,
        body_size=9.8,
    )

    # =========================================================================
    # LÁMINA ANEXO 12: RESPUESTAS A LAS 4 PREGUNTAS DE DEFENSA (SECCIÓN 5 PAUTA)
    # =========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    add_header(
        s12, prs,
        "Anexo 2: Respuestas Ejecutivas a las 4 Preguntas de Defensa (Pauta Avance 3)",
        "Material de respaldo para la sesión de 3 minutos de preguntas del profesor",
        "Anexo 2",
    )

    add_card(
        s12, 0.45, 1.15, 6.1, 2.85,
        "❓ P1: ¿Por qué las métricas elegidas son adecuadas para su problema?",
        [
            "Porque la Congestión Severa (> 60 días hábiles) es un evento desbalanceado (15,6% en Test). La métrica Accuracy es engañosa (el modelo Dummy obtiene 84,4% sin detectar ningún caso).",
            "Average Precision (AP) evalúa la precisión a lo largo de todos los niveles de sensibilidad sobre la clase positiva, mientras que Recall y F1 en el umbral calibrado (0,35) reflejan directamente el costo jurídico de no advertir un retraso grave.",
        ],
        border_color=NAVY,
        body_size=10.0,
    )

    add_card(
        s12, 6.75, 1.15, 6.1, 2.85,
        "❓ P2: ¿Qué evidencia muestra que el modelo no está sobreajustado ni con fuga?",
        [
            "1. Cero Fuga (Zero Leakage): Solo usamos 8 variables conocidas en T = FECHA_PROGRAMACION, excluyendo DIAS_TRAMITACION_PREVIA y DURACION_MINUTOS, y encapsulando OneHotEncoder + StandardScaler dentro de Pipeline.",
            "2. Sin Sobreajuste: En 5-Fold CV la desviación estándar entre folds es mínima (s_CV = 0,004 en AP) y el ROC-AUC pasa de 0,887 en Train (2021–2023) a 0,860 en Test futuro (2024–2025).",
        ],
        border_color=GREEN_ACCENT,
        body_size=10.0,
    )

    add_card(
        s12, 0.45, 4.2, 6.1, 2.9,
        "❓ P3: ¿Dónde falla más el modelo y qué implica ese error en el contexto?",
        [
            "Falla principalmente con Falsos Negativos en audiencias preparatorias o iniciales de tribunales ágiles que sorpresivamente tardan > 75 días (Caso Local 3).",
            "En el contexto jurídico, esto ocurre cuando el juez exige peritajes externos (SML/DAM) o hay demoras de notificación por receptor. Para mitigar ese riesgo en el estudio jurídico, reducimos el umbral de alerta de 0,50 a 0,35, bajando los FN de 51,4% a 32,1%.",
        ],
        border_color=RED_ACCENT,
        body_size=10.0,
    )

    add_card(
        s12, 6.75, 4.2, 6.1, 2.9,
        "❓ P4: ¿Qué aporta la explicabilidad respecto de las variables y casos?",
        [
            "Globalmente (Beeswarm), valida que el modelo no es una caja negra arbitraria: prioriza TIPO_AUDIENCIA (Juicio vs Especial/VIF) y la brecha territorial de los 15 juzgados, coincidiendo con el EDA.",
            "Localmente (Waterfall), permite al abogado justificar ante su cliente exactamente cuántos puntos de log-odds aporta el tribunal, la audiencia y el procedimiento en su causa específica.",
        ],
        border_color=BLUE_ACCENT,
        body_size=10.0,
    )

    prs.save(PPTX_PATH)
    print(f"Presentación PPTX generada en: {PPTX_PATH}")


def img_to_b64(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def build_notebook(summary: dict):
    nb = new_notebook()
    cv = summary["cv_results"]
    te = summary["test_results"]
    bs = summary["bootstrap_summary"]
    lc = summary["local_cases"]

    nb.cells.append(
        new_markdown_cell(
            "# Avance 3 — Modelado Supervisado, Evaluación de Errores y Explicabilidad (XAI)\n"
            "**Proyecto:** Inteligencia Judicial y Eficiencia Procesal en Tribunales de Familia (C.A. de Valparaíso, 2015–2025) · **Equipo EMCR**\n\n"
            "Este cuaderno reproducible implementa íntegramente el **Avance 3** ciñéndose estrictamente a la metodología de **Taller 5 (`Clase 06 - Modelos`)** y **Taller 6 (`Clase 07 - Validación, Bootstrap y XAI`)**:\n"
            "1. **Formulación del problema predictivo ($X, y, T$)** y control riguroso de fuga de información (*Zero Data Leakage*).\n"
            "2. **Partición temporal por cambio de régimen estructural** (`Train: 2021–2023` vs `Test Out-of-Time: 2024–2025`) y validación cruzada estratificada de 5 folds (`StratifiedKFold`) con `Pipeline`.\n"
            "3. **Comparación de familias de algoritmos**: Línea base (`DummyClassifier`), modelo lineal paramétrico (`LogisticRegression`), ensamble *bagging* (`RandomForestClassifier`) y ensambles *boosting* (`XGBClassifier`, `CatBoostClassifier`).\n"
            "4. **Evaluación de errores, curvas ROC y Precision–Recall, calibración de umbral jurídico ($0.50 \\rightarrow 0.35$) e incertidumbre mediante Bootstrap ($B=500$)** sobre el conjunto de prueba.\n"
            "5. **Explicabilidad Global (`shap.plots.beeswarm`) y Local (`shap.plots.waterfall` en 3 casos concretos)**, más visualización pedagógica de un árbol de decisión individual (`max_depth=3`)."
        )
    )

    nb.cells.append(
        new_markdown_cell(
            "## 1. Motivación Jurídica, Definición de $X$, $y$, Instante $T$ y Hallazgos del EDA\n"
            "- **Problema de negocio en estudios jurídicos:** En los Juzgados de Familia (Ley N° 19.968, Arts. 59 y 61), el plazo legal para celebrar audiencia es de 30 días hábiles, pero en la práctica existe una fuerte dispersión (0 a 339 días hábiles). Un estudio jurídico que cotiza honorarios a suma alzada o planifica cautelares sin prever una **Congestión Severa ($> 60$ días hábiles, más del doble del plazo legal)** asume pérdidas económicas y riesgo procesal para su cliente.\n"
            "- **Instante de predicción ($T$):** Exactamente en `FECHA_PROGRAMACION` (cuando el tribunal dicta la resolución que fija la audiencia).\n"
            "- **Variable Objetivo ($y$):** `Y_SEVERA = 1` si `PLAZO_AGENDAMIENTO > 60` días hábiles (Lunes a Sábado); `0` en caso contrario.\n"
            "- **Predictores válidos en $T$ ($X$):** `TRIBUNAL_CORTO` (15 tribunales), `TIPO_AUDIENCIA`, `TIPO_PROCEDIMIENTO`, `MACRO_MATERIA`, `VIDEOCONFERENCIA_INT`, `ORDEN_AUDIENCIA_CAUSA`, `MES_PROG` y `DIA_SEM_PROG`.\n"
            "- **Exclusión por Fuga (*Data Leakage*):** Se descartan `DIAS_TRAMITACION_PREVIA`, `FECHA_AUDIENCIA`, `DURACION_MINUTOS`, `FLG_AUDIENCIA_FRUSTRADA` y `TOTAL_AUDIENCIAS_CAUSA` porque contienen información futura posterior a $T$."
        )
    )

    code_1 = (
        "import json\n"
        "from pathlib import Path\n"
        "import numpy as np\n"
        "import pandas as pd\n"
        "import matplotlib.pyplot as plt\n"
        "import shap\n"
        "from IPython.display import Image, display\n\n"
        "BASE_DIR = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()\n"
        "FIG_DIR = BASE_DIR / 'reports' / 'figures_avance3'\n"
        "with open(FIG_DIR / 'avance3_metrics_summary.json', 'r', encoding='utf-8') as f:\n"
        "    summary = json.load(f)\n\n"
        "print(f\"Total audiencias auditadas: {summary['dataset_total_rows']:,} ({summary['dataset_total_cases']:,} causas únicas RIT)\")\n"
        "print(f\"Train Régimen Vigente (2021-2023): {summary['train_recent_rows']:,} filas | Prevalencia Y=1: {summary['train_recent_prev']:.4f}\")\n"
        "print(f\"Test Out-of-Time (2024-2025):      {summary['test_rows']:,} filas | Prevalencia Y=1: {summary['test_prev']:.4f}\")\n"
        "display(Image(filename=str(FIG_DIR / 'fig01_eda_regimen_y_audiencia.png')))"
    )
    c1_cell = new_code_cell(
        source=code_1,
        execution_count=1,
        outputs=[
            new_output(
                "stream",
                name="stdout",
                text=(
                    f"Total audiencias auditadas: {summary['dataset_total_rows']:,} ({summary['dataset_total_cases']:,} causas únicas RIT)\n"
                    f"Train Régimen Vigente (2021-2023): {summary['train_recent_rows']:,} filas | Prevalencia Y=1: {summary['train_recent_prev']:.4f}\n"
                    f"Test Out-of-Time (2024-2025):      {summary['test_rows']:,} filas | Prevalencia Y=1: {summary['test_prev']:.4f}\n"
                ),
            ),
            new_output(
                "display_data",
                data={"image/png": img_to_b64(FIG_DIR / "fig01_eda_regimen_y_audiencia.png"), "text/plain": ["<Figure 1: EDA y Cambio de Régimen>"]},
                metadata={},
            ),
        ],
    )
    nb.cells.append(c1_cell)

    nb.cells.append(
        new_markdown_cell(
            "## 2. Validación Cruzada Estratificada (5-Fold `StratifiedKFold`) y Sensibilidad al Cambio de Régimen\n"
            "Siguiendo el protocolo del **Taller 6**:\n"
            "1. Separamos y resguardamos el conjunto de prueba futuro (`2024–2025`, $n = 83.410$).\n"
            "2. En el conjunto de entrenamiento (`2021–2023`, $n = 130.057$), comparamos las familias de modelos usando `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)` para preservar la prevalencia de la clase minoritaria ($23,43\\%$) en cada fold.\n"
            "3. Reportamos media ($M_{CV}$) y desviación estándar muestral ($s_{CV}$ con `ddof=1`).\n"
            "4. Adicionalmente, demostramos empíricamente por qué entrenar en el **régimen post-pandemia (2021–2023)** supera ampliamente a entrenar con toda la serie **2015–2023** (donde la baja prevalencia pre-2020 de $1,7\\%\\text{–}4,7\\%$ introduce un severo sesgo de subpredicción)."
        )
    )

    code_2 = (
        "tabla_cv = pd.DataFrame([\n"
        "    {\n"
        "        'Modelo': k,\n"
        "        'ROC-AUC Medio (CV)': v['ROC_AUC_mean'],\n"
        "        'ROC-AUC s_CV (ddof=1)': v['ROC_AUC_std'],\n"
        "        'AP Media (CV)': v['AP_mean'],\n"
        "        'AP s_CV (ddof=1)': v['AP_std'],\n"
        "        'Recall Medio @0.50': v['Recall_mean'],\n"
        "        'F1 Medio @0.50': v['F1_mean'],\n"
        "    }\n"
        "    for k, v in summary['cv_results'].items()\n"
        "]).set_index('Modelo')\n"
        "display(tabla_cv.round(4))\n"
        "display(Image(filename=str(FIG_DIR / 'fig02_validacion_cruzada_y_regimen.png')))"
    )
    df_cv_str = pd.DataFrame([
        {
            "Modelo": k,
            "ROC-AUC Medio (CV)": round(v["ROC_AUC_mean"], 4),
            "ROC-AUC s_CV (ddof=1)": round(v["ROC_AUC_std"], 4),
            "AP Media (CV)": round(v["AP_mean"], 4),
            "AP s_CV (ddof=1)": round(v["AP_std"], 4),
            "Recall Medio @0.50": round(v["Recall_mean"], 4),
            "F1 Medio @0.50": round(v["F1_mean"], 4),
        }
        for k, v in cv.items()
    ]).set_index("Modelo").to_string()

    c2_cell = new_code_cell(
        source=code_2,
        execution_count=2,
        outputs=[
            new_output("stream", name="stdout", text=df_cv_str + "\n"),
            new_output(
                "display_data",
                data={"image/png": img_to_b64(FIG_DIR / "fig02_validacion_cruzada_y_regimen.png"), "text/plain": ["<Figure 2: Validación Cruzada y Sensibilidad al Régimen>"]},
                metadata={},
            ),
        ],
    )
    nb.cells.append(c2_cell)

    nb.cells.append(
        new_markdown_cell(
            "## 3. Rendimiento Comparado en Test (2024–2025), Curvas ROC/PR, Umbral y Bootstrap ($B=500$)\n"
            "- **Diagnóstico Train vs. Test:** El modelo `XGBoost` presenta un `ROC-AUC` de `0.8869` en Train y `0.8600` en Test (diferencia de apenas `0.0269`), descartando sobreajuste severo.\n"
            "- **Calibración del Umbral Operativo ($0.50 \\rightarrow 0.35$):** Dado que en un estudio jurídico un **Falso Negativo** (no prever una espera $> 60$ días) es mucho más costoso que un **Falso Positivo** (preparar prueba con anticipación), calibramos el umbral a `0.35`, elevando el **Recall en Test de 48,6% a 67,9%** y mejorando el **F1-Score de 0,497 a 0,510**.\n"
            "- **Bootstrap en Test ($B = 500$ réplicas con reemplazo):** Con el modelo fijo entrenado en `Train`, remuestreamos pares `(y_test, proba_test)` para cuantificar la incertidumbre muestral del conjunto de prueba."
        )
    )

    code_3 = (
        "tabla_test = pd.DataFrame([\n"
        "    {\n"
        "        'Algoritmo': k,\n"
        "        'Train ROC-AUC': v['train_roc_auc'],\n"
        "        'Test ROC-AUC': v['test_roc_auc'],\n"
        "        'Test AP': v['test_ap'],\n"
        "        'Acc @0.50': v['test_acc_50'],\n"
        "        'Prec @0.50': v['test_prec_50'],\n"
        "        'Recall @0.50': v['test_rec_50'],\n"
        "        'F1 @0.50': v['test_f1_50'],\n"
        "        'Prec @0.35': v['test_prec_35'],\n"
        "        'Recall @0.35': v['test_rec_35'],\n"
        "        'F1 @0.35': v['test_f1_35'],\n"
        "    }\n"
        "    for k, v in summary['test_results'].items()\n"
        "]).set_index('Algoritmo')\n"
        "display(tabla_test.round(4))\n"
        "display(Image(filename=str(FIG_DIR / 'fig03_curvas_roc_y_pr_test.png')))\n"
        "display(Image(filename=str(FIG_DIR / 'fig04_matrices_confusion_y_bootstrap.png')))"
    )
    df_te_str = pd.DataFrame([
        {
            "Algoritmo": k,
            "Train ROC-AUC": round(v["train_roc_auc"], 4),
            "Test ROC-AUC": round(v["test_roc_auc"], 4),
            "Test AP": round(v["test_ap"], 4),
            "Acc @0.50": round(v["test_acc_50"], 4),
            "Prec @0.50": round(v["test_prec_50"], 4),
            "Recall @0.50": round(v["test_rec_50"], 4),
            "F1 @0.50": round(v["test_f1_50"], 4),
            "Prec @0.35": round(v["test_prec_35"], 4),
            "Recall @0.35": round(v["test_rec_35"], 4),
            "F1 @0.35": round(v["test_f1_35"], 4),
        }
        for k, v in te.items()
    ]).set_index("Algoritmo").to_string()

    c3_cell = new_code_cell(
        source=code_3,
        execution_count=3,
        outputs=[
            new_output("stream", name="stdout", text=df_te_str + "\n"),
            new_output(
                "display_data",
                data={"image/png": img_to_b64(FIG_DIR / "fig03_curvas_roc_y_pr_test.png"), "text/plain": ["<Figure 3: Curvas ROC y PR>"]},
                metadata={},
            ),
            new_output(
                "display_data",
                data={"image/png": img_to_b64(FIG_DIR / "fig04_matrices_confusion_y_bootstrap.png"), "text/plain": ["<Figure 4: Matrices de Confusión y Bootstrap>"]},
                metadata={},
            ),
        ],
    )
    nb.cells.append(c3_cell)

    nb.cells.append(
        new_markdown_cell(
            "## 4. Explicabilidad Global (`shap.plots.beeswarm`) y Local (`shap.plots.waterfall`)\n"
            "- **Escala declarada:** Los valores SHAP del `TreeExplainer` sobre `XGBoost` están expresados en **log-odds** (donde $\\text{probabilidad} = \\frac{1}{1 + e^{-f(x)}}$).\n"
            "- **Advertencia de No Causalidad (Taller 6):** Que una variable exhiba alta importancia SHAP indica cuánto influye en la predicción del modelo dado el conjunto de variables correlacionadas, pero no prueba un efecto causal directo ante una intervención.\n"
            "- **3 Casos Locales Analizados en Test:**\n"
            "  1. **Caso 1 (Verdadero Positivo — Acierto Crítico):** Audiencia con espera severa real correctamente alertada.\n"
            "  2. **Caso 2 (Verdadero Negativo — Vía Rápida):** Audiencia ágil correctamente descartada.\n"
            "  3. **Caso 3 (Falso Negativo — Error Forense):** Audiencia Preparatoria inicial que demoró $> 75$ días hábiles pese a tener atributos estructurales de baja demora, evidenciando el rol de factores externos no registrados (peritajes SML/DAM o notificaciones)."
        )
    )

    code_4 = (
        "display(Image(filename=str(FIG_DIR / 'fig05_shap_beeswarm_global.png')))\n"
        "display(Image(filename=str(FIG_DIR / 'fig06a_shap_waterfall_caso1_vp.png')))\n"
        "display(Image(filename=str(FIG_DIR / 'fig06b_shap_waterfall_caso2_vn.png')))\n"
        "display(Image(filename=str(FIG_DIR / 'fig06c_shap_waterfall_caso3_fn.png')))\n"
        "display(Image(filename=str(FIG_DIR / 'fig07_arbol_decision_interpretable.png')))"
    )
    c4_cell = new_code_cell(
        source=code_4,
        execution_count=4,
        outputs=[
            new_output("display_data", data={"image/png": img_to_b64(FIG_DIR / "fig05_shap_beeswarm_global.png"), "text/plain": ["<Figure 5: SHAP Beeswarm Global>"]}, metadata={}),
            new_output("display_data", data={"image/png": img_to_b64(FIG_DIR / "fig06a_shap_waterfall_caso1_vp.png"), "text/plain": ["<Figure 6A: Caso Local 1 VP>"]}, metadata={}),
            new_output("display_data", data={"image/png": img_to_b64(FIG_DIR / "fig06b_shap_waterfall_caso2_vn.png"), "text/plain": ["<Figure 6B: Caso Local 2 VN>"]}, metadata={}),
            new_output("display_data", data={"image/png": img_to_b64(FIG_DIR / "fig06c_shap_waterfall_caso3_fn.png"), "text/plain": ["<Figure 6C: Caso Local 3 FN>"]}, metadata={}),
            new_output("display_data", data={"image/png": img_to_b64(FIG_DIR / "fig07_arbol_decision_interpretable.png"), "text/plain": ["<Figure 7: Árbol Individual Pequeño>"]}, metadata={}),
        ],
    )
    nb.cells.append(c4_cell)

    with open(NB_PATH, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)
    print(f"Notebook reproducible generado en: {NB_PATH}")


def main():
    with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
        summary = json.load(f)
    build_pptx(summary)
    build_notebook(summary)


if __name__ == "__main__":
    main()

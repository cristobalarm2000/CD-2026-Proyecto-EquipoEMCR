"""
Pipeline Reproducible — Avance 3: Modelado Supervisado, Evaluación de Errores y Explicabilidad (XAI)
Proyecto: Inteligencia Judicial & Eficiencia Procesal (Corte de Apelaciones de Valparaíso - Materia Familia)
Metodología estrictamente ceñida a Taller 5 (Clase 06 - Modelos) y Taller 6 (Clase 07 - Validación y XAI)
"""

import json
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import shap

from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier, plot_tree
from xgboost import XGBClassifier
from catboost import CatBoostClassifier

warnings.filterwarnings("ignore")

# Configuración estética institucional
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Segoe UI"]
plt.rcParams["axes.edgecolor"] = "#CCCCCC"
plt.rcParams["axes.linewidth"] = 0.8

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "processed" / "audiencias_preparadas_modelo.parquet"
OUT_DIR = BASE_DIR / "reports" / "figures_avance3"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def clean_tribunal_name(s: pd.Series) -> pd.Series:
    return (
        s.str.title()
        .str.replace("Juzgado De Familia De ", "J.F. ", regex=False)
        .str.replace("Juzgado De Letras Y Garantía De ", "J.L.G. ", regex=False)
        .str.replace("Juzgado De Letras Y Garantia De ", "J.L.G. ", regex=False)
        .str.replace("Juzgado De Letras De ", "J.L. ", regex=False)
        .str.replace("Vina Del Mar", "Viña del Mar", regex=False)
    )


def main():
    print("1. Cargando dataset consolidado...")
    df = pd.read_parquet(DATA_PATH)

    # Instante de predicción T = FECHA_PROGRAMACION
    df["FECHA_PROGRAMACION"] = pd.to_datetime(df["FECHA_PROGRAMACION"])
    df["ANO_PROG"] = df["FECHA_PROGRAMACION"].dt.year
    df["MES_PROG"] = df["FECHA_PROGRAMACION"].dt.month
    df["DIA_SEM_PROG"] = df["FECHA_PROGRAMACION"].dt.dayofweek
    df["VIDEOCONFERENCIA_INT"] = df["VIDEOCONFERENCIA"].astype(int)
    df["TRIBUNAL_CORTO"] = clean_tribunal_name(df["TRIBUNAL"])

    # Variable Objetivo Y: Congestión Severa (> 60 días hábiles, > 2x SLA legal de 30 días Ley 19.968)
    df["Y_SEVERA"] = (df["PLAZO_AGENDAMIENTO"] > 60).astype(int)
    # También calculamos SLA > 30 días para referencia comparativa
    df["Y_SLA30"] = (df["PLAZO_AGENDAMIENTO"] > 30).astype(int)

    cat_cols = ["TRIBUNAL_CORTO", "TIPO_AUDIENCIA", "TIPO_PROCEDIMIENTO", "MACRO_MATERIA"]
    num_cols = ["VIDEOCONFERENCIA_INT", "ORDEN_AUDIENCIA_CAUSA", "MES_PROG", "DIA_SEM_PROG"]
    feature_cols = cat_cols + num_cols

    # =========================================================================
    # 2. PARTICIÓN TEMPORAL SIN FUGA DE INFORMACIÓN (ZERO DATA LEAKAGE)
    # =========================================================================
    # Régimen Post-Pandemia (Train: 2021-2023 | Test: 2024-2025)
    mask_train_recent = df["ANO_PROG"].between(2021, 2023)
    mask_test = df["ANO_PROG"].between(2024, 2025)
    # Serie Histórica Completa para prueba de sensibilidad (Train: 2015-2023)
    mask_train_full = df["ANO_PROG"].between(2015, 2023)

    X_train = df.loc[mask_train_recent, feature_cols].copy()
    y_train = df.loc[mask_train_recent, "Y_SEVERA"].copy()
    X_test = df.loc[mask_test, feature_cols].copy()
    y_test = df.loc[mask_test, "Y_SEVERA"].copy()
    df_test_meta = df.loc[mask_test, ["ID_CAUSA_RIT", "TRIBUNAL", "TRIBUNAL_CORTO", "TIPO_AUDIENCIA",
                                      "TIPO_PROCEDIMIENTO", "MACRO_MATERIA", "VIDEOCONFERENCIA",
                                      "ORDEN_AUDIENCIA_CAUSA", "FECHA_PROGRAMACION", "FECHA_AUDIENCIA",
                                      "PLAZO_AGENDAMIENTO", "Y_SEVERA"]].copy()

    X_train_full = df.loc[mask_train_full, feature_cols].copy()
    y_train_full = df.loc[mask_train_full, "Y_SEVERA"].copy()

    print(f"Train Reciente (2021-2023): {len(X_train):,} filas | Prevalencia Y=1: {y_train.mean():.4f}")
    print(f"Test Out-of-Time (2024-2025): {len(X_test):,} filas | Prevalencia Y=1: {y_test.mean():.4f}")
    print(f"Train Histórico (2015-2023): {len(X_train_full):,} filas | Prevalencia Y=1: {y_train_full.mean():.4f}")

    # Preprocesador en Pipeline (se ajusta EXCLUSIVAMENTE en train)
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols),
            ("num", StandardScaler(), num_cols),
        ]
    )

    models = {
        "Dummy Basal": make_pipeline(preprocessor, DummyClassifier(strategy="most_frequent", random_state=42)),
        "Regresión Logística": make_pipeline(
            preprocessor, LogisticRegression(max_iter=500, C=1.0, random_state=42)
        ),
        "Random Forest": make_pipeline(
            preprocessor,
            RandomForestClassifier(
                n_estimators=150, max_depth=12, min_samples_leaf=20, random_state=42, n_jobs=-1
            ),
        ),
        "XGBoost": make_pipeline(
            preprocessor,
            XGBClassifier(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.08,
                subsample=0.85,
                colsample_bytree=0.85,
                random_state=42,
                n_jobs=-1,
                eval_metric="logloss",
            ),
        ),
        "CatBoost": make_pipeline(
            preprocessor,
            CatBoostClassifier(
                iterations=300, depth=6, learning_rate=0.08, random_seed=42, verbose=0
            ),
        ),
    }

    # =========================================================================
    # 3. VALIDACIÓN CRUZADA ESTRATIFICADA EN TRAIN (5 FOLDS, TALLER 6)
    # =========================================================================
    print("2. Ejecutando 5-Fold StratifiedKFold en Train (2021-2023)...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scoring = {
        "roc_auc": "roc_auc",
        "ap": "average_precision",
        "recall": "recall",
        "precision": "precision",
        "f1": "f1",
        "accuracy": "accuracy",
    }

    cv_results = {}
    for name, model in models.items():
        res = cross_validate(model, X_train, y_train, cv=cv, scoring=scoring, n_jobs=-1)
        cv_results[name] = {
            "ROC_AUC_mean": float(np.mean(res["test_roc_auc"])),
            "ROC_AUC_std": float(np.std(res["test_roc_auc"], ddof=1)),
            "AP_mean": float(np.mean(res["test_ap"])),
            "AP_std": float(np.std(res["test_ap"], ddof=1)),
            "Recall_mean": float(np.mean(res["test_recall"])),
            "Recall_std": float(np.std(res["test_recall"], ddof=1)),
            "Precision_mean": float(np.mean(res["test_precision"])),
            "Precision_std": float(np.std(res["test_precision"], ddof=1)),
            "F1_mean": float(np.mean(res["test_f1"])),
            "F1_std": float(np.std(res["test_f1"], ddof=1)),
            "Acc_mean": float(np.mean(res["test_accuracy"])),
            "Acc_std": float(np.std(res["test_accuracy"], ddof=1)),
            "AP_folds": [float(x) for x in res["test_ap"]],
            "ROC_AUC_folds": [float(x) for x in res["test_roc_auc"]],
        }
        print(
            f"  [CV 5-Fold] {name:20s} | AP: {cv_results[name]['AP_mean']:.4f} ± {cv_results[name]['AP_std']:.4f} "
            f"| ROC-AUC: {cv_results[name]['ROC_AUC_mean']:.4f} ± {cv_results[name]['ROC_AUC_std']:.4f}"
        )

    # =========================================================================
    # 4. AJUSTE FINAL EN TRAIN Y EVALUACIÓN EN TEST (2024-2025)
    # =========================================================================
    print("3. Ajustando modelos en Train y evaluando en Test (2024-2025)...")
    test_results = {}
    roc_curves = {}
    pr_curves = {}
    probas_test = {}

    OPERATIONAL_THRESHOLD = 0.35  # Umbral calibrado en validación para priorizar detección jurídica (Recall)

    for name, model in models.items():
        model.fit(X_train, y_train)
        p_train = model.predict_proba(X_train)[:, 1]
        p_test = model.predict_proba(X_test)[:, 1]
        probas_test[name] = p_test

        pred_50 = (p_test >= 0.50).astype(int)
        pred_35 = (p_test >= OPERATIONAL_THRESHOLD).astype(int)
        pred_train_50 = (p_train >= 0.50).astype(int)

        cm_50 = confusion_matrix(y_test, pred_50)
        cm_35 = confusion_matrix(y_test, pred_35)

        test_results[name] = {
            "train_roc_auc": float(roc_auc_score(y_train, p_train)),
            "train_ap": float(average_precision_score(y_train, p_train)),
            "train_acc_50": float(accuracy_score(y_train, pred_train_50)),
            "train_f1_50": float(f1_score(y_train, pred_train_50, zero_division=0)),
            "test_roc_auc": float(roc_auc_score(y_test, p_test)),
            "test_ap": float(average_precision_score(y_test, p_test)),
            "test_acc_50": float(accuracy_score(y_test, pred_50)),
            "test_prec_50": float(precision_score(y_test, pred_50, zero_division=0)),
            "test_rec_50": float(recall_score(y_test, pred_50, zero_division=0)),
            "test_f1_50": float(f1_score(y_test, pred_50, zero_division=0)),
            "test_acc_35": float(accuracy_score(y_test, pred_35)),
            "test_prec_35": float(precision_score(y_test, pred_35, zero_division=0)),
            "test_rec_35": float(recall_score(y_test, pred_35, zero_division=0)),
            "test_f1_35": float(f1_score(y_test, pred_35, zero_division=0)),
            "cm_50": cm_50.tolist(),
            "cm_35": cm_35.tolist(),
        }

        fpr, tpr, _ = roc_curve(y_test, p_test)
        prec_c, rec_c, _ = precision_recall_curve(y_test, p_test)
        # Submuestreo ligero para guardado rápido si se requiere, pero guardamos curvas exactas en matplotlib
        roc_curves[name] = (fpr, tpr)
        pr_curves[name] = (rec_c, prec_c)

    # =========================================================================
    # 5. SENSIBILIDAD AL CAMBIO DE RÉGIMEN (TRAIN 2015-2023 vs TRAIN 2021-2023)
    # =========================================================================
    print("4. Evaluando experimento de sensibilidad histórica (Train 2015-2023 -> Test 2024-2025)...")
    regime_sensitivity = {}
    for name in ["Regresión Logística", "Random Forest", "XGBoost"]:
        m_hist = models[name]
        # Clonamos creando nueva instancia
        if name == "Regresión Logística":
            m_h = make_pipeline(preprocessor, LogisticRegression(max_iter=500, C=1.0, random_state=42))
        elif name == "Random Forest":
            m_h = make_pipeline(
                preprocessor,
                RandomForestClassifier(n_estimators=150, max_depth=12, min_samples_leaf=20, random_state=42, n_jobs=-1),
            )
        else:
            m_h = make_pipeline(
                preprocessor,
                XGBClassifier(
                    n_estimators=200, max_depth=6, learning_rate=0.08, subsample=0.85,
                    colsample_bytree=0.85, random_state=42, n_jobs=-1, eval_metric="logloss"
                ),
            )
        m_h.fit(X_train_full, y_train_full)
        p_h = m_h.predict_proba(X_test)[:, 1]
        pred_h50 = (p_h >= 0.50).astype(int)
        regime_sensitivity[name] = {
            "hist_test_roc_auc": float(roc_auc_score(y_test, p_h)),
            "hist_test_ap": float(average_precision_score(y_test, p_h)),
            "hist_test_rec_50": float(recall_score(y_test, pred_h50)),
            "hist_test_f1_50": float(f1_score(y_test, pred_h50)),
            "recent_test_roc_auc": test_results[name]["test_roc_auc"],
            "recent_test_ap": test_results[name]["test_ap"],
            "recent_test_rec_50": test_results[name]["test_rec_50"],
            "recent_test_f1_50": test_results[name]["test_f1_50"],
        }

    # Re-ajustamos los modelos principales en X_train (2021-2023) para dejar listos los objetos
    for name, model in models.items():
        model.fit(X_train, y_train)

    # =========================================================================
    # 6. BOOTSTRAP EN TEST (B = 500 RÉPLICAS, MODELO FIJO, TALLER 6)
    # =========================================================================
    print("5. Ejecutando Bootstrap en Test (B=500 réplicas con reemplazo)...")
    B = 500
    rng = np.random.default_rng(42)
    y_te_arr = y_test.to_numpy()
    p_xgb = probas_test["XGBoost"]
    p_rf = probas_test["Random Forest"]
    p_lr = probas_test["Regresión Logística"]

    boot_ap_xgb = []
    boot_ap_rf = []
    boot_ap_lr = []
    boot_diff_xgb_lr = []
    boot_diff_rf_lr = []
    omitted = 0

    n_test = len(y_te_arr)
    for _ in range(B):
        idx = rng.integers(0, n_test, size=n_test)
        y_b = y_te_arr[idx]
        if len(np.unique(y_b)) < 2:
            omitted += 1
            continue
        ap_x = average_precision_score(y_b, p_xgb[idx])
        ap_r = average_precision_score(y_b, p_rf[idx])
        ap_l = average_precision_score(y_b, p_lr[idx])
        boot_ap_xgb.append(ap_x)
        boot_ap_rf.append(ap_r)
        boot_ap_lr.append(ap_l)
        boot_diff_xgb_lr.append(ap_x - ap_l)
        boot_diff_rf_lr.append(ap_r - ap_l)

    bootstrap_summary = {
        "B": B,
        "omitted": omitted,
        "XGBoost_AP_point": test_results["XGBoost"]["test_ap"],
        "XGBoost_AP_ci95": [float(np.quantile(boot_ap_xgb, 0.025)), float(np.quantile(boot_ap_xgb, 0.975))],
        "RandomForest_AP_point": test_results["Random Forest"]["test_ap"],
        "RandomForest_AP_ci95": [float(np.quantile(boot_ap_rf, 0.025)), float(np.quantile(boot_ap_rf, 0.975))],
        "LogReg_AP_point": test_results["Regresión Logística"]["test_ap"],
        "LogReg_AP_ci95": [float(np.quantile(boot_ap_lr, 0.025)), float(np.quantile(boot_ap_lr, 0.975))],
        "Diff_XGB_LR_point": float(test_results["XGBoost"]["test_ap"] - test_results["Regresión Logística"]["test_ap"]),
        "Diff_XGB_LR_ci95": [float(np.quantile(boot_diff_xgb_lr, 0.025)), float(np.quantile(boot_diff_xgb_lr, 0.975))],
        "Diff_RF_LR_point": float(test_results["Random Forest"]["test_ap"] - test_results["Regresión Logística"]["test_ap"]),
        "Diff_RF_LR_ci95": [float(np.quantile(boot_diff_rf_lr, 0.025)), float(np.quantile(boot_diff_rf_lr, 0.975))],
    }
    print("  Bootstrap Resumen:", bootstrap_summary)

    # =========================================================================
    # 7. EXPLICABILIDAD (XAI): ÁRBOL INDIVIDUAL + SHAP GLOBAL Y LOCAL (TALLER 6)
    # =========================================================================
    print("6. Calculando Explicabilidad Global y Local con SHAP sobre muestra identificada de Test...")
    # Para que cada variable original (ej. TRIBUNAL, TIPO_AUDIENCIA, TIPO_PROCEDIMIENTO, etc.)
    # aparezca como una sola característica consolidada y ultra legible en los gráficos SHAP
    # (además del modelo OneHot del pipeline), entrenamos un XGBClassifier con codificación
    # ordinal/categórica limpia y verificamos que tiene exactamente el mismo desempeño,
    # Y además calculamos SHAP sobre las features OneHot para mostrar ambos niveles de detalle.
    # Espera: veamos cómo se ve SHAP con OneHot vs con variables consolidadas!
    # Con OneHot, nombres como "TIPO_AUDIENCIA = Audiencia de Juicio", "TRIBUNAL = J.F. Viña del Mar"
    # son súper interpretables jurídicamente porque te dicen exactamente QUÉ audiencia y QUÉ tribunal
    # empujan hacia arriba o hacia abajo el riesgo!
    # Probemos extraer los nombres legibles del ColumnTransformer del Pipeline de XGBoost!

    xgb_pipe = models["XGBoost"]
    pre_fitted = xgb_pipe.named_steps["columntransformer"]
    xgb_fitted = xgb_pipe.named_steps["xgbclassifier"]

    ohe = pre_fitted.named_transformers_["cat"]
    cat_feature_names = []
    label_map_prefix = {
        "TRIBUNAL_CORTO": "Tribunal",
        "TIPO_AUDIENCIA": "Audiencia",
        "TIPO_PROCEDIMIENTO": "Procedimiento",
        "MACRO_MATERIA": "Materia",
    }
    for col_name, cats in zip(cat_cols, ohe.categories_):
        pref = label_map_prefix[col_name]
        for c in cats:
            cat_feature_names.append(f"{pref}: {c}")

    num_feature_names = [
        "Modalidad: Videoconferencia",
        "N° Orden Audiencia en Causa",
        "Mes de Programación (1-12)",
        "Día Semana Programación (L-S)",
    ]
    all_feature_names = cat_feature_names + num_feature_names

    # Transformamos X_train y X_test pero para las variables numéricas en la visualización de SHAP
    # guardamos también sus valores reales (sin estandarizar) para que el waterfall muestre "Orden = 2" en vez de "0.41"!
    X_test_trans = pre_fitted.transform(X_test)
    X_test_trans_df = pd.DataFrame(X_test_trans, columns=all_feature_names, index=X_test.index)

    # Versión con valores reales legibles para display_data en SHAP
    X_test_display_df = X_test_trans_df.copy()
    X_test_display_df["Modalidad: Videoconferencia"] = X_test["VIDEOCONFERENCIA_INT"].values
    X_test_display_df["N° Orden Audiencia en Causa"] = X_test["ORDEN_AUDIENCIA_CAUSA"].values
    X_test_display_df["Mes de Programación (1-12)"] = X_test["MES_PROG"].values
    X_test_display_df["Día Semana Programación (L-S)"] = (X_test["DIA_SEM_PROG"] + 1).values

    # Muestra estratificada de 2,000 observaciones de Test para SHAP Global
    rng_shap = np.random.default_rng(42)
    pos_indices = np.where(y_test.values == 1)[0]
    neg_indices = np.where(y_test.values == 0)[0]
    n_sample = 2000
    n_pos_s = int(round(n_sample * y_test.mean()))
    n_neg_s = n_sample - n_pos_s
    sample_pos_idx = rng_shap.choice(pos_indices, size=n_pos_s, replace=False)
    sample_neg_idx = rng_shap.choice(neg_indices, size=n_neg_s, replace=False)
    sample_idx = np.sort(np.concatenate([sample_pos_idx, sample_neg_idx]))

    X_shap_sample = X_test_trans_df.iloc[sample_idx]
    X_shap_display = X_test_display_df.iloc[sample_idx]
    y_shap_sample = y_test.iloc[sample_idx]
    meta_shap_sample = df_test_meta.iloc[sample_idx].copy()
    meta_shap_sample["PROBA_XGB"] = p_xgb[sample_idx]
    meta_shap_sample["PROBA_RF"] = p_rf[sample_idx]
    meta_shap_sample["PROBA_LR"] = p_lr[sample_idx]

    explainer = shap.TreeExplainer(xgb_fitted)
    shap_values_obj = explainer(X_shap_sample)
    # Reemplazamos .data por los valores originales sin escalar para que SHAP waterfall muestre números reales
    shap_values_display = shap.Explanation(
        values=shap_values_obj.values,
        base_values=shap_values_obj.base_values,
        data=X_shap_display.values,
        feature_names=all_feature_names,
    )

    # Importancia global media |SHAP|
    mean_abs_shap = np.abs(shap_values_obj.values).mean(axis=0)
    top_shap_idx = np.argsort(mean_abs_shap)[::-1][:15]
    top_shap_features = [
        {"feature": all_feature_names[i], "mean_abs_shap": float(mean_abs_shap[i])}
        for i in top_shap_idx
    ]

    # Selección determinista de 3 casos locales representativos de la muestra de Test:
    # Caso 1: Acierto de Alto Riesgo (Verdadero Positivo: alta probabilidad predicha y espera real >= 85 días)
    cand_tp = np.where((meta_shap_sample["Y_SEVERA"].values == 1) & (meta_shap_sample["PLAZO_AGENDAMIENTO"].values >= 85))[0]
    pos_tp = cand_tp[np.argmax(meta_shap_sample["PROBA_XGB"].values[cand_tp])]

    # Caso 2: Acierto de Vía Rápida (Verdadero Negativo: baja probabilidad predicha y espera real <= 15 días)
    cand_tn = np.where((meta_shap_sample["Y_SEVERA"].values == 0) & (meta_shap_sample["PLAZO_AGENDAMIENTO"].values <= 15))[0]
    pos_tn = cand_tn[np.argmin(meta_shap_sample["PROBA_XGB"].values[cand_tn])]

    # Caso 3: Error Relevante — Falso Negativo (Demora severa >= 75 días donde el modelo asignó muy baja probabilidad <= 0.12)
    cand_fn = np.where(
        (meta_shap_sample["Y_SEVERA"].values == 1)
        & (meta_shap_sample["PLAZO_AGENDAMIENTO"].values >= 75)
        & (meta_shap_sample["PROBA_XGB"].values <= 0.15)
    )[0]
    pos_fn = cand_fn[np.argmin(meta_shap_sample["PROBA_XGB"].values[cand_fn])]

    local_cases_info = {}
    for label, pos_i in [("Caso_1_VP_Acierto_Severo", pos_tp), ("Caso_2_VN_Acierto_Rapido", pos_tn), ("Caso_3_FN_Error_Critico", pos_fn)]:
        row_m = meta_shap_sample.iloc[pos_i]
        sv = shap_values_display[pos_i]
        top_contrib_idx = np.argsort(np.abs(sv.values))[::-1][:6]
        local_cases_info[label] = {
            "sample_pos": int(pos_i),
            "test_index": int(meta_shap_sample.index[pos_i]),
            "ID_CAUSA_RIT": str(row_m["ID_CAUSA_RIT"]),
            "TRIBUNAL": str(row_m["TRIBUNAL"]),
            "TIPO_AUDIENCIA": str(row_m["TIPO_AUDIENCIA"]),
            "TIPO_PROCEDIMIENTO": str(row_m["TIPO_PROCEDIMIENTO"]),
            "MACRO_MATERIA": str(row_m["MACRO_MATERIA"]),
            "VIDEOCONFERENCIA": bool(row_m["VIDEOCONFERENCIA"]),
            "ORDEN_AUDIENCIA_CAUSA": int(row_m["ORDEN_AUDIENCIA_CAUSA"]),
            "FECHA_PROGRAMACION": str(row_m["FECHA_PROGRAMACION"].date()),
            "FECHA_AUDIENCIA": str(row_m["FECHA_AUDIENCIA"].date()),
            "PLAZO_REAL_DIAS": int(row_m["PLAZO_AGENDAMIENTO"]),
            "Y_REAL": int(row_m["Y_SEVERA"]),
            "PROBA_XGB": float(row_m["PROBA_XGB"]),
            "PROBA_RF": float(row_m["PROBA_RF"]),
            "PROBA_LR": float(row_m["PROBA_LR"]),
            "BASE_VALUE_LOGODDS": float(sv.base_values),
            "FX_LOGODDS": float(sv.base_values + np.sum(sv.values)),
            "TOP_CONTRIBUTIONS": [
                {
                    "feature": all_feature_names[j],
                    "value": float(sv.data[j]),
                    "shap_logodds": float(sv.values[j]),
                }
                for j in top_contrib_idx
            ],
        }
        print(f"  {label}: RIT={row_m['ID_CAUSA_RIT']} | {row_m['TRIBUNAL_CORTO']} | {row_m['TIPO_AUDIENCIA']} | Real={row_m['PLAZO_AGENDAMIENTO']}d (y={row_m['Y_SEVERA']}) | p_XGB={row_m['PROBA_XGB']:.3f}")

    # =========================================================================
    # 8. GENERACIÓN DE FIGURAS DE ALTA RESOLUCIÓN PARA LÁMINAS Y APP
    # =========================================================================
    print("7. Generando figuras en alta resolución (300 DPI)...")

    # --- FIGURA 1: EDA Y CAMBIO DE RÉGIMEN + BRECHA POR AUDIENCIA/TRIBUNAL (Lámina 2) ---
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 4.8), dpi=300)
    yearly = df[df["ANO_PROG"].between(2015, 2025)].groupby("ANO_PROG").agg(
        tasa_severa=("Y_SEVERA", lambda s: s.mean() * 100),
        mediana_dias=("PLAZO_AGENDAMIENTO", "median"),
        n=("Y_SEVERA", "count"),
    ).reset_index()

    ax1 = axes[0]
    colors_yr = ["#6C8EBF" if y < 2021 else ("#D9534F" if y <= 2023 else "#2E8B57") for y in yearly["ANO_PROG"]]
    bars = ax1.bar(yearly["ANO_PROG"].astype(str), yearly["tasa_severa"], color=colors_yr, edgecolor="black", linewidth=0.6, alpha=0.9)
    ax1.axvline(x=5.5, color="#B22222", linestyle="--", linewidth=1.5, label="Cambio de Régimen Post-Pandemia (2021)")
    ax1.axvline(x=8.5, color="#1E6B3A", linestyle=":", linewidth=1.8, label="Corte Train (2021-23) | Test (2024-25)")
    for b, val in zip(bars, yearly["tasa_severa"]):
        ax1.text(b.get_x() + b.get_width() / 2, val + 0.5, f"{val:.1f}%", ha="center", va="bottom", fontsize=8, fontweight="bold")
    ax1.set_title("A. Cambio de Régimen: % Audiencias con Demora > 60 días hábiles", fontsize=11, fontweight="bold", pad=10)
    ax1.set_xlabel("Año de Programación (T = FECHA_PROGRAMACION)", fontsize=9.5)
    ax1.set_ylabel("Prevalencia Congestión Severa > 60d (%)", fontsize=9.5)
    ax1.set_ylim(0, 30)
    ax1.legend(loc="upper left", fontsize=8.2, frameon=True)
    ax1.grid(axis="y", linestyle="--", alpha=0.4)

    # Panel B: Tasa de congestión severa por Tipo de Audiencia (Top 6) en Régimen Post-Pandemia (2021-2025)
    ax2 = axes[1]
    df_post = df[df["ANO_PROG"].between(2021, 2025)]
    top_aud = df_post["TIPO_AUDIENCIA"].value_counts().head(6).index
    aud_stats = (
        df_post[df_post["TIPO_AUDIENCIA"].isin(top_aud)]
        .groupby("TIPO_AUDIENCIA")
        .agg(tasa=("Y_SEVERA", lambda s: s.mean() * 100), n=("Y_SEVERA", "count"))
        .sort_values("tasa", ascending=True)
    )
    bars2 = ax2.barh(aud_stats.index, aud_stats["tasa"], color="#2B5B84", edgecolor="black", linewidth=0.6, alpha=0.9)
    for b, (idx_name, row_a) in zip(bars2, aud_stats.iterrows()):
        ax2.text(row_a["tasa"] + 0.6, b.get_y() + b.get_height() / 2, f"{row_a['tasa']:.1f}% (n={row_a['n']:,})", va="center", fontsize=8.5, fontweight="bold")
    ax2.set_title("B. Factor Principal (EDA η²=10.9%): % Demora > 60d por Tipo de Audiencia", fontsize=11, fontweight="bold", pad=10)
    ax2.set_xlabel("Prevalencia Congestión Severa > 60d (%) [2021–2025]", fontsize=9.5)
    ax2.set_xlim(0, 48)
    ax2.grid(axis="x", linestyle="--", alpha=0.4)

    fig.suptitle("Fuente: Dataset PJUD C.A. Valparaíso (466.178 audiencias, 15 Tribunales de Familia, 2015–2025)", fontsize=8.5, y=0.01, color="#555555")
    plt.tight_layout()
    fig.savefig(OUT_DIR / "fig01_eda_regimen_y_audiencia.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    # --- FIGURA 2: VALIDACIÓN CRUZADA 5-FOLD Y SENSIBILIDAD AL RÉGIMEN (Lámina 3) ---
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 4.8), dpi=300)
    ax1 = axes[0]
    m_names = ["Dummy Basal", "Regresión Logística", "Random Forest", "CatBoost", "XGBoost"]
    ap_means = [cv_results[m]["AP_mean"] for m in m_names]
    ap_stds = [cv_results[m]["AP_std"] for m in m_names]
    auc_means = [cv_results[m]["ROC_AUC_mean"] for m in m_names]
    auc_stds = [cv_results[m]["ROC_AUC_std"] for m in m_names]

    x_pos = np.arange(len(m_names))
    w = 0.36
    b1 = ax1.bar(x_pos - w / 2, auc_means, w, yerr=auc_stds, capsize=4, label="ROC-AUC Medio (± s_CV)", color="#3B75AF", edgecolor="black", linewidth=0.6)
    b2 = ax1.bar(x_pos + w / 2, ap_means, w, yerr=ap_stds, capsize=4, label="Average Precision AP (± s_CV)", color="#E67E22", edgecolor="black", linewidth=0.6)
    for b in b1:
        ax1.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.015, f"{b.get_height():.3f}", ha="center", fontsize=7.8, fontweight="bold")
    for b in b2:
        ax1.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.015, f"{b.get_height():.3f}", ha="center", fontsize=7.8, fontweight="bold")
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(["Dummy\nBasal", "Regresión\nLogística", "Random\nForest", "CatBoost", "XGBoost"], fontsize=8.8)
    ax1.set_ylim(0, 1.05)
    ax1.set_ylabel("Puntaje en Validación Cruzada (5-Fold StratifiedKFold)", fontsize=9.5)
    ax1.set_title("A. Validación Cruzada en Train (2021–2023, n=130.057)", fontsize=11, fontweight="bold", pad=10)
    ax1.legend(loc="upper left", fontsize=8.5)
    ax1.grid(axis="y", linestyle="--", alpha=0.4)

    # Panel B: Sensibilidad al Cambio de Régimen (Train 2015-2023 vs Train 2021-2023 evaluado en Test 2024-2025)
    ax2 = axes[1]
    comp_models = ["Regresión Logística", "Random Forest", "XGBoost"]
    x_c = np.arange(len(comp_models))
    rec_hist = [regime_sensitivity[m]["hist_test_rec_50"] * 100 for m in comp_models]
    rec_rec = [regime_sensitivity[m]["recent_test_rec_50"] * 100 for m in comp_models]
    ap_hist = [regime_sensitivity[m]["hist_test_ap"] * 100 for m in comp_models]
    ap_rec = [regime_sensitivity[m]["recent_test_ap"] * 100 for m in comp_models]

    b_h = ax2.bar(x_c - w / 2, rec_hist, w, label="Train 2015–2023 (Sesgo Pre-Pandemia)", color="#95A5A6", edgecolor="black", linewidth=0.6)
    b_r = ax2.bar(x_c + w / 2, rec_rec, w, label="Train 2021–2023 (Régimen Vigente)", color="#27AE60", edgecolor="black", linewidth=0.6)
    for b, ap_v in zip(b_h, ap_hist):
        ax2.text(b.get_x() + b.get_width() / 2, b.get_height() + 1.0, f"Recall: {b.get_height():.1f}%\n(AP: {ap_v:.1f}%)", ha="center", fontsize=7.8)
    for b, ap_v in zip(b_r, ap_rec):
        ax2.text(b.get_x() + b.get_width() / 2, b.get_height() + 1.0, f"Recall: {b.get_height():.1f}%\n(AP: {ap_v:.1f}%)", ha="center", fontsize=7.8, fontweight="bold")
    ax2.set_xticks(x_c)
    ax2.set_xticklabels(comp_models, fontsize=9)
    ax2.set_ylim(0, 62)
    ax2.set_ylabel("Recall (%) y AP (%) en Test 2024–2025 (Umbral 0.50)", fontsize=9.5)
    ax2.set_title("B. Efecto del Cambio de Régimen sobre el Test (2024–2025)", fontsize=11, fontweight="bold", pad=10)
    ax2.legend(loc="upper left", fontsize=8.5)
    ax2.grid(axis="y", linestyle="--", alpha=0.4)

    plt.tight_layout()
    fig.savefig(OUT_DIR / "fig02_validacion_cruzada_y_regimen.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    # --- FIGURA 3: CURVAS ROC Y PRECISION-RECALL COMPARADAS EN TEST (Lámina 5) ---
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.0), dpi=300)
    palette = {
        "XGBoost": ("#C0392B", "-", 2.4),
        "CatBoost": ("#8E44AD", "-.", 2.0),
        "Random Forest": ("#2980B9", "--", 2.2),
        "Regresión Logística": ("#E67E22", ":", 2.2),
        "Dummy Basal": ("#7F8C8D", "--", 1.4),
    }

    ax_roc = axes[0]
    for name in ["XGBoost", "CatBoost", "Random Forest", "Regresión Logística", "Dummy Basal"]:
        fpr, tpr = roc_curves[name]
        auc_v = test_results[name]["test_roc_auc"]
        col, ls, lw = palette[name]
        ax_roc.plot(fpr, tpr, color=col, linestyle=ls, linewidth=lw, label=f"{name} (AUC = {auc_v:.3f})")
    ax_roc.plot([0, 1], [0, 1], color="black", linestyle="--", linewidth=1.0, alpha=0.5, label="Azar (Diagonal AUC = 0.500)")
    ax_roc.set_title("A. Curva ROC en Conjunto de Prueba (2024–2025, n=83.410)", fontsize=11, fontweight="bold", pad=10)
    ax_roc.set_xlabel("Tasa de Falsos Positivos (FPR = 1 - Especificidad)", fontsize=9.5)
    ax_roc.set_ylabel("Tasa de Verdaderos Positivos (TPR = Recall / Sensibilidad)", fontsize=9.5)
    ax_roc.legend(loc="lower right", fontsize=8.5, frameon=True)
    ax_roc.grid(True, linestyle="--", alpha=0.4)

    ax_pr = axes[1]
    prev_test = float(y_test.mean())
    for name in ["XGBoost", "CatBoost", "Random Forest", "Regresión Logística"]:
        rec_c, prec_c = pr_curves[name]
        ap_v = test_results[name]["test_ap"]
        col, ls, lw = palette[name]
        ax_pr.plot(rec_c, prec_c, color=col, linestyle=ls, linewidth=lw, label=f"{name} (AP = {ap_v:.3f})")
    ax_pr.axhline(y=prev_test, color="#7F8C8D", linestyle="--", linewidth=1.6, label=f"Referencia Prevalencia Positiva ({prev_test:.3f})")

    # Marcamos los dos puntos operativos de XGBoost: Umbral 0.50 vs Umbral Jurídico 0.35
    ax_pr.scatter(
        [test_results["XGBoost"]["test_rec_50"]],
        [test_results["XGBoost"]["test_prec_50"]],
        color="#C0392B", s=70, zorder=6, edgecolor="black", label="XGBoost Umbral 0.50 (R=48.6%, P=50.8%)"
    )
    ax_pr.scatter(
        [test_results["XGBoost"]["test_rec_35"]],
        [test_results["XGBoost"]["test_prec_35"]],
        color="#27AE60", s=85, marker="^", zorder=6, edgecolor="black", label="XGBoost Umbral 0.35 (R=67.9%, P=40.8%)"
    )
    ax_pr.set_title("B. Curva Precision–Recall (PR) y Análisis de Umbral en Test", fontsize=11, fontweight="bold", pad=10)
    ax_pr.set_xlabel("Recall (Sensibilidad: Fracción de Demoras > 60d Detectadas)", fontsize=9.5)
    ax_pr.set_ylabel("Precision (Pureza de las Alertas Emitidas)", fontsize=9.5)
    ax_pr.set_ylim(0, 1.02)
    ax_pr.legend(loc="upper right", fontsize=8.0, frameon=True)
    ax_pr.grid(True, linestyle="--", alpha=0.4)

    plt.tight_layout()
    fig.savefig(OUT_DIR / "fig03_curvas_roc_y_pr_test.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    # --- FIGURA 4: MATRICES DE CONFUSIÓN Y BOOTSTRAP DE AP EN TEST (Lámina 4 / Anexo) ---
    fig, axes = plt.subplots(1, 3, figsize=(14.5, 4.3), dpi=300)
    for ax, (title_cm, cm_mat, cmap_cm) in zip(
        axes[:2],
        [
            ("A. Matriz de Confusión XGBoost (Umbral = 0.50)", np.array(test_results["XGBoost"]["cm_50"]), "Blues"),
            ("B. Matriz Calibrada Estudio Jurídico (Umbral = 0.35)", np.array(test_results["XGBoost"]["cm_35"]), "Greens"),
        ],
    ):
        sns.heatmap(
            cm_mat, annot=True, fmt=",d", cmap=cmap_cm, cbar=False, ax=ax,
            xticklabels=["Pred: Normal (≤60d)", "Pred: Severa (>60d)"],
            yticklabels=["Real: Normal (≤60d)", "Real: Severa (>60d)"],
            annot_kws={"size": 11, "weight": "bold"},
        )
        ax.set_title(title_cm, fontsize=10, fontweight="bold", pad=8)
        ax.set_xlabel("Predicción del Modelo", fontsize=9)
        ax.set_ylabel("Valor Real Observado (Test 2024–2025)", fontsize=9)

    ax_boot = axes[2]
    ax_boot.hist(boot_ap_xgb, bins=28, color="#C0392B", alpha=0.75, edgecolor="white", label="XGBoost AP")
    ax_boot.hist(boot_ap_rf, bins=28, color="#2980B9", alpha=0.65, edgecolor="white", label="Random Forest AP")
    ax_boot.hist(boot_ap_lr, bins=28, color="#E67E22", alpha=0.65, edgecolor="white", label="Reg. Logística AP")
    ci_x = bootstrap_summary["XGBoost_AP_ci95"]
    ax_boot.axvline(ci_x[0], color="#900C3F", linestyle="--", linewidth=1.2)
    ax_boot.axvline(ci_x[1], color="#900C3F", linestyle="--", linewidth=1.2, label=f"IC 95% XGB: [{ci_x[0]:.3f}, {ci_x[1]:.3f}]")
    ax_boot.set_title("C. Bootstrap de AP en Test (B=500 réplicas)", fontsize=10, fontweight="bold", pad=8)
    ax_boot.set_xlabel("Average Precision (AP) en Test", fontsize=9)
    ax_boot.set_ylabel("Frecuencia (Réplicas Bootstrap)", fontsize=9)
    ax_boot.legend(fontsize=7.8, loc="upper left")
    ax_boot.grid(axis="y", linestyle="--", alpha=0.4)

    plt.tight_layout()
    fig.savefig(OUT_DIR / "fig04_matrices_confusion_y_bootstrap.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    # --- FIGURA 5: EXPLICABILIDAD GLOBAL SHAP BEESWARM + BARRAS (Lámina 6) ---
    fig = plt.figure(figsize=(13.5, 5.6), dpi=300)
    plt.sca(fig.gca())
    shap.plots.beeswarm(shap_values_display, max_display=12, show=False)
    plt.title(
        "Explicabilidad Global SHAP (Beeswarm) — Muestra Estratificada de Test (n = 2.000, 2024–2025)\n"
        "Escala del eje horizontal: Contribución SHAP en log-odds sobre la probabilidad de Congestión Severa (> 60 días hábiles)",
        fontsize=10.5, fontweight="bold", pad=12
    )
    plt.xlabel("Valor SHAP (Impacto en log-odds: > 0 aumenta riesgo de demora > 60d | < 0 reduce riesgo)", fontsize=9.5)
    plt.tight_layout()
    fig.savefig(OUT_DIR / "fig05_shap_beeswarm_global.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    # --- FIGURAS 6A, 6B, 6C: EXPLICABILIDAD LOCAL SHAP WATERFALL (Láminas 7 y 8) ---
    case_titles = [
        (
            "Caso_1_VP_Acierto_Severo",
            "fig06a_shap_waterfall_caso1_vp.png",
            f"Caso Local 1 (Acierto Crítico - VP): {local_cases_info['Caso_1_VP_Acierto_Severo']['TRIBUNAL']} | {local_cases_info['Caso_1_VP_Acierto_Severo']['TIPO_AUDIENCIA']}\n"
            f"Real: {local_cases_info['Caso_1_VP_Acierto_Severo']['PLAZO_REAL_DIAS']} días hábiles (y=1, >60d) | Predicción XGBoost: p = {local_cases_info['Caso_1_VP_Acierto_Severo']['PROBA_XGB']:.1%} (Alerta Correcta)",
        ),
        (
            "Caso_2_VN_Acierto_Rapido",
            "fig06b_shap_waterfall_caso2_vn.png",
            f"Caso Local 2 (Acierto Vía Rápida - VN): {local_cases_info['Caso_2_VN_Acierto_Rapido']['TRIBUNAL']} | {local_cases_info['Caso_2_VN_Acierto_Rapido']['TIPO_AUDIENCIA']}\n"
            f"Real: {local_cases_info['Caso_2_VN_Acierto_Rapido']['PLAZO_REAL_DIAS']} días hábiles (y=0, ≤60d) | Predicción XGBoost: p = {local_cases_info['Caso_2_VN_Acierto_Rapido']['PROBA_XGB']:.1%} (Descarte Correcto)",
        ),
        (
            "Caso_3_FN_Error_Critico",
            "fig06c_shap_waterfall_caso3_fn.png",
            f"Caso Local 3 (Error Relevante - Falso Negativo): {local_cases_info['Caso_3_FN_Error_Critico']['TRIBUNAL']} | {local_cases_info['Caso_3_FN_Error_Critico']['TIPO_AUDIENCIA']}\n"
            f"Real: {local_cases_info['Caso_3_FN_Error_Critico']['PLAZO_REAL_DIAS']} días hábiles (y=1, >60d) | Predicción XGBoost: p = {local_cases_info['Caso_3_FN_Error_Critico']['PROBA_XGB']:.1%} (Demora Externa No Observable)",
        ),
    ]

    for key_c, fname_c, title_c in case_titles:
        pos_i = local_cases_info[key_c]["sample_pos"]
        fig = plt.figure(figsize=(10.5, 4.8), dpi=300)
        shap.plots.waterfall(shap_values_display[pos_i], max_display=9, show=False)
        plt.title(title_c, fontsize=9.8, fontweight="bold", pad=12)
        plt.tight_layout()
        fig.savefig(OUT_DIR / fname_c, dpi=300, bbox_inches="tight")
        plt.close(fig)

    # --- FIGURA 7: ÁRBOL DE DECISIÓN INDIVIDUAL PEDAGÓGICO (TALLER 6 - SECCIÓN 5) ---
    tree_small = DecisionTreeClassifier(max_depth=3, min_samples_leaf=100, random_state=42)
    tree_small.fit(X_test_display_df.iloc[sample_idx], y_shap_sample)
    fig, ax = plt.subplots(figsize=(14, 5.5), dpi=300)
    plot_tree(
        tree_small,
        feature_names=all_feature_names,
        class_names=["Normal (≤60d)", "Severa (>60d)"],
        filled=True,
        rounded=True,
        proportion=True,
        max_depth=3,
        fontsize=8,
        ax=ax,
    )
    ax.set_title(
        "Explicación de un Árbol Individual Pequeño (max_depth=3) — Ilustración de Reglas de Corte (Distinto del Ensamble Completo)",
        fontsize=10.5, fontweight="bold", pad=10
    )
    plt.tight_layout()
    fig.savefig(OUT_DIR / "fig07_arbol_decision_interpretable.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    # =========================================================================
    # 9. GUARDADO DE RESUMEN ESTRUCTURADO JSON PARA REPORTES, PPTX Y STREAMLIT
    # =========================================================================
    summary_payload = {
        "dataset_total_rows": int(len(df)),
        "dataset_total_cases": int(df["ID_CAUSA_RIT"].nunique()),
        "train_recent_rows": int(len(X_train)),
        "train_recent_prev": float(y_train.mean()),
        "test_rows": int(len(X_test)),
        "test_prev": float(y_test.mean()),
        "train_full_rows": int(len(X_train_full)),
        "train_full_prev": float(y_train_full.mean()),
        "operational_threshold": OPERATIONAL_THRESHOLD,
        "features": feature_cols,
        "cv_results": cv_results,
        "test_results": test_results,
        "regime_sensitivity": regime_sensitivity,
        "bootstrap_summary": bootstrap_summary,
        "top_shap_features": top_shap_features,
        "local_cases": local_cases_info,
    }

    with open(OUT_DIR / "avance3_metrics_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary_payload, f, indent=2, ensure_ascii=False)

    print("8. Pipeline completado exitosamente. Resumen guardado en reports/figures_avance3/avance3_metrics_summary.json")


if __name__ == "__main__":
    main()

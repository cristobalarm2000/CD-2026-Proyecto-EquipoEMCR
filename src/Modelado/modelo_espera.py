"""
Bloques reutilizables del modelado de la espera (Avance 3).

Los usan el notebook `04_Modelado_audienciasparquet.ipynb` y el script `entrenar.py`.
La página 6 de Streamlit solo lee los artefactos que se guardan en `models/`.

Pregunta: dada una audiencia que se va a agendar, ¿qué probabilidad hay de que la
espera sea Rápida (≤ 15 d), Estándar (16–30 d) o con Demora (> 30 d)? Y como alerta
aparte: ¿qué probabilidad hay de una espera severa (> 60 d)?
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.frozen import FrozenEstimator
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score, confusion_matrix,
                             f1_score, precision_recall_curve, roc_auc_score, roc_curve)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

# -----------------------------------------------------------------------------
# Decisiones fijadas antes de mirar resultados
# -----------------------------------------------------------------------------
CLASES = ["Rápido (≤ 15 d)", "Estándar (16–30 d)", "Demora (> 30 d)"]
UMBRAL_SEVERA = 60

# Variables que el abogado conoce al momento de agendar
VARS = ["TRIBUNAL", "TIPO_PROCEDIMIENTO", "TIPO_AUDIENCIA"]
# Variables excluidas y por qué (se muestran en el notebook y en la app)
EXCLUIDAS = {
    "MACRO_MATERIA": "Es una función exacta de TIPO_PROCEDIMIENTO (información repetida).",
    "DIAS_TRAMITACION_PREVIA": "Se calcula con las mismas fechas que la espera (fuga de información).",
    "DIAS_DESPACHO_AGENDAMIENTO": "Se calcula con las mismas fechas que la espera (fuga de información).",
    "FECHA_AUDIENCIA (mes, día)": "No se conoce al agendar: es justamente lo que se quiere estimar.",
    "DURACION_MINUTOS, FRUSTRADA": "Ocurren después de la audiencia.",
    "ANO_AUDIENCIA": "El sistema cambió de régimen; extrapolar el año empeora el modelo.",
}

ANIO_VAL = 2023            # validación: aquí se ELIGE el modelo
ANIOS_TEST = (2024, 2025)  # prueba ciega: solo se REPORTA
ANIO_INICIO = 2015
# "Origen" = momento simulado en que se entrena: solo se usan años anteriores a él
ORIGEN_VAL, ORIGEN_TEST, ORIGEN_FINAL = 2023, 2024, 2026

# Una "receta" define qué años anteriores al origen se usan para entrenar
RECETAS = {
    "Completa": lambda origen: (ANIO_INICIO, origen - 1),
    "Reciente": lambda origen: (origen - 2, origen - 1),
}
ETIQUETA_RECETA = {"Completa": "Completa (desde 2015)", "Reciente": "Reciente (últimos 2 años)"}
MODELOS = ["Bayesiano jerárquico", "Regresión logística", "HistGradientBoosting"]
ORDEN_SIMPLEZA = {m: i for i, m in enumerate(MODELOS)}
TOLERANCIA_PARSIMONIA = 0.002  # si dos candidatos difieren menos que esto, gana el más simple
EPS = 1e-4                     # piso de probabilidad para métricas (evita log(0))


def etiqueta_receta(receta: str) -> str:
    return ETIQUETA_RECETA[receta]


def anios_variante(receta, origen, calibrado):
    """Años de entrenamiento y de calibración de una variante para un origen dado.
    Calibrar = reservar el último año antes del origen para calibrar en vez de entrenar."""
    a, b = RECETAS[receta](origen - 1 if calibrado else origen)
    return (a, b), (origen - 1 if calibrado else None)


def esquema(receta, calibrado):
    """Rol de cada año en validación y prueba (para el gráfico de la app)."""
    out = {}
    for nombre, origen, evalua in [("Validación (origen 2023)", ORIGEN_VAL, [ANIO_VAL]),
                                   ("Prueba (origen 2024)", ORIGEN_TEST, list(ANIOS_TEST))]:
        (a, b), cal = anios_variante(receta, origen, calibrado)
        roles = {}
        for anio in range(ANIO_INICIO, max(ANIOS_TEST) + 1):
            roles[anio] = ("Entrenamiento" if a <= anio <= b else "Calibración" if anio == cal
                           else "Evaluación" if anio in evalua else "No se usa")
        out[nombre] = roles
    return out


# -----------------------------------------------------------------------------
# Preparación
# -----------------------------------------------------------------------------
def congestion_previa(d: pd.DataFrame, dias: int = 90) -> np.ndarray:
    """Espera promedio del tribunal en audiencias YA realizadas en los `dias` previos
    a la fecha de programación. Es información disponible al agendar (sin fuga)."""
    out = np.full(len(d), np.nan)
    pos = pd.Series(np.arange(len(d)), index=d.index)
    for _, g in d.sort_values("FECHA_AUDIENCIA").groupby("TRIBUNAL"):
        fa = g["FECHA_AUDIENCIA"].values
        pl = g["PLAZO_AGENDAMIENTO"].astype(float).values
        fp = g["FECHA_PROGRAMACION"].values
        hi = np.searchsorted(fa, fp, side="left")
        lo = np.searchsorted(fa, fp - np.timedelta64(dias, "D"), side="left")
        cs = np.concatenate([[0.0], np.cumsum(pl)])
        n = hi - lo
        out[pos[g.index].values] = np.where(n > 0, (cs[hi] - cs[lo]) / np.maximum(n, 1), np.nan)
    return out


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    p = d["PLAZO_AGENDAMIENTO"].astype(int)
    d["Y"] = np.select([p <= 15, p <= 30], [0, 1], 2)
    d["SEVERA"] = (p > UMBRAL_SEVERA).astype(int)
    d["ANIO"] = d["ANO_AUDIENCIA"].astype(int)
    d["MODALIDAD"] = np.where(d["VIDEOCONFERENCIA"].astype(bool), "Telemática", "Presencial")
    d["MES_PROG"] = d["FECHA_PROGRAMACION"].dt.month.astype(str)
    d["DIA_PROG"] = d["FECHA_PROGRAMACION"].dt.dayofweek.astype(str)
    d["CONG_90D"] = congestion_previa(d)
    d["CONG_90D"] = d["CONG_90D"].fillna(d["PLAZO_AGENDAMIENTO"].astype(float).median())
    for c in VARS + ["MODALIDAD", "MES_PROG", "DIA_PROG", "ID_CAUSA_RIT"]:
        d[c] = d[c].astype(str)
    return d


def datos_evaluacion(d, origen):
    return d[d["ANIO"] == ANIO_VAL] if origen == ORIGEN_VAL else d[d["ANIO"].isin(ANIOS_TEST)]


def datos_variante(d, receta, origen, calibrado):
    (a, b), cal = anios_variante(receta, origen, calibrado)
    tr = d[(d["ANIO"] >= a) & (d["ANIO"] <= b)]
    ca = d[d["ANIO"] == cal] if cal else None
    return tr, ca


# -----------------------------------------------------------------------------
# Modelos
# -----------------------------------------------------------------------------
class TablaFrecuencias(ClassifierMixin, BaseEstimator):
    """Modelo bayesiano jerárquico (Dirichlet–multinomial con agrupamiento parcial).

    Estima la probabilidad de cada clase en la celda tribunal × procedimiento × tipo.
    Cada nivel usa al nivel superior como distribución a priori, con peso `alpha`
    (global → tipo → procedimiento × tipo → celda): si la celda tiene muchos casos manda
    su frecuencia; si tiene pocos, la estimación se acerca a la del nivel superior."""

    def __init__(self, niveles=None, alpha=10.0):
        self.niveles = niveles
        self.alpha = alpha

    def _niveles(self):
        return self.niveles or [["TIPO_AUDIENCIA"], ["TIPO_PROCEDIMIENTO", "TIPO_AUDIENCIA"], VARS]

    def fit(self, X, y):
        y = np.asarray(y)
        self.classes_ = np.unique(y)
        Y = (y[:, None] == self.classes_[None, :]).astype(float)
        self.prior_ = Y.mean(0)
        X = X.reset_index(drop=True)
        self.tablas_ = []
        for cols in self._niveles():
            t = pd.DataFrame(Y, columns=list(range(len(self.classes_))))
            t[cols] = X[cols].values
            self.tablas_.append((cols, t.groupby(cols).sum(), t.groupby(cols).size()))
        return self

    def predict_proba(self, X):
        X = X.reset_index(drop=True)
        P = np.tile(self.prior_, (len(X), 1))
        for cols, sumas, n in self.tablas_:
            idx = pd.MultiIndex.from_frame(X[cols]) if len(cols) > 1 else pd.Index(X[cols[0]])
            s = sumas.reindex(idx).to_numpy(dtype=float)
            m = n.reindex(idx).to_numpy(dtype=float)
            ok = ~np.isnan(m)
            P[ok] = (s[ok] + self.alpha * P[ok]) / (m[ok, None] + self.alpha)
        return P

    def predict(self, X):
        return self.classes_[self.predict_proba(X).argmax(1)]


def crear_modelo(nombre, vars_cat=VARS, vars_num=(), semilla=0):
    vars_cat, vars_num = list(vars_cat), list(vars_num)
    if nombre == "Bayesiano jerárquico":
        return TablaFrecuencias()
    if nombre == "Regresión logística":
        prep = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore"), vars_cat)]
                                 + ([("num", StandardScaler(), vars_num)] if vars_num else []))
        return Pipeline([("prep", prep), ("modelo", LogisticRegression(max_iter=3000, C=1.0))])
    if nombre == "HistGradientBoosting":
        prep = ColumnTransformer(
            [("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1,
                                    encoded_missing_value=-1), vars_cat)]
            + ([("num", "passthrough", vars_num)] if vars_num else []))
        hgb = HistGradientBoostingClassifier(
            categorical_features=[True] * len(vars_cat) + [False] * len(vars_num),
            max_iter=300, learning_rate=0.1, early_stopping=True, random_state=semilla)
        return Pipeline([("prep", prep), ("modelo", hgb)])
    raise ValueError(nombre)


def calibrar(modelo, X, y):
    """Calibración isotónica sobre un modelo ya entrenado (no se reentrena)."""
    return CalibratedClassifierCV(FrozenEstimator(modelo), method="isotonic").fit(X, y)


# -----------------------------------------------------------------------------
# Métricas
# -----------------------------------------------------------------------------
def suavizar(P):
    P = np.clip(np.asarray(P, dtype=float), EPS, None)
    return P / P.sum(1, keepdims=True)


def perdida_por_fila(y, P):
    P = suavizar(P)
    return -np.log(P[np.arange(len(y)), np.asarray(y)])


def metricas(y, P):
    y = np.asarray(y)
    P = suavizar(P)
    k = P.shape[1]
    pred = P.argmax(1)
    m = {
        "accuracy": accuracy_score(y, pred),
        "f1_macro": f1_score(y, pred, average="macro", labels=list(range(k))),
        "log_loss": float(perdida_por_fila(y, P).mean()),
        "brier": float(np.mean(np.sum((P - np.eye(k)[y]) ** 2, 1))),
    }
    if k == 2:
        m["roc_auc"] = roc_auc_score(y, P[:, 1])
        m["pr_auc"] = average_precision_score(y, P[:, 1])
        m["brier"] = float(np.mean((P[:, 1] - y) ** 2))
    return m


def ic_bootstrap(valores, grupos, B=300, semilla=0):
    """IC 95 % de la media de `valores` remuestreando CAUSAS completas (bootstrap de
    Poisson por grupo), porque las audiencias de una misma causa no son independientes."""
    cod = pd.factorize(np.asarray(grupos))[0]
    sumas = np.bincount(cod, weights=np.asarray(valores, dtype=float))
    cuentas = np.bincount(cod)
    rng = np.random.default_rng(semilla)
    stats = np.empty(B)
    for b in range(B):
        w = rng.poisson(1.0, len(sumas))
        stats[b] = (w @ sumas) / max(w @ cuentas, 1)
    return float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5))


def curva_calibracion(y_bin, p, bins=10):
    t = pd.DataFrame({"p": p, "y": y_bin})
    t["bin"] = pd.qcut(t["p"].rank(method="first"), bins, labels=False)
    g = t.groupby("bin").agg(prob_predicha=("p", "mean"), frecuencia_real=("y", "mean"), n=("y", "size"))
    return g.reset_index(drop=True)


# -----------------------------------------------------------------------------
# Experimentos
# -----------------------------------------------------------------------------
def lineas_base_rigidas(tr, d_eval, objetivo):
    """Reglas sin probabilidad: clase mayoritaria y moda por celda."""
    k = tr[objetivo].nunique()
    mayor = tr[objetivo].mode()[0]
    moda = tr.groupby(VARS)[objetivo].agg(lambda s: s.mode()[0])
    pred_moda = d_eval[VARS].merge(moda.rename("m"), left_on=VARS, right_index=True, how="left")["m"]
    pred_moda = pred_moda.fillna(mayor).astype(int).values
    y = d_eval[objetivo].values
    filas = []
    for nombre, pred in [("Siempre la clase mayoritaria", np.full(len(y), mayor)),
                         ("Moda por tribunal × procedimiento × tipo", pred_moda)]:
        filas.append({"modelo": nombre, "tipo": "Regla", "accuracy": accuracy_score(y, pred),
                      "f1_macro": f1_score(y, pred, average="macro", labels=list(range(k)))})
    return filas


def ajustar_variante(d, nombre, receta, origen, calibrado, objetivo, vars_cat=VARS, vars_num=(), semilla=0):
    """Entrena una variante usando SOLO años anteriores al `origen`."""
    tr, ca = datos_variante(d, receta, origen, calibrado)
    cols = list(vars_cat) + list(vars_num)
    m = crear_modelo(nombre, vars_cat, vars_num, semilla).fit(tr[cols], tr[objetivo].values)
    if calibrado:
        m = calibrar(m, ca[cols], ca[objetivo].values)
    return m


CONJUNTOS = [(ORIGEN_VAL, "Validación 2023"), (ORIGEN_TEST, "Prueba 2024–2025")]


def comparar_modelos(d, objetivo, receta, n_semillas=3, log=print):
    """Para cada origen (validación y prueba) entrena los 3 modelos, sin y con calibración,
    y los evalúa en el periodo siguiente. Devuelve filas de métricas y las probabilidades
    de la prueba (semilla 0) para curvas e intervalos."""
    etiqueta = etiqueta_receta(receta)
    filas, probs = [], {}
    for origen, conj in CONJUNTOS:
        ev = datos_evaluacion(d, origen)
        y = ev[objetivo].values
        tr, _ = datos_variante(d, receta, origen, False)
        prior = np.bincount(tr[objetivo], minlength=d[objetivo].nunique()) / len(tr)
        filas.append({"receta": etiqueta, "receta_clave": receta, "modelo": "Distribución global (sin variables)",
                      "tipo": "Línea base", "calibrado": False, "conjunto": conj,
                      **metricas(y, np.tile(prior, (len(y), 1)))})
        for f in lineas_base_rigidas(tr, ev, objetivo):
            filas.append({"receta": etiqueta, "receta_clave": receta, "calibrado": False, "conjunto": conj, **f})

        for nombre in MODELOS:
            semillas = range(n_semillas) if nombre == "HistGradientBoosting" else [0]
            for calibrado in (False, True):
                res = []
                for s in semillas:
                    estado = "calibrado" if calibrado else "sin calibrar"
                    log(f"  · {conj} · {etiqueta} · {nombre} · {estado} · semilla {s}")
                    m = ajustar_variante(d, nombre, receta, origen, calibrado, objetivo, semilla=s)
                    P = m.predict_proba(ev[VARS])
                    res.append(metricas(y, P))
                    if s == 0 and origen == ORIGEN_TEST:
                        probs[(nombre, calibrado)] = P
                fila = {"receta": etiqueta, "receta_clave": receta, "modelo": nombre, "tipo": "Modelo",
                        "calibrado": calibrado, "conjunto": conj,
                        **{k: float(np.mean([r[k] for r in res])) for k in res[0]},
                        "n_semillas": len(res), "log_loss_std_semillas": float(np.std([r["log_loss"] for r in res]))}
                if origen == ORIGEN_TEST:
                    perd = perdida_por_fila(y, probs[(nombre, calibrado)])
                    fila["log_loss_ic_inf"], fila["log_loss_ic_sup"] = ic_bootstrap(perd, ev["ID_CAUSA_RIT"])
                    if nombre != "Bayesiano jerárquico":
                        dif = perd - perdida_por_fila(y, probs[("Bayesiano jerárquico", calibrado)])
                        fila["dif_vs_bayes"] = float(dif.mean())
                        fila["dif_ic_inf"], fila["dif_ic_sup"] = ic_bootstrap(dif, ev["ID_CAUSA_RIT"])
                filas.append(fila)
    return filas, probs


def elegir(filas):
    """Elige con VALIDACIÓN 2023 (nunca con la prueba): menor log-loss; si otro candidato
    más simple está a menos de TOLERANCIA_PARSIMONIA, se prefiere el más simple."""
    t = pd.DataFrame(filas)
    t = t[(t["tipo"] == "Modelo") & (t["conjunto"] == "Validación 2023")].copy()
    mejor = t["log_loss"].min()
    t = t[t["log_loss"] <= mejor + TOLERANCIA_PARSIMONIA]
    t["orden"] = t["modelo"].map(ORDEN_SIMPLEZA) * 2 + t["calibrado"].astype(int)
    fila = t.sort_values(["orden", "log_loss"]).iloc[0]
    return {"receta_etiqueta": fila["receta"], "receta": fila["receta_clave"],
            "modelo": fila["modelo"], "calibrado": bool(fila["calibrado"]),
            "log_loss_validacion": float(fila["log_loss"]), "mejor_log_loss_validacion": float(mejor)}


CONJUNTOS_ABLACION = {
    "A · Tribunal + procedimiento + tipo": (VARS, []),
    "B · A + modalidad + mes y día de programación": (VARS + ["MODALIDAD", "MES_PROG", "DIA_PROG"], []),
    "C · A + congestión del tribunal (90 días previos)": (VARS, ["CONG_90D"]),
}


def ablacion(d, receta, log=print):
    """¿Agregar más variables mejora? HistGradientBoosting, semilla 0, sin calibrar."""
    filas = []
    for nombre, (cat, num) in CONJUNTOS_ABLACION.items():
        for origen, conj in CONJUNTOS:
            log(f"  · ablación {nombre} · {conj}")
            m = ajustar_variante(d, "HistGradientBoosting", receta, origen, False, "Y", cat, num)
            ev = datos_evaluacion(d, origen)
            filas.append({"variables": nombre, "conjunto": conj,
                          **metricas(ev["Y"].values, m.predict_proba(ev[cat + num]))})
    return filas


def prevalencia_por_anio(d):
    t = d.groupby("ANIO").agg(n=("Y", "size"), rapido=("Y", lambda s: (s == 0).mean()),
                              estandar=("Y", lambda s: (s == 1).mean()),
                              demora=("Y", lambda s: (s == 2).mean()), severa=("SEVERA", "mean"))
    return t.reset_index()


# -----------------------------------------------------------------------------
# Modelo para el simulador y comparador de tribunales
# -----------------------------------------------------------------------------
def entrenar_final(d, eleccion, objetivo, origen=ORIGEN_FINAL):
    """Misma variante elegida, aplicada con todos los datos disponibles (origen 2026)."""
    m = ajustar_variante(d, eleccion["modelo"], eleccion["receta"], origen, eleccion["calibrado"], objetivo)
    (a, b), cal = anios_variante(eleccion["receta"], origen, eleccion["calibrado"])
    return m, {"entrenamiento": f"{a}–{b}", "calibracion": str(cal) if cal else "—"}


def _ic_bootstrap_celda(v, B, rng):
    if len(v) < 5:
        return (np.nan,) * 4
    idx = rng.integers(0, len(v), (B, len(v)))
    muestras = v[idx]
    med = np.median(muestras, axis=1)
    p30 = (muestras > 30).mean(1)
    return (*np.percentile(med, [2.5, 97.5]), *np.percentile(p30, [2.5, 97.5]))


def grilla_tribunales(d, modelo_tramo, modelo_severa, anios=ANIOS_TEST, min_combo=100, B=400):
    """Para cada tribunal × (procedimiento, tipo) frecuente: probabilidades del modelo final
    y estadísticas reales del periodo reciente con IC 95 % por bootstrap."""
    rec = d[d["ANIO"].isin(anios)]
    combos = rec.groupby(["TIPO_PROCEDIMIENTO", "TIPO_AUDIENCIA"]).size()
    combos = combos[combos >= min_combo].index.to_frame(index=False)
    trib = pd.DataFrame({"TRIBUNAL": sorted(d["TRIBUNAL"].unique())})
    g = trib.merge(combos, how="cross")
    P = modelo_tramo.predict_proba(g[VARS])
    for i, c in enumerate(["p_rapido", "p_estandar", "p_demora"]):
        g[c] = P[:, i]
    g["p_severa"] = modelo_severa.predict_proba(g[VARS])[:, 1]

    rng = np.random.default_rng(0)
    filas = []
    for clave, s in rec.groupby(VARS)["PLAZO_AGENDAMIENTO"]:
        v = s.astype(float).values
        ic = _ic_bootstrap_celda(v, B, rng)
        filas.append({**dict(zip(VARS, clave)), "n": len(v),
                      "p25": np.percentile(v, 25), "mediana": np.median(v), "p75": np.percentile(v, 75),
                      "pct_mas30": (v > 30).mean(), "pct_mas60": (v > 60).mean(),
                      "mediana_ic_inf": ic[0], "mediana_ic_sup": ic[1],
                      "pct_mas30_ic_inf": ic[2], "pct_mas30_ic_sup": ic[3]})
    emp = pd.DataFrame(filas)
    g = g.merge(emp, on=VARS, how="left")
    g["n"] = g["n"].fillna(0).astype(int)
    return g


# -----------------------------------------------------------------------------
# Curvas y resumen para la app
# -----------------------------------------------------------------------------
def curvas_modelo_elegido(te, probs_elegidas, probs_crudas, probs_calibradas, objetivo):
    """Curvas en la prueba. `probs_crudas` y `probs_calibradas` son las dos variantes del
    modelo elegido (sin calibrar: entrena hasta 2023; calibrado: entrena hasta 2022 y calibra con 2023)."""
    y = te[objetivo].values
    out = {}
    if objetivo == "Y":
        out["confusion"] = confusion_matrix(y, probs_elegidas.argmax(1), labels=[0, 1, 2],
                                            normalize="true").tolist()
        out["calibracion"] = {}
        for k, clase in enumerate(CLASES):
            out["calibracion"][clase] = {
                "sin_calibrar": curva_calibracion((y == k).astype(int), probs_crudas[:, k]).to_dict("list"),
                "calibrado": curva_calibracion((y == k).astype(int), probs_calibradas[:, k]).to_dict("list"),
            }
    else:
        p = probs_elegidas[:, 1]
        pr, rc, _ = precision_recall_curve(y, p)
        fpr, tpr, _ = roc_curve(y, p)
        sel = lambda a, n=120: np.asarray(a)[np.linspace(0, len(a) - 1, min(n, len(a))).astype(int)].tolist()
        out["pr"] = {"precision": sel(pr), "recall": sel(rc)}
        out["roc"] = {"fpr": sel(fpr), "tpr": sel(tpr)}
        out["prevalencia"] = float(y.mean())
        out["calibracion"] = {
            "sin_calibrar": curva_calibracion(y, probs_crudas[:, 1]).to_dict("list"),
            "calibrado": curva_calibracion(y, probs_calibradas[:, 1]).to_dict("list"),
        }
    return out


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))


def guardar_artefactos(carpeta: Path, resultados: dict, grilla: pd.DataFrame, modelos: dict):
    import joblib
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    resultados = {**resultados, "generado": datetime.now().strftime("%Y-%m-%d %H:%M")}
    (carpeta / "resultados_modelado.json").write_text(
        json.dumps(resultados, ensure_ascii=False, indent=1, default=_json_default), encoding="utf-8")
    grilla.to_parquet(carpeta / "predicciones_tribunales.parquet", index=False)
    for nombre, m in modelos.items():
        joblib.dump(m, carpeta / f"{nombre}.joblib", compress=3)


def ejecutar_todo(df: pd.DataFrame, log=print):
    """Pipeline completo, el mismo que sigue el notebook 04. Devuelve
    (resultados, grilla, modelos) listos para `guardar_artefactos`."""
    log("Preparando datos...")
    d = preparar(df)
    R = {"clases": CLASES, "variables": VARS, "excluidas": EXCLUIDAS,
         "anio_validacion": ANIO_VAL, "anios_prueba": list(ANIOS_TEST),
         "recetas": dict(ETIQUETA_RECETA),
         "esquemas": {f"{r}|{c}": esquema(r, c) for r in RECETAS for c in (False, True)},
         "prevalencia": prevalencia_por_anio(d).to_dict("records")}
    te = datos_evaluacion(d, ORIGEN_TEST)

    for objetivo, clave in [("Y", "tramo"), ("SEVERA", "severa")]:
        log(f"Comparando modelos para '{clave}'...")
        filas, probs = [], {}
        for receta in RECETAS:
            f, p = comparar_modelos(d, objetivo, receta, log=log)
            filas += f
            probs[receta] = p
        el = elegir(filas)
        P = probs[el["receta"]]
        curvas = curvas_modelo_elegido(te, P[(el["modelo"], el["calibrado"])], P[(el["modelo"], False)],
                                       P[(el["modelo"], True)], objetivo)
        R[clave] = {"tabla": filas, "eleccion": el, "curvas": curvas}
        log(f"  → elegido: {el}")

    log("Ablación de variables...")
    R["ablacion"] = ablacion(d, R["tramo"]["eleccion"]["receta"], log=log)

    log("Entrenando modelos finales para el simulador...")
    m_tramo, info_t = entrenar_final(d, R["tramo"]["eleccion"], "Y")
    m_sev, info_s = entrenar_final(d, R["severa"]["eleccion"], "SEVERA")
    R["tramo"]["final"], R["severa"]["final"] = info_t, info_s
    grilla = grilla_tribunales(d, m_tramo, m_sev)
    return R, grilla, {"modelo_tramo": m_tramo, "modelo_severa": m_sev}

"""
Regenera los artefactos del modelado sin abrir Jupyter.

Uso (desde la raíz del proyecto):
    python src/Modelado/entrenar.py

Escribe en `models/`: resultados_modelado.json, predicciones_tribunales.parquet,
modelo_tramo.joblib y modelo_severa.joblib. Es el mismo pipeline del notebook 04.
"""
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))

import pandas as pd  # noqa: E402

from Modelado.modelo_espera import ejecutar_todo, guardar_artefactos  # noqa: E402

if __name__ == "__main__":
    t0 = time.time()
    df = pd.read_parquet(RAIZ / "data" / "processed" / "audiencias_preparadas_modelo.parquet")
    R, grilla, modelos = ejecutar_todo(df)
    guardar_artefactos(RAIZ / "models", R, grilla, modelos)
    print(f"Listo en {time.time() - t0:.0f} s → {RAIZ / 'models'}")

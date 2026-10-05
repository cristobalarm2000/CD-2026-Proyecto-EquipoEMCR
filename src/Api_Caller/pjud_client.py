"""Módulo centralizado para la conexión e ingesta de la API del Poder Judicial de Chile (PJUD).
Ubicación: src/Api_Caller/pjud_client.py
"""

import json
import re
import time
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Directorio del módulo Api_Caller
API_CALLER_DIR = Path(__file__).resolve().parent
CORTES_CSV_PATH = API_CALLER_DIR / "cortes.csv"
TRIBUNALES_CSV_PATH = API_CALLER_DIR / "tribunales.csv"
SWAGGER_JSON_PATH = API_CALLER_DIR / "swagger.json"
ENDPOINTS_CSV_PATH = API_CALLER_DIR / "endpoints.csv"

# Mapeos estándar de la API PJUD
ENDPOINTS_MAP = {
    "ingresos_rol_competencia_detalle": "Ingresos por Causa (RIT/Rol)",
    "terminos_rol_competencia_detalle": "Términos por Causa (RIT/Rol)",
    "ingresos_materia_competencia_detalle": "Ingresos por Materia Específica",
    "terminos_materia_competencia_detalle": "Términos por Materia Específica",
    "duracion_causas_competencia_detalle": "Duración de Causas (Días)",
    "causas_tramitacion_competencia_detalle": "Causas en Tramitación (Stock)",
    "audiencias_realizadas_competencia_detalle": "Audiencias Realizadas"
}

COMPETENCIAS_MAP = {
    "Familia": "Familia",
    "Laboral": "Laboral",
    "Oral en lo Penal (TOP)": "Top"
}

MAPA_COMPETENCIAS_INVERSO = {
    "Familia": "Familia",
    "Laboral": "Laboral",
    "Top": "Oral en lo Penal (TOP)"
}


def norm_col(c: str) -> str:
    """Normaliza nombres de columnas a mayúsculas sin tildes ni caracteres especiales."""
    c = unicodedata.normalize("NFKD", str(c)).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "_", c.strip().upper()).strip("_")


def cargar_catalogo_cortes(ruta_csv: Optional[Path] = None) -> pd.DataFrame:
    """Carga el catálogo de Cortes de Apelaciones."""
    p = ruta_csv or CORTES_CSV_PATH
    if p.exists():
        return pd.read_csv(p)
    return pd.DataFrame({"corte": [30], "glosa_corte": ["C.A. de Valparaíso"]})


def cargar_catalogo_tribunales(ruta_csv: Optional[Path] = None) -> pd.DataFrame:
    """Carga el catálogo de Tribunales."""
    p = ruta_csv or TRIBUNALES_CSV_PATH
    if p.exists():
        return pd.read_csv(p)
    return pd.DataFrame()


class PJUDClient:
    """Cliente HTTP resiliente con reintentos exponenciales para la API del PJUD."""
    BASE_URL = "https://estadisticaservices.pjud.cl/pjen"

    def __init__(
        self,
        retries: int = 3,
        backoff_factor: float = 1.5,
        timeout: int = 60,
        sleep_delay: float = 0.5
    ):
        self.timeout = timeout
        self.sleep_delay = sleep_delay
        self.session = requests.Session()
        retry_strategy = Retry(
            total=retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=frozenset(["GET"]),
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.session.headers.update({
            "User-Agent": "PJUD-ApiCaller/2.0 (EquipoEMCR)",
            "Accept": "application/json"
        })

    def construir_url(
        self,
        endpoint: str,
        corte: int,
        tribunal: int,
        competencia_api: str,
        anio: int
    ) -> str:
        """Construye la URL parametrizada para el endpoint solicitado."""
        return f"{self.BASE_URL}/{endpoint}/{corte}/{tribunal}/{competencia_api}/{anio}"

    def descargar(
        self,
        endpoint: str,
        anio: int,
        corte: int = 30,
        tribunal: int = 0,
        competencia_api: str = "Familia",
        force_refresh: bool = False,
        raw_dir: Optional[Path] = None
    ) -> Dict:
        """Descarga el payload de un endpoint y gestiona la caché local en disco."""
        target_dir = raw_dir or (API_CALLER_DIR.parent.parent / "data" / "raw" / "05_muestras")
        target_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{endpoint}__{corte}_{tribunal}_{competencia_api}_{anio}.json"
        filepath = target_dir / filename
        url = self.construir_url(endpoint, corte, tribunal, competencia_api, anio)

        res = {
            "endpoint": endpoint,
            "competencia": competencia_api,
            "anio": anio,
            "corte": corte,
            "tribunal": tribunal,
            "url": url,
            "status_code": 200,
            "registros": 0,
            "tamano_mb": 0.0,
            "desde_cache": False,
            "tiempo_s": 0.0,
            "error": None
        }

        t0 = time.time()
        if filepath.exists() and not force_refresh:
            try:
                data = json.loads(filepath.read_bytes())
                res["desde_cache"] = True
                res["tamano_mb"] = round(filepath.stat().st_size / (1024 * 1024), 2)
                res["registros"] = len(data) if isinstance(data, list) else 1
                res["tiempo_s"] = round(time.time() - t0, 3)
                return res
            except Exception as e:
                res["error"] = f"Error leyendo cache: {e}"

        try:
            resp = self.session.get(url, timeout=self.timeout)
            res["status_code"] = resp.status_code
            res["tamano_mb"] = round(len(resp.content) / (1024 * 1024), 2)
            if resp.status_code == 200:
                data = resp.json()
                res["registros"] = len(data) if isinstance(data, list) else 1
                filepath.write_bytes(resp.content)
            else:
                res["error"] = f"HTTP {resp.status_code}"
        except Exception as ex:
            res["error"] = str(ex)[:120]
        finally:
            res["tiempo_s"] = round(time.time() - t0, 3)
            time.sleep(self.sleep_delay)

        return res


def consolidar_a_parquet(
    raw_dir: Path,
    parquet_dir: Path,
    endpoints: List[str],
    competencias: List[str],
    anios: List[int],
    cod_corte: int = 30
) -> List[str]:
    """Lee archivos JSON crudos y consolida en datasets Parquet tipificados con compresión Snappy."""
    parquet_dir.mkdir(parents=True, exist_ok=True)
    consolidados = []

    for ep in endpoints:
        dfs = []
        for comp_nombre in competencias:
            comp_api = COMPETENCIAS_MAP.get(comp_nombre, comp_nombre)
            for anio in anios:
                p = raw_dir / f"{ep}__{cod_corte}_0_{comp_api}_{anio}.json"
                if p.exists():
                    try:
                        data = json.loads(p.read_bytes())
                        if data:
                            df_a = pd.json_normalize(data)
                            df_a.columns = [c.replace("_id.", "") for c in df_a.columns]
                            df_a.columns = [norm_col(c) for c in df_a.columns]
                            if "COMPETENCIA" not in df_a.columns:
                                df_a["COMPETENCIA"] = comp_api
                            if "ANO_PROCESO" not in df_a.columns and "ANO" not in df_a.columns:
                                df_a["ANO_PROCESO"] = anio
                            dfs.append(df_a)
                    except Exception:
                        pass
        if dfs:
            df_consolidado = pd.concat(dfs, ignore_index=True)
            # Parsear fechas
            for c in df_consolidado.columns:
                if any(kw in c for kw in ["FECHA", "FEC_"]):
                    s = df_consolidado[c].astype(str).str.strip()
                    df_consolidado[c] = pd.to_datetime(s, format="%Y-%m-%d", errors="coerce").fillna(
                        pd.to_datetime(s, format="%d-%m-%Y", errors="coerce")
                    )
            # IDs numéricos seguros
            for id_col in ["ID_CAUSA", "COD_CORTE", "COD_TRIBUNAL", "ID_AUDIENCIA", "TOTAL_TERMINOS", "TOTAL_CAUSAS", "TOTAL_AUDIENCIAS"]:
                if id_col in df_consolidado.columns:
                    df_consolidado[id_col] = pd.to_numeric(df_consolidado[id_col], errors="coerce").astype("Int64")
            # Armonizar tipos object
            for col in df_consolidado.columns:
                if df_consolidado[col].dtype == "object":
                    tipos = set(type(x) for x in df_consolidado[col].dropna())
                    if len(tipos) > 1:
                        df_consolidado[col] = df_consolidado[col].astype(str).str.replace(r"\.0$", "", regex=True)

            out_file = parquet_dir / f"{ep}.parquet"
            df_consolidado.to_parquet(out_file, engine="pyarrow", index=False, compression="snappy")
            consolidados.append(str(out_file))

    return consolidados

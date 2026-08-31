"""
Cliente para la API de Estadísticas del Poder Judicial de Chile.

Base:  https://estadisticaservices.pjud.cl
Docs:  https://estadisticaservices.pjud.cl/documentacion/

La API es pública (no requiere autenticación) y todas las rutas siguen el
patrón:

    /pjen/{endpoint}/{corte}/{tribunal}/{competencia}/{anio}

y devuelven una lista JSON de objetos {"key": <texto>, "value": <numero>}.

Los valores fijos (cortes y competencias) y las variables (año, sección,
competencia) están descritos en el documento "Uso de APIs" (usoapis.pdf).
"""

from __future__ import annotations

import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter

try:  # reintentos automáticos si urllib3 lo permite
    from urllib3.util.retry import Retry
except Exception:  # pragma: no cover
    Retry = None  # type: ignore


BASE_URL = "https://estadisticaservices.pjud.cl"

# --------------------------------------------------------------------------
# Valores fijos: Cortes de Apelaciones (0 = total país)
# --------------------------------------------------------------------------
CORTES: dict[int, str] = {
    0: "Todo el País",
    10: "C.A. de Arica",
    11: "C.A. de Iquique",
    15: "C.A. de Antofagasta",
    20: "C.A. de Copiapó",
    25: "C.A. de La Serena",
    30: "C.A. de Valparaíso",
    35: "C.A. de Rancagua",
    40: "C.A. de Talca",
    45: "C.A. de Chillán",
    46: "C.A. de Concepción",
    50: "C.A. de Temuco",
    55: "C.A. de Valdivia",
    56: "C.A. de Puerto Montt",
    60: "C.A. de Coyhaique",
    61: "C.A. de Punta Arenas",
    90: "C.A. de Santiago",
    91: "C.A. de San Miguel",
}

# --------------------------------------------------------------------------
# Valores variables: Competencia
#   Set general  -> aplica a la mayoría de las APIs
#   Set detalle  -> reemplaza "Penal" por "Garantia" y "Top"
# --------------------------------------------------------------------------
COMPETENCIAS = ["Civil", "Cobranza", "Familia", "Laboral", "Penal"]
COMPETENCIAS_DETALLE = ["Civil", "Cobranza", "Familia", "Laboral", "Garantia", "Top"]

# --------------------------------------------------------------------------
# Endpoints. Cada uno tiene además una variante "<nombre>_detalle" que
# entrega el desglose por tribunal (respuestas mucho más grandes).
# --------------------------------------------------------------------------
ENDPOINTS: dict[str, str] = {
    "ingresos_rol_competencia": "Ingresos por tipo de procedimiento (rol)",
    "ingresos_materia_competencia": "Ingresos por materia",
    "terminos_rol_competencia": "Términos por tipo de procedimiento (rol)",
    "terminos_materia_competencia": "Términos por materia",
    "causas_tramitacion_competencia": "Causas en tramitación",
    "duracion_causas_competencia": "Duración de causas (días)",
    "audiencias_realizadas_competencia": "Audiencias realizadas",
    "duracion_audiencias_competencia": "Duración de audiencias",
}

# Año mínimo consultable según la documentación.
ANIO_MINIMO = 2015


class PJUDError(RuntimeError):
    """Error al consultar la API del Poder Judicial."""


class PJUDClient:
    """Cliente simple con reintentos y timeout para la API pjud."""

    def __init__(self, base_url: str = BASE_URL, timeout: int = 60,
                 reintentos: int = 3, pausa: float = 1.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.pausa = pausa
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "pjud-visor/1.0 (+consumo API pública de estadísticas)",
        })
        if Retry is not None:
            retry = Retry(
                total=reintentos,
                backoff_factor=pausa,
                status_forcelist=(429, 500, 502, 503, 504),
                allowed_methods=frozenset(["GET"]),
            )
            adapter = HTTPAdapter(max_retries=retry)
            self.session.mount("https://", adapter)
            self.session.mount("http://", adapter)
        self._reintentos = reintentos

    # ------------------------------------------------------------------
    def url(self, endpoint: str, corte: int, tribunal: int,
            competencia: str, anio: int) -> str:
        return (f"{self.base_url}/pjen/{endpoint}/{int(corte)}/{int(tribunal)}/"
                f"{competencia}/{int(anio)}")

    # ------------------------------------------------------------------
    def consultar(self, endpoint: str, corte: int = 0, tribunal: int = 0,
                  competencia: str = "Civil", anio: int = 2025
                  ) -> list[dict[str, Any]]:
        """Devuelve la lista [{'key':..., 'value':...}, ...] del endpoint.

        Una lista vacía significa que el Poder Judicial aún no publica esa
        combinación de competencia/año (habitual a comienzos de año).
        """
        if anio < ANIO_MINIMO:
            raise PJUDError(f"El año mínimo consultable es {ANIO_MINIMO} (se pidió {anio}).")

        url = self.url(endpoint, corte, tribunal, competencia, anio)
        ultimo_error: Exception | None = None
        for intento in range(1, self._reintentos + 1):
            try:
                resp = self.session.get(url, timeout=self.timeout)
                resp.raise_for_status()
                if not resp.text.strip():
                    return []
                datos = resp.json()
                if isinstance(datos, dict):  # algunos errores llegan como dict
                    raise PJUDError(f"Respuesta inesperada de {url}: {datos}")
                return datos
            except (requests.RequestException, ValueError) as exc:
                ultimo_error = exc
                if intento < self._reintentos:
                    time.sleep(self.pausa * intento)
        raise PJUDError(f"No se pudo consultar {url}: {ultimo_error}")

    # ------------------------------------------------------------------
    def total(self, datos: list[dict[str, Any]]) -> float:
        return float(sum(float(d.get("value", 0) or 0) for d in datos))


def nombre_corte(corte: int) -> str:
    return CORTES.get(int(corte), f"Corte {corte}")

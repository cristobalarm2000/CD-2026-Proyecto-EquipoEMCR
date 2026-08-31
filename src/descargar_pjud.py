"""
Descarga las bases fila-a-fila de "Poder Judicial en Números"
(https://numeros.pjud.cl) desde su API de descargas:

    https://estadisticaservices.pjud.cl/descargas/descargas/<seccion>/<Dataset>/<Dataset>-<AÑO>-CSV.zip

Cada ZIP -CSV trae los CSV "por Rol" y (para Ingresos/Términos) "por Materia".

Uso:
    python src/descargar_pjud.py --competencia familia --anios 2022 2023 2024
    python src/descargar_pjud.py --competencia familia --anios 2024 --datasets Ingresos Terminos

Salida por defecto: data/raw/<competencia>/
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import requests

BASE = "https://estadisticaservices.pjud.cl/descargas/descargas"
CATALOGO = "https://estadisticaservices.pjud.cl/pjen/cifras_clave/descargas/{seccion}/{anio}"

# LINK tal como lo entrega el catálogo (cifras_clave/descargas).
DATASETS_DEFECTO = {
    "Ingresos": "/{sec}/Ingresos/Ingresos-",
    "Terminos": "/{sec}/Terminos/Terminos-",
    "Inventario": "/{sec}/Inventario/Inventario-",
    "Duracion": "/{sec}/Duracion/Duracion-",
    "Audiencias": "/{sec}/Audiencias/Audiencias-",
}


def sesion() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0",
                      "Referer": "https://numeros.pjud.cl/"})
    return s


def descargar(url: str, destino: Path, s: requests.Session, reintentos: int = 3) -> int:
    for intento in range(1, reintentos + 1):
        try:
            with s.get(url, timeout=(20, 600), stream=True) as r:
                if r.status_code != 200:
                    print(f"  HTTP {r.status_code}  {url}")
                    return 0
                n = 0
                destino.parent.mkdir(parents=True, exist_ok=True)
                with destino.open("wb") as fh:
                    for chunk in r.iter_content(1 << 20):
                        fh.write(chunk)
                        n += len(chunk)
                return n
        except requests.RequestException as e:
            print(f"  reintento {intento}: {type(e).__name__}: {e}")
            time.sleep(3 * intento)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--competencia", default="familia",
                    help="seccion: familia | penal | civil | cobranza | laboral")
    ap.add_argument("--anios", nargs="+", type=int, required=True)
    ap.add_argument("--datasets", nargs="+", default=list(DATASETS_DEFECTO),
                    help=f"por defecto: {', '.join(DATASETS_DEFECTO)}")
    ap.add_argument("--salida", default=None,
                    help="carpeta destino (por defecto data/raw/<competencia>/)")
    args = ap.parse_args(argv)

    sec = args.competencia.lower()
    dest = Path(args.salida) if args.salida else Path("data/raw") / sec
    s = sesion()

    total = 0
    for anio in args.anios:
        for ds in args.datasets:
            link = DATASETS_DEFECTO.get(ds, f"/{{sec}}/{ds}/{ds}-").format(sec=sec)
            url = f"{BASE}{link}{anio}-CSV.zip"
            out = dest / f"{ds}-{anio}-CSV.zip"
            if out.exists() and out.stat().st_size > 10_000:
                print(f"= {out.name} ya existe ({out.stat().st_size:,} B)")
                total += out.stat().st_size
                continue
            n = descargar(url, out, s)
            if n:
                print(f"+ {out.name}  {n:,} B")
                total += n
            else:
                print(f"! {out.name}  FALLIDO")
    print(f"\nTotal: {total/1e9:.2f} GB en {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""
Descomprime los ZIP -CSV de PJUD a CSV con nombres limpios.

    python src/descomprimir_zips.py --entrada data/raw/familia --salida data/raw/familia/csv

Cada miembro se guarda como  <Dataset>-<AÑO>[-Rol|-Materia].csv
Se omiten los archivos "__MACOSX" y los duplicados byte a byte.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
import zipfile
from pathlib import Path


def sufijo(nombre_miembro: str) -> str:
    n = nombre_miembro.lower()
    if "materia" in n:
        return "Materia"
    if "rol" in n:
        return "Rol"
    if "realizadas" in n:
        return "Realizadas"
    if "duracion de audiencias" in n or "duración de audiencias" in n:
        return "DuracionAudiencias"
    return ""


def md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entrada", required=True, help="carpeta con los .zip")
    ap.add_argument("--salida", default=None, help="carpeta destino (def: <entrada>/csv)")
    args = ap.parse_args(argv)

    entrada = Path(args.entrada)
    salida = Path(args.salida) if args.salida else entrada / "csv"
    salida.mkdir(parents=True, exist_ok=True)

    vistos: dict[str, str] = {}
    total = 0
    for z in sorted(entrada.glob("*.zip")):
        stem = re.sub(r"-CSV$", "", z.stem)  # Ingresos-2024
        zf = zipfile.ZipFile(z)
        for m in zf.namelist():
            if not m.lower().endswith(".csv") or "macosx" in m.lower():
                continue
            suf = sufijo(m)
            dest = salida / f"{stem}{('-' + suf) if suf else ''}.csv"
            if dest.exists() and dest.stat().st_size > 1000:
                print(f"= {dest.name} ya existe")
                continue
            n = 0
            with zf.open(m) as fh, dest.open("wb") as out:
                while (b := fh.read(1 << 20)):
                    out.write(b)
                    n += len(b)
            firma = md5(dest)
            if firma in vistos:
                print(f"- {dest.name}  duplicado de {vistos[firma]} -> eliminado")
                dest.unlink()
                continue
            vistos[firma] = dest.name
            total += n
            print(f"+ {dest.name}  {n/1e6:,.0f} MB")
    print(f"\nTotal: {total/1e9:.2f} GB en {salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

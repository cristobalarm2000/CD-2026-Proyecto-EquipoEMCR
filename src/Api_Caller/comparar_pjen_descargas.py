#!/usr/bin/env python3
"""
Compara los INGRESOS que ya extraes de /descargas/ con los detalles equivalentes de /pjen/.

Pregunta que responde: ¿ambas fuentes contienen las mismas causas (CRR CAUSA == ID_CAUSA)?
y, en las causas comunes, ¿coinciden RIT, RUC, tribunal, fecha y materia?

Entradas
  --descargas    archivo de ingresos de /descargas/ (csv, tsv o xlsx), con columnas como
                 "CRR CAUSA", "CÓDIGO TRIBUNAL", "RIT", "RUC", "FECHA INGRESO", "AÑO INGRESO", "COD. MATERIA", "SISTEMA"
  --pjen-rol     JSON de PJUD_FAMILIA/05_muestras/ingresos_rol_competencia_detalle__30_0_Familia_2023.json
  --pjen-materia JSON de PJUD_FAMILIA/05_muestras/ingresos_materia_competencia_detalle__30_0_Familia_2023.json  (opcional)

Ejemplo
  python comparar_pjen_descargas.py --descargas C:\\ruta\\ingresos_2023.csv ^
     --pjen-rol PJUD_FAMILIA\\05_muestras\\ingresos_rol_competencia_detalle__30_0_Familia_2023.json ^
     --pjen-materia PJUD_FAMILIA\\05_muestras\\ingresos_materia_competencia_detalle__30_0_Familia_2023.json ^
     --anio 2023 --sistema SITFA

Salida: informe en consola + CSV en --out (por tribunal, discrepancias y causas que están solo en un lado).
Requiere: pandas (y openpyxl solo si el archivo es xlsx).
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd


def norm_col(c: str) -> str:
    c = unicodedata.normalize("NFKD", str(c)).encode("ascii", "ignore").decode()
    c = re.sub(r"[^A-Za-z0-9]+", "_", c.strip().upper()).strip("_")
    return c


def leer_descargas(path: str) -> pd.DataFrame:
    p = Path(path)
    if p.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(p, dtype=str)
    else:
        for enc in ("utf-8-sig", "latin-1"):
            try:
                df = pd.read_csv(p, sep=None, engine="python", dtype=str, encoding=enc)
                break
            except UnicodeDecodeError:
                continue
    df.columns = [norm_col(c) for c in df.columns]
    return df


def leer_pjen(path: str) -> pd.DataFrame:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    df = pd.json_normalize(data)
    df.columns = [norm_col(c.replace("_id.", "")) for c in df.columns]   # aplana el objeto _id
    return df


def a_id(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").astype("Int64")


def a_fecha(s: pd.Series) -> pd.Series:
    """Acepta 2023-01-20 (ISO) y 20-01-2023 (dd-mm-aaaa)."""
    s = s.astype(str).str.strip()
    iso = pd.to_datetime(s, format="%Y-%m-%d", errors="coerce")
    dmy = pd.to_datetime(s, format="%d-%m-%Y", errors="coerce")
    return iso.fillna(dmy)


def limpia(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.upper()


def comparar(nombre, d, p, out: Path, tiene_materia: bool):
    print(f"\n=== {nombre} ===")
    n_dup_p = int(p["ID"].duplicated().sum())
    n_dup_d = int(d["ID"].duplicated().sum())
    print(f"filas:      descargas={len(d):,}   pjen={len(p):,}")
    print(f"ID únicos:  descargas={d['ID'].nunique():,}   pjen={p['ID'].nunique():,}   (repetidos: descargas={n_dup_d:,}, pjen={n_dup_p:,})")
    sd, sp = set(d["ID"].dropna()), set(p["ID"].dropna())
    comunes = sd & sp
    solo_d, solo_p = sd - sp, sp - sd
    print(f"en ambas:   {len(comunes):,}   solo descargas: {len(solo_d):,}   solo pjen: {len(solo_p):,}")
    if sd:
        print(f"cobertura:  {len(comunes)/len(sd):.2%} de las causas de descargas aparecen en pjen")
    pd.Series(sorted(solo_d), name="ID").to_csv(out / f"{nombre}_solo_descargas.csv", index=False)
    pd.Series(sorted(solo_p), name="ID").to_csv(out / f"{nombre}_solo_pjen.csv", index=False)

    # coincidencia de campos en causas comunes (1 fila por ID en cada lado para comparar)
    dd = d.drop_duplicates("ID").set_index("ID").loc[sorted(comunes)]
    pp = p.drop_duplicates("ID").set_index("ID").loc[sorted(comunes)]
    campos = [("RIT", "RIT", limpia), ("RUC", "RUC", lambda s: limpia(s).str.replace(" ", "", regex=False)),
              ("COD_TRIBUNAL", "COD_TRIBUNAL", a_id), ("FECHA", "FECHA", None)]
    if tiene_materia:
        campos += [("COD_MATERIA", "COD_MATERIA", limpia)]
    filas = []
    for etiqueta, col, fn in campos:
        if etiqueta == "FECHA":
            a, b = a_fecha(dd["FECHA_INGRESO"]), a_fecha(pp["FECHA_INGRESO"])
        else:
            if col not in dd.columns or col not in pp.columns:
                continue
            a, b = (fn(dd[col]), fn(pp[col]))
        ok = (a == b) | (a.isna() & b.isna())
        filas.append((etiqueta, int(ok.sum()), int((~ok).sum())))
        print(f"  {etiqueta:<13} coinciden {ok.sum():>8,}   difieren {(~ok).sum():>8,}")
        if (~ok).any():
            dif = pd.DataFrame({"ID": dd.index[~ok.values], "descargas": a[~ok].values, "pjen": b[~ok].values})
            dif.head(5000).to_csv(out / f"{nombre}_difiere_{etiqueta}.csv", index=False)

    # por tribunal
    t = pd.DataFrame({"descargas": d.groupby("COD_TRIBUNAL")["ID"].nunique(),
                      "pjen": p.groupby("COD_TRIBUNAL")["ID"].nunique()}).fillna(0).astype(int)
    t["diferencia"] = t["pjen"] - t["descargas"]
    t.to_csv(out / f"{nombre}_por_tribunal.csv")
    print(f"  tribunales con diferencia: {(t['diferencia'] != 0).sum()} de {len(t)}  (detalle en {nombre}_por_tribunal.csv)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--descargas", required=True)
    ap.add_argument("--pjen-rol", required=True)
    ap.add_argument("--pjen-materia")
    ap.add_argument("--anio", type=int, default=2023)
    ap.add_argument("--corte", type=int, default=30)
    ap.add_argument("--sistema", default="SITFA", help="filtra descargas por columna SISTEMA ('' = no filtrar)")
    ap.add_argument("--out", default="COMPARACION")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(exist_ok=True)

    d = leer_descargas(a.descargas)
    necesarias = ["CRR_CAUSA", "CODIGO_TRIBUNAL", "RIT", "RUC", "FECHA_INGRESO"]
    faltan = [c for c in necesarias if c not in d.columns]
    if faltan:
        sys.exit(f"Faltan columnas en descargas: {faltan}\nColumnas leídas: {list(d.columns)}")
    d = d.rename(columns={"CRR_CAUSA": "ID", "CODIGO_TRIBUNAL": "COD_TRIBUNAL", "CODIGO_CORTE": "COD_CORTE"})
    d["ID"], d["COD_TRIBUNAL"] = a_id(d["ID"]), a_id(d["COD_TRIBUNAL"])
    if "ANO_INGRESO" in d.columns:
        d = d[pd.to_numeric(d["ANO_INGRESO"], errors="coerce") == a.anio]
    if "COD_CORTE" in d.columns:
        d = d[pd.to_numeric(d["COD_CORTE"], errors="coerce") == a.corte]
    if a.sistema and "SISTEMA" in d.columns:
        antes = len(d); d = d[limpia(d["SISTEMA"]) == a.sistema.upper()]
        print(f"descargas: filtrado SISTEMA={a.sistema}: {antes:,} -> {len(d):,} filas")
    d = d.rename(columns={"COD_MATERIA": "COD_MATERIA"})

    def prep_pjen(path):
        p = leer_pjen(path)
        p = p.rename(columns={"ID_CAUSA": "ID"})
        p["ID"], p["COD_TRIBUNAL"] = a_id(p["ID"]), a_id(p["COD_TRIBUNAL"])
        if "ANO_INGRESO" in p.columns:
            p = p[pd.to_numeric(p["ANO_INGRESO"], errors="coerce") == a.anio]
        return p

    comparar("pjen_rol", d, prep_pjen(a.pjen_rol), out, tiene_materia=False)
    if a.pjen_materia:
        comparar("pjen_materia", d, prep_pjen(a.pjen_materia), out, tiene_materia=True)
    print(f"\nListo. Archivos en {out}/")


if __name__ == "__main__":
    main()

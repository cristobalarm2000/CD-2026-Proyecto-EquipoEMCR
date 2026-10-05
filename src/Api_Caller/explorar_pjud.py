#!/usr/bin/env python3
"""
PJUD API Explorer  -  fase de EXPLORACIÓN (no es el descargador masivo).

Qué hace
  1. Lee swagger.json y lista los endpoints /pjen/ con sus parámetros       -> 01_endpoints.csv, 02_parametros.csv
  2. Prueba una muestra pequeña (1 año, 1 corte) contra la API real           -> 03_pruebas_api.csv, 05_muestras/
  3. Registra status HTTP, tipo de respuesta, nº de registros y campos       -> para decidir cómo diseñar el descargador

Valores de parámetros (fuente: "Documento de Uso de APIs", PJUD, 20/04/2021)
  corte       int   0 = todo el país; códigos en cortes.csv
  tribunal    int   0 = total país / total corte; códigos en tribunales.csv
  anio / ano  int   desde 2015
  seccion     str   por ahora solo "0"
  competencia str   con mayúscula inicial. Para los endpoints *_competencia:
                    Civil, Cobranza, Familia, Laboral, Garantia, Top
                    (el set general, para el resto, usa Penal en vez de Garantia/Top)

Uso típico
  python explorar_pjud.py --dry-run                 # sin red: solo genera 01 y 02 y muestra qué probaría
  python explorar_pjud.py                           # prueba la muestra por defecto (año 2023, corte 30)
  python explorar_pjud.py --anio 2022 --corte 0 --competencia Familia
  python explorar_pjud.py --endpoints ingresos_rol_competencia terminos_rol_competencia
  python explorar_pjud.py --todos                   # 1 llamada por endpoint (puede ser lento)

Requiere: pip install requests
"""
import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path

COMPETENCIAS_COMP = ["Civil", "Cobranza", "Familia", "Laboral", "Garantia", "Top"]   # endpoints *_competencia
COMPETENCIAS_GEN = ["Civil", "Cobranza", "Familia", "Laboral", "Penal"]               # set general
MUESTRA_DEFECTO = [
    "ingresos_rol_competencia",
    "terminos_rol_competencia",
    "causas_tramitacion_competencia",
    "duracion_causas_competencia",
]
HTTP_METHODS = {"get", "post", "put", "delete", "patch"}


# ----------------------------------------------------------------------------- Swagger
def cargar_swagger(origen: str) -> dict:
    if re.match(r"^https?://", origen):
        import requests
        r = requests.get(origen, timeout=60)
        r.raise_for_status()
        return r.json()
    return json.loads(Path(origen).read_text(encoding="utf-8"))


def base_del_swagger(sw: dict, base_url: str) -> str:
    """Devuelve base_url + basePath (Swagger 2) o el path del primer server (OpenAPI 3)."""
    prefijo = ""
    if sw.get("basePath") and sw["basePath"] != "/":
        prefijo = sw["basePath"].rstrip("/")
    elif sw.get("servers"):
        u = sw["servers"][0].get("url", "")
        m = re.match(r"^https?://[^/]+(/.*)?$", u)
        prefijo = (m.group(1) or "").rstrip("/") if m else u.rstrip("/") if u.startswith("/") else ""
    return base_url.rstrip("/") + prefijo


def extraer_endpoints(sw: dict):
    """Lista de dicts: path, nombre, metodo, operation_id, tags, params[{name,in,required,type}]."""
    eps = []
    for path, item in sw.get("paths", {}).items():
        if not path.startswith("/pjen/"):
            continue
        comunes = item.get("parameters", [])
        for metodo, op in item.items():
            if metodo.lower() not in HTTP_METHODS:
                continue
            params = []
            for p in comunes + op.get("parameters", []):
                tipo = p.get("type") or (p.get("schema") or {}).get("type") or ""
                params.append({"name": p.get("name"), "in": p.get("in"),
                               "required": bool(p.get("required")), "type": tipo})
            nombre = path.split("/")[2] if path.count("/") >= 2 else path
            eps.append({"path": path, "nombre": nombre, "metodo": metodo.upper(),
                        "operation_id": op.get("operationId", ""),
                        "tags": "|".join(op.get("tags", [])), "params": params})
    return eps


def familia(params) -> str:
    nombres = {p["name"] for p in params if p["in"] == "path"}
    anio = {"anio", "ano"} & nombres
    resto = nombres - anio
    mapa = {frozenset({"corte"}): "corte+anio",
            frozenset({"seccion"}): "seccion+anio",
            frozenset({"corte", "tribunal", "competencia"}): "corte+tribunal+competencia+anio"}
    return mapa.get(frozenset(resto), "otra: " + ",".join(sorted(nombres))) if anio else "otra: " + ",".join(sorted(nombres))


# ----------------------------------------------------------------------------- Valores
def valor_param(nombre: str, args, anio: int = None, competencia: str = None):
    if nombre in ("anio", "ano"):
        if anio is not None:
            return anio
        if isinstance(args.anio, list):
            return args.anio[0] if args.anio else 2023
        return args.anio
    if nombre == "corte":
        return args.corte
    if nombre == "tribunal":
        return args.tribunal
    if nombre == "seccion":
        return "0"
    if nombre == "competencia":
        if competencia is not None:
            return competencia
        if isinstance(args.competencia, list):
            return args.competencia[0] if args.competencia else "Civil"
        return args.competencia
    return None   # desconocido -> no se prueba, queda registrado


def construir_url(base, ep, args, anio: int = None, competencia: str = None):
    url, faltan = ep["path"], []
    for p in ep["params"]:
        if p["in"] != "path":
            continue
        v = valor_param(p["name"], args, anio=anio, competencia=competencia)
        if v is None:
            faltan.append(p["name"])
        else:
            url = url.replace("{" + p["name"] + "}", str(v))
    return base + url, faltan


def competencia_valida(ep, comp):
    """Avisa (no bloquea) si la competencia pedida no está en el set documentado para ese endpoint."""
    if not any(p["name"] == "competencia" for p in ep["params"]):
        return True
    valid = COMPETENCIAS_COMP if ep["nombre"].endswith(("_competencia", "_competencia_detalle")) else COMPETENCIAS_GEN
    return comp in valid


# ----------------------------------------------------------------------------- HTTP
def sesion(reintentos):
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    s = requests.Session()
    r = Retry(total=reintentos, backoff_factor=1.5, status_forcelist=(429, 500, 502, 503, 504),
              allowed_methods=frozenset(["GET"]), raise_on_status=False)
    s.mount("https://", HTTPAdapter(max_retries=r))
    s.mount("http://", HTTPAdapter(max_retries=r))
    s.headers["User-Agent"] = "pjud-api-explorer/0.1 (proyecto academico)"
    s.headers["Accept"] = "application/json"
    return s


def resumir_respuesta(resp):
    """-> (tipo, n_registros, campos, primer_registro)"""
    try:
        data = resp.json()
    except ValueError:
        return "no-json", "", "", ""
    if isinstance(data, list):
        reg = data
        tipo = "lista"
    elif isinstance(data, dict):
        listas = [(k, v) for k, v in data.items() if isinstance(v, list)]
        if listas:
            k, reg = max(listas, key=lambda kv: len(kv[1]))
            tipo = f"objeto->lista[{k}]"
        else:
            reg, tipo = [data], "objeto"
    else:
        return type(data).__name__, "", "", str(data)[:200]
    primero = reg[0] if reg else ""
    campos = "|".join(primero.keys()) if isinstance(primero, dict) else ""
    return tipo, len(reg), campos, json.dumps(primero, ensure_ascii=False)[:300]


# ----------------------------------------------------------------------------- main
DEFAULT_SWAGGER = str(Path(__file__).resolve().parent / "swagger.json")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--swagger", default=DEFAULT_SWAGGER, help="ruta local o URL del swagger.json")
    ap.add_argument("--base-url", default="https://estadisticaservices.pjud.cl")
    ap.add_argument("--out", default="PJUD_API_EXPLORER")
    ap.add_argument("--anio", nargs="*", type=int, default=None, help="año o lista de años (def: 2023)")
    ap.add_argument("--anios", nargs="*", type=int, default=None, help="alias para lista de años")
    ap.add_argument("--desde", type=int, default=None, help="año inicial del rango (ej: 2020)")
    ap.add_argument("--hasta", type=int, default=None, help="año final del rango (ej: 2025)")
    ap.add_argument("--corte", type=int, default=30, help="0 = todo el país")
    ap.add_argument("--tribunal", type=int, default=0, help="0 = total del corte/país")
    ap.add_argument("--competencia", nargs="*", default=None, help="competencia o lista de competencias (Civil, Familia, Laboral, Top...)")
    ap.add_argument("--competencias", nargs="*", default=None, help="alias para lista de competencias")
    ap.add_argument("--endpoints", nargs="*", help="nombres a probar (def: muestra pequeña)")
    ap.add_argument("--todos", action="store_true", help="probar 1 vez cada endpoint /pjen/")
    ap.add_argument("--sleep", type=float, default=1.0, help="pausa entre llamadas (s)")
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--reintentos", type=int, default=3)
    ap.add_argument("--refrescar", action="store_true", help="ignorar muestras ya guardadas")
    ap.add_argument("--dry-run", action="store_true", help="no llama a la API; solo genera 01/02 y lista las URLs")
    args = ap.parse_args()

    if args.desde is not None and args.hasta is not None:
        anios = list(range(args.desde, args.hasta + 1))
    elif args.anios:
        anios = args.anios
    elif args.anio:
        anios = args.anio if isinstance(args.anio, list) else [args.anio]
    else:
        anios = [2023]

    for a in anios:
        if a < 2015:
            sys.exit(f"El PDF indica que la API entrega datos desde 2015. Año inválido: {a}")

    MAPA_COMP = {
        "ORAL": "Top",
        "TOP": "Top",
        "ORAL EN LO PENAL": "Top",
        "ORAL_EN_LO_PENAL": "Top",
        "PENAL ORAL": "Top",
        "PENAL": "Penal",
        "GARANTIA": "Garantia",
        "LABORAL": "Laboral",
        "FAMILIA": "Familia",
        "CIVIL": "Civil",
        "COBRANZA": "Cobranza"
    }

    raw_comps = args.competencias or args.competencia or ["Civil"]
    if isinstance(raw_comps, str):
        raw_comps = [raw_comps]
    competencias = []
    for c in raw_comps:
        k = c.strip().upper()
        competencias.append(MAPA_COMP.get(k, c.capitalize()))

    out = Path(args.out)
    (out / "05_muestras").mkdir(parents=True, exist_ok=True)
    (out / "logs").mkdir(exist_ok=True)

    sw = cargar_swagger(args.swagger)
    (out / "swagger.json").write_text(json.dumps(sw, ensure_ascii=False, indent=1), encoding="utf-8")
    base = base_del_swagger(sw, args.base_url)
    eps = extraer_endpoints(sw)
    if not eps:
        sys.exit("No se encontraron rutas /pjen/ en el swagger.")

    # 01 y 02
    with open(out / "01_endpoints.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["nombre", "path", "metodo", "operation_id", "tags", "es_detalle", "familia_parametros"])
        for e in eps:
            w.writerow([e["nombre"], e["path"], e["metodo"], e["operation_id"], e["tags"],
                        e["nombre"].endswith("_detalle"), familia(e["params"])])
    with open(out / "02_parametros.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["endpoint", "parametro", "in", "tipo", "obligatorio"])
        for e in eps:
            for p in e["params"]:
                w.writerow([e["nombre"], p["name"], p["in"], p["type"], p["required"]])

    fam = {}
    for e in eps:
        fam.setdefault(familia(e["params"]), []).append(e["nombre"])
    print(f"Endpoints /pjen/: {len(eps)}  (base: {base})")
    for k, v in sorted(fam.items()):
        print(f"  {k}: {len(v)}")

    # selección de lo que se prueba
    por_nombre = {e["nombre"]: e for e in eps}
    if args.todos:
        sel = eps
    else:
        pedidos = args.endpoints or MUESTRA_DEFECTO
        sel = []
        for n in pedidos:
            if n in por_nombre:
                sel.append(por_nombre[n])
            else:
                parecidos = [x for x in por_nombre if n.split("_")[0] in x][:5]
                print(f"AVISO: '{n}' no existe en el swagger. Parecidos: {parecidos}")
    print(f"A probar: {len(sel)} endpoint(s)  | anios={anios} corte={args.corte} tribunal={args.tribunal} competencias={competencias}")

    filas, s = [], (None if args.dry_run else sesion(args.reintentos))
    total_iter = len(competencias) * len(anios) * len(sel)
    i = 0
    for comp in competencias:
        for a in anios:
            for e in sel:
                i += 1
                url, faltan = construir_url(base, e, args, anio=a, competencia=comp)
                fila = {"endpoint": e["nombre"], "competencia": comp, "anio": a, "url": url, "status": "", "tipo": "", "n_registros": "", "bytes": "",
                        "campos": "", "primer_registro": "", "error": "", "desde_cache": False}
                if faltan:
                    fila["error"] = "parametros sin valor definido: " + ",".join(faltan)
                elif not competencia_valida(e, comp):
                    fila["error"] = f"competencia '{comp}' fuera del set documentado para este endpoint"
                if args.dry_run:
                    print(f"[dry-run {i}/{total_iter}] {url} {('<- ' + fila['error']) if fila['error'] else ''}")
                    filas.append(fila)
                    continue
                if fila["error"].startswith("parametros"):
                    filas.append(fila); continue

                usados = [str(valor_param(p["name"], args, anio=a, competencia=comp)) for p in e["params"] if p["in"] == "path"]
                muestra = out / "05_muestras" / (e["nombre"] + "__" + "_".join(usados) + ".json")
                try:
                    if muestra.exists() and not args.refrescar:
                        class _R:  # respuesta simulada desde cache
                            status_code = 200
                            content = muestra.read_bytes()
                            def json(self): return json.loads(self.content)
                        resp, fila["desde_cache"] = _R(), True
                    else:
                        resp = s.get(url, timeout=args.timeout)
                        time.sleep(args.sleep)
                    fila["status"] = resp.status_code
                    fila["bytes"] = len(resp.content)
                    fila["tipo"], fila["n_registros"], fila["campos"], fila["primer_registro"] = resumir_respuesta(resp)
                    if resp.status_code == 200 and not fila["desde_cache"]:
                        muestra.write_bytes(resp.content)
                    elif resp.status_code != 200:
                        fila["error"] = (fila["error"] + " " + getattr(resp, "text", "")[:200]).strip()
                except Exception as ex:   # red, timeout, SSL...
                    fila["error"] = f"{type(ex).__name__}: {ex}"[:300]
                estado = fila["status"] or "ERR"
                cache_info = "(cache) " if fila["desde_cache"] else ""
                print(f"[{i}/{total_iter}] {estado} {e['nombre']} ({comp} {a}) {cache_info}registros={fila['n_registros']}  {fila['error'][:80]}")
                filas.append(fila)

    with open(out / "03_pruebas_api.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader(); w.writerows(filas)
    print(f"\nListo. Resultados en {out}/  (01_endpoints.csv, 02_parametros.csv, 03_pruebas_api.csv, 05_muestras/)")


if __name__ == "__main__":
    main()

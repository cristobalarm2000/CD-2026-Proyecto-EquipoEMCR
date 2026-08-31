"""
Visor de estadísticas del Poder Judicial de Chile.

Uso rápido (Windows, con el lanzador de Python "py"):

    py app.py listar
    py app.py consultar --endpoint ingresos_rol_competencia --competencia Civil --anio 2025
    py app.py dashboard --anio 2025 --abrir
    py app.py descargar --anio 2025

Comandos:
  listar      Muestra endpoints, cortes y competencias disponibles.
  consultar   Consulta un endpoint y muestra la tabla (opcional: --csv archivo).
  dashboard   Descarga un resumen del año y genera dashboard.html (gráficos).
  descargar   Guarda todos los endpoints del año como CSV en datos/<anio>/.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

from pjud_api import (
    ANIO_MINIMO,
    COMPETENCIAS,
    CORTES,
    ENDPOINTS,
    PJUDClient,
    PJUDError,
    nombre_corte,
)

# En Windows la consola no siempre usa UTF-8; forzamos para no romper acentos.
try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except Exception:
    pass

RAIZ = Path(__file__).resolve().parent
ANIO_ACTUAL = datetime.now().year


# ---------------------------------------------------------------------------
# Utilidades de salida
# ---------------------------------------------------------------------------
def imprimir_tabla(datos: list[dict], titulo: str = "") -> None:
    if titulo:
        print(f"\n{titulo}")
    if not datos:
        print("  (sin datos publicados para esta combinación)")
        return
    ancho = max((len(str(d["key"])) for d in datos), default=10)
    total = 0.0
    for d in sorted(datos, key=lambda x: float(x.get("value", 0) or 0), reverse=True):
        val = float(d.get("value", 0) or 0)
        total += val
        print(f"  {str(d['key']):<{ancho}}  {val:>15,.1f}")
    print(f"  {'-' * ancho}  {'-' * 15}")
    print(f"  {'TOTAL':<{ancho}}  {total:>15,.1f}")


def guardar_csv(datos: list[dict], ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["key", "value"])
        for d in datos:
            w.writerow([d.get("key", ""), d.get("value", "")])


# ---------------------------------------------------------------------------
# Comandos
# ---------------------------------------------------------------------------
def cmd_listar(_args) -> None:
    print("ENDPOINTS (agregar '_detalle' para el desglose por tribunal):")
    for nombre, desc in ENDPOINTS.items():
        print(f"  {nombre:<34} {desc}")
    print("\nCOMPETENCIAS:", ", ".join(COMPETENCIAS),
          "\n  (en los endpoints *_detalle: Penal se divide en 'Garantia' y 'Top')")
    print("\nCORTES (código = valor de --corte; 0 = todo el país):")
    for cod, glosa in CORTES.items():
        print(f"  {cod:>3}  {glosa}")
    print(f"\nAÑOS: desde {ANIO_MINIMO} en adelante (el año en curso solo cuando el PJUD lo habilita).")


def cmd_consultar(args) -> None:
    client = PJUDClient()
    datos = client.consultar(
        args.endpoint, corte=args.corte, tribunal=args.tribunal,
        competencia=args.competencia, anio=args.anio,
    )
    titulo = (f"{ENDPOINTS.get(args.endpoint, args.endpoint)} | "
              f"{args.competencia} | {nombre_corte(args.corte)} | año {args.anio}")
    imprimir_tabla(datos, titulo)
    if args.csv:
        ruta = Path(args.csv)
        guardar_csv(datos, ruta)
        print(f"\nCSV guardado en: {ruta.resolve()}")


def cmd_descargar(args) -> None:
    client = PJUDClient()
    destino = RAIZ / "datos" / str(args.anio)
    endpoints = list(ENDPOINTS)
    if args.detalle:
        endpoints += [f"{e}_detalle" for e in ENDPOINTS]
    total_archivos = 0
    for ep in endpoints:
        for comp in COMPETENCIAS:
            try:
                datos = client.consultar(ep, corte=args.corte, tribunal=args.tribunal,
                                         competencia=comp, anio=args.anio)
            except PJUDError as exc:
                print(f"  [!] {ep} / {comp}: {exc}")
                continue
            estado = f"{len(datos):>4} filas" if datos else "  sin datos"
            print(f"  {ep:<40} {comp:<10} {estado}")
            if datos:
                guardar_csv(datos, destino / f"{ep}__{comp}.csv")
                total_archivos += 1
    print(f"\n{total_archivos} archivo(s) CSV en: {destino.resolve()}")


def cmd_dashboard(args) -> None:
    client = PJUDClient()
    print(f"Descargando resumen del Poder Judicial para el año {args.anio} "
          f"({nombre_corte(args.corte)})...\n")

    secciones = []
    datos_dir = RAIZ / "datos" / str(args.anio)
    for ep, desc in ENDPOINTS.items():
        series = {}
        for comp in COMPETENCIAS:
            try:
                datos = client.consultar(ep, corte=args.corte, tribunal=args.tribunal,
                                         competencia=comp, anio=args.anio)
            except PJUDError as exc:
                print(f"  [!] {ep} / {comp}: {exc}")
                datos = []
            if datos:
                datos = sorted(datos, key=lambda x: float(x.get("value", 0) or 0),
                               reverse=True)
                series[comp] = datos
                guardar_csv(datos, datos_dir / f"{ep}__{comp}.csv")
            print(f"  {ep:<40} {comp:<10} {len(datos):>4} filas")
        if series:
            secciones.append({"endpoint": ep, "titulo": desc, "series": series})

    if not secciones:
        print("\nNo hay datos publicados todavía para ese año. Prueba con un año anterior "
              "(por ejemplo --anio 2024).")
        return

    salida = RAIZ / (args.salida or f"dashboard_{args.anio}.html")
    _escribir_dashboard(salida, args.anio, args.corte, args.tribunal, secciones)
    print(f"\nDashboard generado: {salida.resolve()}")
    print(f"CSV de respaldo en:  {datos_dir.resolve()}")
    if args.abrir:
        webbrowser.open(salida.resolve().as_uri())


# ---------------------------------------------------------------------------
# Generación del dashboard HTML (gráficos con Chart.js desde CDN)
# ---------------------------------------------------------------------------
def _escribir_dashboard(ruta: Path, anio: int, corte: int, tribunal: int,
                        secciones: list[dict]) -> None:
    payload = {
        "anio": anio,
        "corte": nombre_corte(corte),
        "tribunal": "Todos" if int(tribunal) == 0 else str(tribunal),
        "generado": datetime.now().strftime("%d-%m-%Y %H:%M"),
        "secciones": secciones,
    }
    html = _PLANTILLA.replace("__DATOS_JSON__", json.dumps(payload, ensure_ascii=False))
    ruta.write_text(html, encoding="utf-8")


_PLANTILLA = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Poder Judicial de Chile — Estadísticas</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.3/chart.umd.min.js"></script>
<style>
  :root { color-scheme: light dark; }
  * { box-sizing: border-box; }
  body { margin: 0; font: 15px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
         background: #f4f5f7; color: #1c1f23; }
  header { background: #1b3a5b; color: #fff; padding: 22px 28px; }
  header h1 { margin: 0 0 4px; font-size: 20px; }
  header p { margin: 0; opacity: .85; font-size: 13px; }
  main { padding: 20px 28px 60px; max-width: 1200px; margin: 0 auto; }
  .kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
          gap: 14px; margin: 22px 0 30px; }
  .kpi { background: #fff; border: 1px solid #e2e5ea; border-radius: 10px; padding: 16px 18px; }
  .kpi b { display: block; font-size: 24px; margin-top: 4px; }
  .kpi span { font-size: 12px; text-transform: uppercase; letter-spacing: .04em; color: #5b6470; }
  section { margin-bottom: 38px; }
  section > h2 { font-size: 17px; border-left: 4px solid #1b3a5b; padding-left: 10px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 18px; }
  .card { background: #fff; border: 1px solid #e2e5ea; border-radius: 10px; padding: 14px 16px; }
  .card h3 { margin: 0 0 6px; font-size: 14px; }
  .card .sub { font-size: 12px; color: #5b6470; margin-bottom: 10px; }
  .wrap { position: relative; height: 320px; }
  details { margin-top: 10px; font-size: 13px; }
  details table { width: 100%; border-collapse: collapse; margin-top: 6px; }
  details td { padding: 3px 6px; border-bottom: 1px solid #eee; }
  details td:last-child { text-align: right; font-variant-numeric: tabular-nums; }
  footer { max-width: 1200px; margin: 0 auto; padding: 0 28px 40px; font-size: 12px; color: #5b6470; }
  @media (prefers-color-scheme: dark) {
    body { background: #14171a; color: #e7e9ec; }
    .kpi, .card { background: #1e2226; border-color: #2c3238; }
    .kpi span, .card .sub, footer { color: #97a0ac; }
    details td { border-color: #2c3238; }
  }
</style>
</head>
<body>
<header>
  <h1>Estadísticas del Poder Judicial de Chile</h1>
  <p id="meta"></p>
</header>
<div class="kpis" id="kpis" style="max-width:1200px;margin:0 auto;padding:0 28px"></div>
<main id="contenido"></main>
<footer>
  Fuente: <a href="https://estadisticaservices.pjud.cl">estadisticaservices.pjud.cl</a> ·
  Datos obtenidos desde la API pública de estadísticas. Los valores de "duración" están
  expresados en las unidades que entrega el servicio (días para causas, minutos para audiencias).
</footer>
<script>
const DATOS = __DATOS_JSON__;
const PALETA = ["#1b3a5b","#2e7d5b","#b5651d","#7a4fa3","#c62828","#00796b","#455a64"];
const nf = new Intl.NumberFormat("es-CL", { maximumFractionDigits: 1 });

document.getElementById("meta").textContent =
  `Año ${DATOS.anio}  ·  ${DATOS.corte}  ·  Tribunal: ${DATOS.tribunal}  ·  generado ${DATOS.generado}`;

function suma(serie){ return serie.reduce((a,d)=> a + (Number(d.value)||0), 0); }
function buscarSerie(endpoint, comp){
  const s = DATOS.secciones.find(x => x.endpoint === endpoint);
  return s && s.series[comp] ? s.series[comp] : null;
}

/* ---- KPIs ---- */
const kpis = [];
const ingRol = DATOS.secciones.find(s => s.endpoint === "ingresos_rol_competencia");
const terRol = DATOS.secciones.find(s => s.endpoint === "terminos_rol_competencia");
const tram   = DATOS.secciones.find(s => s.endpoint === "causas_tramitacion_competencia");
function totalSeccion(sec){
  if(!sec) return null;
  return Object.values(sec.series).reduce((a, serie) => a + suma(serie), 0);
}
const tIng = totalSeccion(ingRol), tTer = totalSeccion(terRol), tTra = totalSeccion(tram);
if(tIng!=null) kpis.push(["Ingresos totales", tIng]);
if(tTer!=null) kpis.push(["Términos totales", tTer]);
if(tTra!=null) kpis.push(["Causas en tramitación", tTra]);
if(ingRol) kpis.push(["Competencias con datos", Object.keys(ingRol.series).length]);
document.getElementById("kpis").innerHTML = kpis.map(
  ([k,v]) => `<div class="kpi"><span>${k}</span><b>${nf.format(v)}</b></div>`).join("");

/* ---- Secciones con gráficos ---- */
const cont = document.getElementById("contenido");
DATOS.secciones.forEach((sec, si) => {
  const el = document.createElement("section");
  el.innerHTML = `<h2>${sec.titulo}</h2><div class="grid"></div>`;
  const grid = el.querySelector(".grid");

  Object.entries(sec.series).forEach(([comp, serie], ci) => {
    const top = serie.slice(0, 15);
    const card = document.createElement("div");
    card.className = "card";
    const cid = `c_${si}_${ci}`;
    const filas = serie.map(d => `<tr><td>${d.key}</td><td>${nf.format(d.value)}</td></tr>`).join("");
    card.innerHTML =
      `<h3>${comp}</h3>` +
      `<div class="sub">Total: ${nf.format(suma(serie))} · ${serie.length} categorías` +
      (serie.length > 15 ? " (se grafican las 15 mayores)" : "") + `</div>` +
      `<div class="wrap"><canvas id="${cid}"></canvas></div>` +
      `<details><summary>Ver tabla completa</summary><table>${filas}</table></details>`;
    grid.appendChild(card);

    new Chart(document.getElementById(cid), {
      type: "bar",
      data: {
        labels: top.map(d => d.key),
        datasets: [{
          label: comp,
          data: top.map(d => Number(d.value) || 0),
          backgroundColor: PALETA[(si + ci) % PALETA.length],
        }],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false },
                   tooltip: { callbacks: { label: c => nf.format(c.parsed.x) } } },
        scales: { x: { ticks: { callback: v => nf.format(v) } },
                  y: { ticks: { autoSkip: false, font: { size: 11 } } } },
      },
    });
  });
  cont.appendChild(el);
});
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
def construir_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Visor de estadísticas del Poder Judicial de Chile (API pública).")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("listar", help="Muestra endpoints, cortes y competencias.")

    c = sub.add_parser("consultar", help="Consulta un endpoint y muestra la tabla.")
    c.add_argument("--endpoint", required=True, choices=list(ENDPOINTS)
                   + [f"{e}_detalle" for e in ENDPOINTS])
    c.add_argument("--corte", type=int, default=0)
    c.add_argument("--tribunal", type=int, default=0)
    c.add_argument("--competencia", default="Civil")
    c.add_argument("--anio", type=int, default=2025)
    c.add_argument("--csv", help="Ruta de archivo CSV donde guardar el resultado.")

    d = sub.add_parser("dashboard", help="Genera dashboard HTML con gráficos del año.")
    d.add_argument("--anio", type=int, default=2025)
    d.add_argument("--corte", type=int, default=0)
    d.add_argument("--tribunal", type=int, default=0)
    d.add_argument("--salida", help="Nombre del archivo HTML de salida.")
    d.add_argument("--abrir", action="store_true", help="Abrir el HTML en el navegador.")

    g = sub.add_parser("descargar", help="Guarda todos los endpoints del año como CSV.")
    g.add_argument("--anio", type=int, default=2025)
    g.add_argument("--corte", type=int, default=0)
    g.add_argument("--tribunal", type=int, default=0)
    g.add_argument("--detalle", action="store_true",
                   help="Incluir también los endpoints *_detalle (respuestas grandes).")
    return p


def main(argv: list[str] | None = None) -> int:
    args = construir_parser().parse_args(argv)
    try:
        {
            "listar": cmd_listar,
            "consultar": cmd_consultar,
            "dashboard": cmd_dashboard,
            "descargar": cmd_descargar,
        }[args.cmd](args)
    except PJUDError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrumpido.", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

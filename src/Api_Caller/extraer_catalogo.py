#!/usr/bin/env python3
"""Extrae el catálogo de cortes y tribunales del PDF 'Documento de Uso de APIs' (PJUD, 20/04/2021).
Uso: python extraer_catalogo.py usoapis.pdf [carpeta_salida]
Requiere poppler (pdftotext)."""
import subprocess, re, csv, sys, collections, pathlib

pdf = sys.argv[1]
out = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else ".")
out.mkdir(parents=True, exist_ok=True)

txt = subprocess.run(["pdftotext", "-layout", "-f", "3", "-l", "28", pdf, "-"],
                     capture_output=True, text=True, check=True).stdout
lines = txt.replace("\f", "\n").splitlines()

# --- Cortes (página 3)
cortes = {}
for l in lines:
    m = re.match(r"^\s+(\d+)\s{2,}(Todo el País|C\.A\. de [^\d]+?)\s*$", l)
    if m and len(cortes) < 18 and int(m.group(1)) not in cortes:
        cortes[int(m.group(1))] = m.group(2).strip()

# --- Tribunales por competencia (páginas 4-27)
SECCIONES = ["Civil", "Cobranza", "Familia", "Penal", "Laboral"]
CORTE_WRAP = {"Antofagasta", "Montt", "Arenas"}   # 2ª línea de "C.A. de Antofagasta/Puerto Montt/Punta Arenas"
rowre = re.compile(r"^\s*(\d+)\s+(C\.A\. de [^\d]*?)\s{2,}(\d+)\s{2,}(\S.*?)\s*$")
cur, rows, started, last = None, [], False, None
for l in lines:
    s = l.strip()
    if not s: continue
    if s == "Tribunal": started = True; continue
    if not started: continue
    if s.startswith("3. Valores variables"): break
    if s in SECCIONES and len(l) - len(l.lstrip()) < 15:
        cur, last = s, None; continue
    if s.startswith(("SubDepto.", "Página")) or re.match(r"^CORTE\s+GLOSA", s): continue
    m = rowre.match(l)
    if m:
        last = [cur, int(m.group(1)), int(m.group(3)), m.group(4)]; rows.append(last); continue
    if last is not None and not re.match(r"^\d", s):
        segs = [x for x in re.split(r"\s{2,}", s) if x]
        if segs and segs[0] in CORTE_WRAP: segs = segs[1:]
        if segs: last[3] += " " + " ".join(segs)

# --- Validaciones (si algo falla, se detiene en vez de seguir con datos malos)
assert len(cortes) == 18, f"se esperaban 18 cortes, hay {len(cortes)}"
assert all(r[0] for r in rows), "fila sin competencia"
assert all(r[1] in cortes for r in rows), "corte inexistente en el catálogo"
dups = [k for k, v in collections.Counter((r[0], r[1], r[2]) for r in rows).items() if v > 1]
assert not dups, f"duplicados: {dups[:3]}"
assert not [r for r in rows if re.search(r"\s{2,}|\b(de|del|la|y)$", r[3])], "glosa sospechosa (truncada o con espacios)"

with open(out / "cortes.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["corte", "glosa_corte"]); w.writerows(cortes.items())
with open(out / "tribunales.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["competencia_pdf", "corte", "glosa_corte", "tribunal", "glosa_tribunal"])
    for c, co, t, g in rows: w.writerow([c, co, cortes[co], t, g])

print(f"cortes: {len(cortes)} | filas tribunal-competencia: {len(rows)} | tribunales únicos: {len({r[2] for r in rows})}")
print(dict(collections.Counter(r[0] for r in rows)))

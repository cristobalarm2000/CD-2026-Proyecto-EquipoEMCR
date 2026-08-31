# Predicción de demanda en Tribunales de Familia — Región de Valparaíso

**CD 2026 · Equipo EMCR**

**Integrantes:**
* Cristóbal Rojas
* Emanuel Herrera
* Nicholas Espinoza
* Bastián Suárez

> El enunciado original del Taller 01 quedó archivado en
> [`README_TALLER01.md`](README_TALLER01.md).

---

## Objetivo

Modelar la **demanda** de los Juzgados de Familia de la **Región de Valparaíso**
(Corte de Apelaciones de Valparaíso, código **30**): cuántas causas ingresan y
cuántas terminan por mes, cuánto tardan en terminar y cuántas quedan en
tramitación. El insumo son los datos abiertos del Poder Judicial de Chile.

## Estado actual

- [x] **Extracción de datos 2022–2024** (Ingresos, Términos, Inventario,
      Duración y Audiencias de la materia Familia, a nivel nacional).
- [ ] Construcción del panel `tribunal × mes` filtrado a la Corte 30.
- [ ] EDA y modelos (demanda y duración).

---

## 1. De dónde salen los datos

Todo viene de `https://estadisticaservices.pjud.cl` (público, sin autenticación).
Hay **dos APIs**. Referencia detallada en [`docs/API_PJUD.md`](docs/API_PJUD.md) y
en el documento oficial [`docs/usoapis.pdf`](docs/usoapis.pdf).

### 1.1 API agregada — `/pjen/…`

Series ya totalizadas. Útil para las series mensuales rápidas.

```
GET /pjen/<endpoint>/<corte>/<tribunal>/<competencia>/<anio>
→ [ { "key": "<texto>", "value": <número> }, ... ]
```

| parámetro | valor para este proyecto |
|---|---|
| `corte` | **30** (C.A. de Valparaíso); `0` = todo el país |
| `tribunal` | `0` (todos) |
| `competencia` | `Familia` |
| `anio` | 2015 en adelante |

Endpoints usados: `ingresos_rol_competencia`, `ingresos_materia_competencia`,
`terminos_rol_competencia`, `terminos_materia_competencia`,
`causas_tramitacion_competencia`, `duracion_causas_competencia`,
`audiencias_realizadas_competencia`, `duracion_audiencias_competencia`
(cada uno con su variante `*_detalle` = desglose por tribunal).

**Conexión:** `src/pjud_api.py` expone la clase `PJUDClient` (sesión `requests`
con reintentos y timeout). CLI en `src/app.py`:

```bash
python src/app.py consultar --endpoint ingresos_rol_competencia \
    --competencia Familia --corte 30 --anio 2024
python src/app.py descargar --anio 2024 --corte 30        # vuelca a CSV
```

### 1.2 API de descargas fila-a-fila — `/descargas/…`

Bases con **una fila por causa** (o por causa × materia). Es la fuente principal
del proyecto.

**Catálogo** de un año/competencia (qué datasets existen y su `LINK`):

```
GET /pjen/cifras_clave/descargas/familia/<anio>
```

**Archivo** (ZIP con CSV, separador `;`, UTF-8):

```
https://estadisticaservices.pjud.cl/descargas/descargas<LINK><anio>-CSV.zip
ej.: .../descargas/descargas/familia/Ingresos/Ingresos-2024-CSV.zip
```

Cada ZIP `-CSV` contiene:
- **`…-Rol.csv`** → 1 fila por causa (clave `CRR CAUSA`).
- **`…-Materia.csv`** → 1 fila por causa × materia (solo Ingresos y Términos).

Los archivos son **nacionales**; la Región de Valparaíso se obtiene filtrando
`COD. CORTE = 30`.

**Conexión / pipeline:**

```bash
# 1) descargar los ZIP -CSV (Ingresos, Terminos, Inventario, Duracion, Audiencias)
python src/descargar_pjud.py   --competencia familia --anios 2022 2023 2024
# 2) extraer a CSV con nombres limpios en data/raw/familia/csv/
python src/descomprimir_zips.py --entrada data/raw/familia
```

### 1.3 Qué se extrajo (2022–2024)

Carpeta `data/raw/familia/` (no versionada). 15 ZIP · ~0,26 GB comprimido ·
~2,4 GB en CSV.

| Dataset | archivos por año | clave | notas |
|---|---|---|---|
| `Ingresos-<año>` | `-Rol.csv`, `-Materia.csv` | `CRR CAUSA` | fecha, tribunal, forma de inicio, marca VIF |
| `Terminos-<año>` | `-Rol.csv`, `-Materia.csv` | `CRR CAUSA` | fecha ingreso y término, motivo de término |
| `Inventario-<año>` | 1 archivo (al 31-12) | `CRR CAUSA` | causas en tramitación, etapa, última diligencia |
| `Duracion-<año>` | 1 archivo | `CRR CAUSA` | `DURACIÓN CAUSA (DÍAS)` de las causas terminadas |
| `Audiencias-<año>` | `-Realizadas.csv` | `CRR AUD` / `CRR CAUSA` | tipo de audiencia y duración (minutos) como columna |

Inconsistencias entre años (a normalizar en el ETL): claves `CRR CAUSA` vs
`CRR IDCAUSA` vs `ID_CAUSA`; fechas `dd-mm-yy` vs `dd/mm/yyyy`; encabezados con
acentos rotos (mojibake). Ver `norm()` en `src/cruce_ingresos_terminos.py`.

---

## 2. Estructura del repositorio

```
├── data/
│   ├── raw/          # ZIP y CSV crudos de PJUD            (ignorado)
│   └── processed/    # panel mensual / parquet, Corte 30   (ignorado)
├── notebooks/        # EDA y modelado
├── reports/          # dashboards y figuras generadas      (ignorado)
├── src/
│   ├── pjud_api.py                # cliente de la API agregada (/pjen)
│   ├── app.py                     # CLI: consultar / descargar / dashboard
│   ├── descargar_pjud.py          # baja los ZIP -CSV por competencia y año
│   ├── descomprimir_zips.py       # extrae los ZIP a CSV con nombres limpios
│   └── cruce_ingresos_terminos.py # cruza ingresos vs términos por ID de causa
├── docs/
│   ├── API_PJUD.md                # referencia de ambas APIs
│   └── usoapis.pdf                # documento oficial de códigos
├── requirements.txt
└── README_TALLER01.md             # enunciado original archivado
```

Los **datos no se versionan** (`.gitignore`): se regeneran con los scripts de
`src/`. Solo se versiona código, documentación y notebooks.

## 3. Puesta en marcha

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements.txt

python src/descargar_pjud.py   --competencia familia --anios 2022 2023 2024
python src/descomprimir_zips.py --entrada data/raw/familia
```

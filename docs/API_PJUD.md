# APIs del Poder Judicial de Chile

Dos servicios públicos, ambos sin autenticación, en `https://estadisticaservices.pjud.cl`.
Ver también `docs/usoapis.pdf` (documento oficial de códigos de Corte, Tribunal,
competencias y años).

## 1. API agregada  `/pjen/…`

Patrón: `/pjen/<endpoint>/<corte>/<tribunal>/<competencia>/<anio>`
Respuesta: lista JSON de `{"key": <texto>, "value": <número>}`.

- `corte` (int): `0` = todo el país, o código de Corte de Apelaciones (10 Arica … 91 San Miguel). **Valparaíso = 30**.
- `tribunal` (int): `0` = todos, o código del tribunal.
- `competencia` (str, 1ª letra mayúscula): `Civil`, `Cobranza`, `Familia`, `Laboral`, `Penal`.
  En los endpoints `*_detalle`, `Penal` se divide en `Garantia` y `Top`.
- `anio` (int): desde 2015.

Endpoints (cada uno con su variante `<endpoint>_detalle` = desglose por tribunal):

| endpoint | contenido |
|---|---|
| `ingresos_rol_competencia` | ingresos por tipo de procedimiento |
| `ingresos_materia_competencia` | ingresos por materia |
| `terminos_rol_competencia` | términos por tipo de procedimiento |
| `terminos_materia_competencia` | términos por materia |
| `causas_tramitacion_competencia` | causas en tramitación |
| `duracion_causas_competencia` | duración de causas (días) |
| `audiencias_realizadas_competencia` | audiencias realizadas |
| `duracion_audiencias_competencia` | duración de audiencias |

Cliente: `src/pjud_api.py` (clase `PJUDClient`) y CLI `src/app.py`.

## 2. API de descargas fila-a-fila  `/descargas/…`

Catálogo de un año/competencia:

    GET /pjen/cifras_clave/descargas/<seccion>/<anio>
    (seccion = familia | penal | civil | cobranza | laboral)

Devuelve los datasets disponibles con su `LINK`, p. ej. `/familia/Ingresos/Ingresos-`.

Archivo:

    GET https://estadisticaservices.pjud.cl/descargas/descargas<LINK><anio>-CSV.zip
    ej: .../descargas/descargas/familia/Ingresos/Ingresos-2024-CSV.zip

Datasets: `Ingresos`, `Terminos`, `Inventario`, `Duracion`, `Audiencias`.
Los ZIP `-CSV` traen los CSV **"por Rol"** (1 fila por causa) y, para
Ingresos/Términos, también **"por Materia"** (1 fila por causa × materia).
También existe `-XLS` (≈4× más pesado; no usar).

Los archivos son **nacionales**: para la V Región se filtra por `COD. CORTE = 30`.

Scripts: `src/descargar_pjud.py` y `src/descomprimir_zips.py`.

## Notas de esquema (inconsistencias entre años)

- Clave de causa: `CRR CAUSA` (Familia), `CRR IDCAUSA` (Penal), `ID_CAUSA`.
- `RUC` = identificador único nacional de la causa (útil para re-cruzar).
- Fechas: unas en `dd-mm-yy`, otras en `dd/mm/yyyy`.
- Encabezados con acentos rotos (mojibake) → normalizar por palabra clave
  (ver `norm()` en `src/cruce_ingresos_terminos.py`).
- Audiencias: la duración de la audiencia (minutos) es una **columna** dentro
  del archivo *Audiencias Realizadas*, no un archivo aparte.

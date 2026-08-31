# Predicción de demanda en Tribunales de Familia — Región de Valparaíso

**CD 2026 · Equipo EMCR**

**Integrantes:**
* Cristóbal Rojas
* Emanuel Herrera
* Nicholas Espinoza

> El enunciado original del Taller 01 (propuestas individuales) quedó archivado en
> [`README_TALLER01.md`](README_TALLER01.md).

---

## 1. Problema

Los Juzgados de Familia concentran una carga muy alta y volátil (pensión de
alimentos, cuidado personal, relación directa y regular, violencia intrafamiliar,
medidas de protección). Cuando los **ingresos** superan de forma sostenida la
capacidad de **término**, crece el inventario de causas pendientes, se alargan las
duraciones y se saturan las agendas de audiencias.

**¿Quién decide?** La Corporación Administrativa del Poder Judicial (dotación,
creación de tribunales, salas), las Cortes de Apelaciones y los jueces
presidentes de cada tribunal (gestión de agenda).

**¿Qué impacto tendría resolverlo?** Anticipar la demanda permite dimensionar
dotación y agenda con semanas o meses de anticipación, reducir el atraso y
acortar la duración de las causas.

**Alcance:** materia **Familia**, **Corte de Apelaciones de Valparaíso
(código 30)**, período base **2022–2024** (ampliable a 2015+).

## 2. Preguntas analíticas

### P1 — Regresión / series de tiempo (demanda)
¿Cuántas causas de Familia **ingresarán** y cuántas **terminarán** por mes en cada
juzgado de la V Región durante los próximos 3–12 meses, dada la estacionalidad,
la tendencia y la carga reciente?
* **Objetivo:** nº de ingresos / nº de términos mensuales (conteo).
* **Predictores:** rezagos (1, 3, 12 meses), mes del año, inventario del mes
  anterior, audiencias realizadas, tribunal, tipo de causa.

### P2 — Análisis de supervivencia (duración)
¿Cuánto tardará una causa en **terminar** desde su ingreso, y qué probabilidad
tiene de seguir abierta a los N meses?
* **Objetivo:** tiempo ingreso→término (evento), con censura para las causas aún
  en tramitación.
* **Predictores:** materia, tipo de causa, tribunal, forma de inicio, marca VIF,
  nº de audiencias, carga del tribunal al ingresar.

### P3 — Clasificación (riesgo de atraso)
¿Qué causas tienen alta probabilidad de superar la duración objetivo (p. ej. 12
meses) o de quedar sin término dentro del año de ingreso?

## 3. Datos

Todo proviene de datos abiertos del Poder Judicial (ver [`docs/API_PJUD.md`](docs/API_PJUD.md)):

| Fuente | Uso |
|---|---|
| API agregada `/pjen/…` | series mensuales rápidas (ingresos, términos, duración, audiencias) por Corte 30 + Familia, 2015+ |
| Descargas fila-a-fila (`numeros.pjud.cl`) | `Ingresos`, `Terminos`, `Inventario`, `Duracion`, `Audiencias` 2022–2024, nacional → se filtra `COD. CORTE = 30` |

**Los datos NO se versionan** (ver `.gitignore`). Se regeneran con los scripts:

```bash
python src/descargar_pjud.py   --competencia familia --anios 2022 2023 2024
python src/descomprimir_zips.py --entrada data/raw/familia
```

## 4. Estructura del repo

```
├── data/
│   ├── raw/         # descargas y CSV crudos (ignorado)
│   └── processed/   # panel mensual / parquet filtrado a V Región (ignorado)
├── notebooks/       # EDA y modelado
├── reports/         # dashboards y figuras generadas (ignorado)
├── src/
│   ├── pjud_api.py               # cliente de la API agregada
│   ├── app.py                    # CLI: consultar / descargar / dashboard
│   ├── descargar_pjud.py         # baja los ZIP -CSV por competencia y año
│   ├── descomprimir_zips.py      # extrae los ZIP a CSV con nombres limpios
│   └── cruce_ingresos_terminos.py# cruza ingresos vs términos por ID de causa
├── docs/
│   ├── API_PJUD.md               # referencia de ambas APIs
│   └── usoapis.pdf               # documento oficial de códigos
└── README_TALLER01.md            # enunciado original archivado
```

## 5. Puesta en marcha

```bash
python -m venv .venv && .venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

Ejemplos:

```bash
# Serie agregada de ingresos de Familia en Valparaíso
python src/app.py consultar --endpoint ingresos_rol_competencia --competencia Familia --corte 30 --anio 2024

# Cruce ingreso↔término por ID, solo V Región, 2022-2024
python src/cruce_ingresos_terminos.py \
  --ingresos data/raw/familia/Ingresos-2022-CSV.zip data/raw/familia/Ingresos-2023-CSV.zip data/raw/familia/Ingresos-2024-CSV.zip \
  --terminos data/raw/familia/Terminos-2022-CSV.zip data/raw/familia/Terminos-2023-CSV.zip data/raw/familia/Terminos-2024-CSV.zip \
  --filtro-corte 30 --salida reports/cruce_familia_valparaiso
```

## 6. CRISP-DM

| Fase | En este proyecto |
|---|---|
| **Business Understanding** | Reducir el atraso en Familia (V Región): predecir ingresos/términos mensuales y la duración de las causas para dimensionar dotación y agenda. Métrica de éxito: MAPE < 15 % en la demanda mensual y c-index > 0,70 en el modelo de duración. |
| **Data Understanding** | API agregada + bases fila-a-fila de PJUD. Explorar estacionalidad, tendencia, quiebres (pandemia 2020, tribunales nuevos), calidad (mojibake, claves `CRR CAUSA`, formatos de fecha, multiplicidad por materia). |
| **Data Preparation** | Filtrar `COD. CORTE = 30`, deduplicar por ID, construir panel `tribunal × mes` (ingresos, términos, inventario, audiencias). Marcar censura para causas sin término. Guardar en `data/processed/` como Parquet. |
| **Modeling** | Demanda: SARIMA / Prophet y gradient boosting (LightGBM) con rezagos, modelo global jerárquico por tribunal. Duración: análisis de supervivencia (Cox, AFT, Random Survival Forest). |
| **Evaluation** | Validación temporal (*time series split*). Métricas: MAE/RMSE/MAPE (demanda), c-index / Brier (duración). Comparar tribunales y contra estándares (tasa de resolución ≈ 100 %). |
| **Deployment** | Dashboard (`reports/`) con proyección de demanda e inventario y simulación de capacidad ("¿cuántas salas para bajar la duración mediana en 2 meses?"). Reentrenamiento periódico al publicarse cada nuevo año. |

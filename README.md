# ⚖️ Inteligencia Judicial & Eficiencia Procesal (PJUD Chile)
### Plataforma de Business Intelligence & Analytics para Estudios de Abogados
> **Rama:** `Test_nacional` | **Alcance:** 17 Cortes de Apelaciones (Escala Nacional) | **Materia:** Familia (2015–2025)

---

## 📌 Contexto Estratégico del Proyecto

Este proyecto desarrolla una **plataforma integral de inteligencia de negocios (BI) y analítica judicial** basada en los microdatos públicos del **Poder Judicial de Chile (PJUD)**. En esta versión a **Escala Nacional** (`Test_nacional`), se replican y escalan exitosamente todos los procesos, pipelines y artefactos del MVP hacia la totalidad de las **17 Cortes de Apelaciones del país** en la competencia de **Familia** durante el período decenal completo (**2015–2025**).

- **Cliente Objetivo:** Estudios jurídicos, departamentos legales corporativos y abogados litigantes de todo Chile.
- **Propuesta de Valor:**
  - **Predictibilidad de Plazos y SLAs:** Predecir tiempos de espera de agendamiento y madurez de causas por juzgado y por corte para gestionar expectativas de clientes.
  - **Estrategia de Pricing y Costeo:** Medir la tasa de litigiosidad y riesgo de continuaciones de juicio para tarificar honorarios (tarifa plana vs recargo por audiencia).
  - **Capacidad de Sala y Time-Tracking:** Analizar la duración real en sala y la saturación semanal y horaria para evitar colisiones de comparecencia.
  - **Productividad Telemática:** Cuantificar el ahorro en traslados y viáticos mediante la comparecencia remota vía Zoom (Ley 21.226 / Ley 21.394).
- **Estado Actual (Consolidación Nacional en Familia):** Pipeline de datos, auditoría forense y dashboard ejecutivo 100% operativos sobre **3.526.516 audiencias** y **141 tribunales**, dejando la arquitectura lista para la expansión hacia materias Laboral, Penal y Civil.

---

## 📊 Cifras Clave del Despliegue Nacional

| Métrica / Dimensión | Alcance MVP Previo (Corte 30) | Alcance Nacional Actual (`Test_nacional`) |
| :--- | :--- | :--- |
| **Cobertura Jurisdiccional** | 1 Corte (Valparaíso) | **17 Cortes de Apelaciones (Todo Chile)** |
| **Tribunales Canónicos** | 15 juzgados (V Región) | **141 juzgados de Familia y mixtos** |
| **Audiencias Realizadas** | 466.178 filas | **3.526.516 filas (100% Familia)** |
| **Causas Judiciales Únicas** | 128.401 causas | **2.266.379 causas (`ID_CAUSA_RIT`)** |
| **Cruce Oficial Lote 2023** | 43.380 causas recuperadas | **350.149 causas recuperadas (100% match)** |
| **Inconsistencias Corregidas** | 22 casos ajustados | **401 casos de fechas ajustados** y 75 horas imputadas |
| **Artefacto Preparado (Parquet)** | 36 columnas (10,77 MB) | **36 columnas (82,52 MB, compresión Snappy)** |
| **Completitud de Datos** | 100,00% (0 nulos) | **100,00% (0 nulos en las 36 variables)** |

---

## 🚀 Arquitectura de la Plataforma Web (Streamlit)

La plataforma cuenta con una interfaz web interactiva multi-página desacoplada y orientada a roles directivos, litigantes y analistas:

```text
src/App/
├── Inicio.py                     # Portada institucional, métricas nacionales y roadmap
└── pages/
    ├── 1.- Ingesta de Datos.py    # Monitoreo de extracción REST desde la API judicial
    ├── 2.- Notebook ETL.py       # Réplica técnica del cuaderno de 7 fases con catálogos nacionales
    ├── 3.- Informe ETL.py        # Informe ejecutivo de hallazgos forenses y decisiones procesales (3.52M)
    └── 4.- Dashboard BI.py       # Tablero directivo con filtro dinámico por Corte y 5 vistas de negocio
```

### Módulos Principales de la Aplicación:
1. **`Inicio`**: Visión general, contexto institucional del Poder Judicial, métricas a nivel nacional (17 Cortes, 141 tribunales, 3.52M audiencias) y hoja de ruta de escalamiento multi-materia.
2. **`1.- Ingesta de Datos`**: Monitoreo y ejecución de llamadas hacia la API estadística del PJUD, descarga de lotes anuales y consolidación inicial.
3. **`2.- Notebook ETL`**: Publicación interactiva fiel del cuaderno [`01 ETL_audienciasparquet.ipynb`](notebooks/01%20ETL_audienciasparquet.ipynb), detallando cada una de las 7 fases del pipeline de datos con sus bloques de código, visualizaciones de nulos y verificación de tipos adaptadas al catálogo nacional de 141 tribunales.
4. **`3.- Informe ETL`**: Resumen ejecutivo interactivo estructurado en torno a los **hallazgos forenses y decisiones de negocio** a nivel nacional (rescate del lote 2023 con 350.149 causas, causa única `ID_CAUSA_RIT` con 2.266.379 procesos, eliminación legal de `FECHA_FIRMA`, imputación de audiencias inmediatas y tratamiento de outliers).
5. **`4.- Dashboard BI`**: Tablero directivo para estudios de abogados con filtros globales interactivos (**Cortes de Apelaciones**, tribunales en cascada, años, macro-materias y modalidad telemática) y 5 pestañas analíticas:
   * **⏱️ Tablero 1: SLAs y Predictibilidad de Plazos:** Benchmark por días hábiles de espera y segmentación de cuellos de botella por corte y juzgado.
   * **⚖️ Tablero 2: Litigiosidad y Riesgo de Costos:** Tasa de continuaciones, distribución de audiencias por causa (1,56 promedio) y diseño de estructuras tarifarias.
   * **🕒 Tablero 3: Capacidad de Sala y Time-Tracking:** Matriz de calor de saturación (Día $\times$ Franja horaria) y medianas de duración en sala.
   * **💻 Tablero 4: Transformación Digital y Virtualidad:** Evolución de la comparecencia remota por Zoom y ranking de adopción telemática a nivel nacional.
   * **📑 Tablero 5: Explorador de Microdatos:** Consulta filtrada y exportación en CSV.

---

## 🛠️ Resumen del Pipeline de Datos (ETL y Feature Engineering Nacional)

El pipeline procesa **3.526.516 registros de audiencias** a lo largo de 7 fases rigurosamente auditadas y sincronizadas entre el Jupyter Notebook, los reportes técnicos y la aplicación web:

| Fase del Pipeline | Hito Metodológico | Decisión y Transformación Clave |
| :--- | :--- | :--- |
| **1. Carga de Datos** | Ingesta de Parquet crudo | Consolidación de 11 períodos anuales de la API PJUD a nivel nacional (3.526.516 filas $\times$ 22 columnas). |
| **2. Auditoría Inicial** | Perfil de calidad exploratorio | Diagnóstico de missingness estructural y detección de inconsistencias categóricas e institucionales. |
| **3. Limpieza y Estandarización** | Saneamiento y canonización | **Rescate del Lote 2023:** Cruce relacional oficial con `audiencias_realizadas_2023.csv` por `ID_AUDIENCIA` (**350.149 registros rescatados al 100%**). Integración de catálogos canónicos de las **17 Cortes** y los **141 tribunales de Familia**. Creación de **`ID_CAUSA_RIT`** (**2.266.379 causas únicas**). |
| **4. Datos Faltantes** | Depuración y 100% completitud | **Anonimización y Depuración:** Eliminación de `RUC`, `ID_CAUSA`, `ID_AUDIENCIA` y **`FECHA_FIRMA`** (justificada por el principio de oralidad en Ley N° 19.968). **Imputación procesal:** 83.524 audiencias inmediatas imputadas con mismo día y espera `0` días; 75 imputaciones horarias con mediana de sala (18 min). **Resultado: 100,00% completitud (0 nulos)**. |
| **5. Valores Imposibles y Outliers** | Coherencia temporal | Corrección de 401 desfases administrativos en fechas (`FECHA_AUDIENCIA < FECHA_PROGRAMACION` $\rightarrow$ alineadas). **Decisión de Negocio:** No truncar plazos extremos por reflejar cuellos de botella procesales reales (peritajes DAM/SML y suspensiones). |
| **6. Feature Engineering** | Enriquecimiento para BI | Generación de **16 características analíticas derivadas** (calendario, lead times, time-tracking de sala, secuencias de litigiosidad de la causa, macro-materias y épocas normativas). |
| **7. Persistencia Definitiva** | Exportación del modelo | Generación de [`audiencias_preparadas_modelo.parquet`](data/processed/audiencias_preparadas_modelo.parquet) (**3.526.516 filas $\times$ 36 columnas**, 82,52 MB, 0 nulos). Carga en memoria en **~0,5 segundos**. |

---

## 📊 Matriz Comparativa: El Antes vs El Después del Dataset

| Dimensión Evaluada | Estado Original (API PJUD) | Modelo Preparado Final (Nacional EMCR) |
| :--- | :--- | :--- |
| **Estructura Tabular** | 22 columnas operativas crudas | **36 columnas analíticas especializadas** |
| **Completitud de Celdas** | Solo 12 variables completas (55%) | **36 de 36 variables 100,00% completas (0 nulos)** |
| **Volumen de Nulos** | > 10.000.000 celdas vacías (RUC 81% nulo, desfase 2023) | **0 valores nulos en todo el universo** |
| **Lote Crítico 2023** | Columnas desplazadas a la izquierda | **100% auténtico mediante cruce oficial PJUD (350.149 causas)** |
| **Identificación de Causas** | RIT relativo por tribunal con errores `--` | **Clave única `ID_CAUSA_RIT` (2.266.379 causas únicas)** |
| **Consistencia Cronológica** | 401 inversiones de fecha de programación | **100,00% coherencia temporal universal** |
| **Tamaño y Rendimiento** | > 5,5 GB en JSON crudo / 1,8 GB Parquet inicial | **82,52 MB en Parquet Snappy (carga en ~0,5 s)** |

---

## 📁 Estructura del Repositorio

```text
CD-2026-Proyecto-EquipoEMCR/
├── data/
│   ├── raw/                           # Datos brutos extraídos de la API y fuentes oficiales PJUD
│   │   ├── 05_muestras/               # JSONs anuales de respaldo
│   │   ├── excel_pjud/                # Reportes oficiales del Departamento de Estadísticas (2023, 2025)
│   │   └── parquet/                   # Parquet consolidado crudo nacional (3.52M registros)
│   └── processed/                     # Datasets procesados y listos para consumo
│       └── audiencias_preparadas_modelo.parquet   # ⭐ Artefacto final nacional enriquecido (36 cols, 0 nulos, 82.5 MB)
├── notebooks/
│   └── 01 ETL_audienciasparquet.ipynb # ⭐ Cuaderno interactivo nacional ejecutado de punta a punta
├── reports/
│   ├── 01_Ingesta_acotada.md          # Informe técnico de la extracción REST
│   └── 02_Auditoria_Calidad_Datos.md  # ⭐ Auditoría y bitácora de decisiones metodológicas
├── scratch/
│   └── run_full_pipeline_nacional.py  # Script de ejecución y benchmark automatizado del pipeline nacional
├── src/
│   ├── Api_Caller/                    # Conector hacia la API estadística del Poder Judicial y catálogos
│   │   ├── cortes.csv                 # Catálogo canónico oficial de 17 Cortes de Apelaciones
│   │   └── tribunales.csv             # Catálogo canónico oficial de tribunales de Chile
│   └── App/                           # Plataforma interactiva Streamlit
│       ├── Inicio.py                  # Portada y router de navegación multi-página
│       └── pages/
│           ├── 1.- Ingesta de Datos.py
│           ├── 2.- Notebook ETL.py
│           ├── 3.- Informe ETL.py
│           └── 4.- Dashboard BI.py
├── requirements.txt                   # Dependencias del proyecto
└── README.md                          # Este archivo
```

---

## 💻 Instalación y Despliegue Local

### 1. Clonar el Repositorio y Posicionarse en la Rama
```bash
git clone https://github.com/cristobalarm2000/CD-2026-Proyecto-EquipoEMCR.git
cd CD-2026-Proyecto-EquipoEMCR

# Asegurar estar en la rama de escala nacional
git checkout Test_nacional
```

### 2. Configurar Entorno e Instalar Dependencias
```bash
python -m venv .venv
# En Windows:
.venv\Scripts\activate
# En Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Ejecutar la Aplicación Web (Streamlit)
```bash
streamlit run src/App/Inicio.py
```
La aplicación se desplegará automáticamente en tu navegador en `http://localhost:8501`.

---

## 📑 Informes Técnicos de Referencia

Para consultar el sustento normativo detallado (Ley 19.968, Ley 21.226, Ley 21.394), el diccionario de variables y la bitácora metodológica completa:
* 📄 [`reports/01_Ingesta_acotada.md`](reports/01_Ingesta_acotada.md): Auditoría de la extracción REST vía API PJUD.
* 📄 [`reports/02_Auditoria_Calidad_Datos.md`](reports/02_Auditoria_Calidad_Datos.md): Auditoría forense exhaustiva, fundamentos jurídicos, resolución del lote 2023, justificación de eliminación de `FECHA_FIRMA` y diccionario de las 36 variables preparadas.

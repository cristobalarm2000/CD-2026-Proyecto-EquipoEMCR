# ⚖️ Inteligencia Judicial & Eficiencia Procesal (PJUD Chile)
### Plataforma de Business Intelligence & Analytics para Estudios de Abogados

---

## 📌 Contexto Estratégico del Proyecto

Este proyecto desarrolla una **plataforma integral de inteligencia de negocios (BI) y analítica judicial** basada en los microdatos públicos del **Poder Judicial de Chile (PJUD)**, focalizada en las **Audiencias Realizadas** de la jurisdicción de la **Corte de Apelaciones de Valparaíso (Código 30)** durante un decenio completo (**2015–2025**).

- **Cliente Objetivo:** Estudios jurídicos, departamentos legales corporativos y abogados litigantes.
- **Propuesta de Valor:**
  - **Predictibilidad de Plazos y SLAs:** Predecir tiempos de espera de agendamiento y madurez de causas por juzgado para gestionar expectativas de clientes.
  - **Estrategia de Pricing y Costeo:** Medir la tasa de litigiosidad y riesgo de continuaciones de juicio para tarificar honorarios (tarifa plana vs recargo por audiencia).
  - **Capacidad de Sala y Time-Tracking:** Analizar la duración real en sala y la saturación semanal y horaria para evitar colisiones de comparecencia.
  - **Productividad Telemática:** Cuantificar el ahorro en traslados y viáticos mediante la comparecencia remota (Ley 21.226 / 21.394).
- **Estado Actual (MVP Certificado en Familia):** Producto Mínimo Viable (MVP) 100% completado en la competencia de **Familia**, sentando la arquitectura y metodología para su escalamiento a materias Laboral, Penal y Civil.

---

## 🚀 Arquitectura de la Plataforma Web (Streamlit)

La plataforma cuenta con una interfaz web interactiva multi-página desacoplada y orientada a roles ejecutivos y técnicos:

```text
src/App/
├── Inicio.py                     # Portada institucional, navegación y alcance del MVP
└── pages/
    ├── 1.- Ingesta de Datos.py    # Monitoreo de extracción REST desde la API judicial
    ├── 2.- Notebook ETL.py       # Réplica técnica ejecutable del cuaderno de 7 fases (código y lints)
    ├── 3.- Informe ETL.py        # Informe interactivo ejecutivo de hallazgos forenses y decisiones procesales
    └── 4.- Dashboard BI.py       # Tablero analítico ejecutivo interactivo con 5 vistas de negocio (Plotly)
```

### Módulos Principales de la Aplicación:
1. **`Inicio`**: Visión general, contexto institucional del Poder Judicial y hoja de ruta de escalamiento multi-materia.
2. **`1.- Ingesta de Datos`**: Monitoreo y ejecución de llamadas hacia la API estadística del PJUD, descarga de lotes anuales y consolidación inicial.
3. **`2.- Notebook ETL`**: Publicación interactiva fiel del cuaderno [`01 ETL_audienciasparquet.ipynb`](notebooks/01%20ETL_audienciasparquet.ipynb), detallando cada una de las 7 fases del pipeline de datos con sus bloques de código, visualizaciones de nulos y verificación de tipos.
4. **`3.- Informe ETL`**: Resumen ejecutivo interactivo estructurado en torno a los **hallazgos forenses y decisiones de negocio** (rescate del lote 2023, causa única `ID_CAUSA_RIT`, eliminación legal de `FECHA_FIRMA`, imputación de audiencias inmediatas y tratamiento de outliers).
5. **`4.- Dashboard BI`**: Tablero directivo para estudios de abogados con filtros globales dinámicos (años, macro-materias, juzgados y modalidad telemática) y 5 pestañas analíticas:
   * **⏱️ Tablero 1: SLAs y Predictibilidad de Plazos:** Benchmark de los 15 juzgados por días hábiles de espera y segmentación de cuellos de botella.
   * **⚖️ Tablero 2: Litigiosidad y Riesgo de Costos:** Tasa de continuaciones, distribución de audiencias por causa y diseño de estructuras tarifarias.
   * **🕒 Tablero 3: Capacidad de Sala y Time-Tracking:** Matriz de calor de saturación (Día $\times$ Franja horaria) y medianas de duración en sala.
   * **💻 Tablero 4: Transformación Digital y Virtualidad:** Evolución de la comparecencia remota por Zoom y ranking de adopción por tribunal.
   * **📑 Tablero 5: Explorador de Microdatos:** Consulta filtrada y exportación en CSV.

---

## 🛠️ Resumen del Pipeline de Datos (ETL y Feature Engineering)

El pipeline procesa **466.178 registros de audiencias** a lo largo de 7 fases rigurosamente auditadas y sincronizadas entre el Jupyter Notebook, los reportes técnicos y la aplicación web:

| Fase del Pipeline | Hito Metodológico | Decisión y Transformación Clave |
| :--- | :--- | :--- |
| **1. Carga de Datos** | Ingesta de Parquet crudo | Consolidación de 11 períodos anuales de la API PJUD (466.178 filas $\times$ 20 columnas). |
| **2. Auditoría Inicial** | Perfil de calidad exploratorio | Diagnóstico de 1,3 millones de celdas vacías y detección de inconsistencias categóricas. |
| **3. Limpieza y Estandarización** | Saneamiento y canonización | **Rescate del Lote 2023:** Cruce relacional oficial con `audiencias_realizadas_2023.csv` por `ID_AUDIENCIA` (43.380 registros rescatados). Normalización de 15 juzgados canónicos y 12 materias. Creación de **`ID_CAUSA_RIT`** (280.795 causas únicas). |
| **4. Datos Faltantes** | Depuración y 100% completitud | **Anonimización y Depuración:** Eliminación de `RUC`, `ID_CAUSA`, `ID_AUDIENCIA` y **`FECHA_FIRMA`** (justificada por el principio de oralidad en Ley N° 19.968). **Imputación procesal:** 9.228 audiencias inmediatas imputadas con mismo día y espera `0` días. **Resultado: 100,00% completitud (0 nulos)**. |
| **5. Valores Imposibles y Outliers** | Coherencia temporal | Corrección de 22 desfases administrativos en fechas (`FECHA_AUDIENCIA < FECHA_PROGRAMACION` $\rightarrow$ alineadas). **Decisión de Negocio:** No truncar plazos extremos (hasta 339 días hábiles) por reflejar cuellos de botella procesales reales (peritajes DAM/SML y suspensiones). |
| **6. Feature Engineering** | Enriquecimiento para BI | Generación de **16 características analíticas derivadas** (calendario, lead times, time-tracking de sala, secuencia de causa y macro-materias). |
| **7. Persistencia Definitiva** | Exportación del modelo | Generación de [`audiencias_preparadas_modelo.parquet`](data/processed/audiencias_preparadas_modelo.parquet) (**466.178 filas $\times$ 36 columnas**, 10,77 MB, 0 nulos). Carga en memoria en **0,13 segundos**. |

---

## 📊 Matriz Comparativa: El Antes vs El Después del Dataset

| Dimensión Evaluada | Estado Original (API PJUD) | Modelo Preparado Final (EMCR) |
| :--- | :--- | :--- |
| **Estructura Tabular** | 20 columnas operativas crudas | **36 columnas analíticas especializadas** |
| **Completitud de Celdas** | Solo 12 variables completas (60%) | **36 de 36 variables 100,00% completas (0 nulos)** |
| **Volumen de Nulos** | > 1.300.000 celdas vacías (RUC 81% nulo) | **0 valores nulos en todo el universo** |
| **Lote Crítico 2023** | Columnas corridas a la izquierda | **100% auténtico mediante cruce oficial PJUD** |
| **Identificación de Causas** | RIT relativo con 41.439 errores `--` | **Clave única `ID_CAUSA_RIT` (280.795 causas)** |
| **Consistencia Cronológica** | 22 inversiones de fecha | **100,00% coherencia temporal universal** |
| **Tamaño y Rendimiento** | > 700 MB en JSON crudo | **10,77 MB en Parquet Snappy (carga en 0,13 s)** |

---

## 📁 Estructura del Repositorio

```text
CD-2026-Proyecto-EquipoEMCR/
├── data/
│   ├── raw/                           # Datos brutos extraídos de la API y fuentes oficiales PJUD
│   │   ├── 05_muestras/               # JSONs crudos por año (2015–2025)
│   │   ├── excel_pjud/                # Reportes consolidados oficiales (2023, 2025)
│   │   └── parquet/                   # Parquet consolidado crudo original
│   └── processed/                     # Datasets procesados y listos para consumo
│       └── audiencias_preparadas_modelo.parquet   # ⭐ Artefacto final enriquecido (36 columnas, 0 nulos)
├── notebooks/
│   └── 01 ETL_audienciasparquet.ipynb # ⭐ Cuaderno interactivo de 7 fases ejecutado con NotebookClient
├── reports/
│   ├── 01_Ingesta_acotada.md          # Informe técnico de la extracción REST
│   └── 02_Auditoria_Calidad_Datos.md  # ⭐ Informe técnico exhaustivo de auditoría y decisiones (Secciones 1 a 10)
├── src/
│   ├── Api_Caller/                    # Conector hacia la API estadística del Poder Judicial
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

### 1. Clonar el Repositorio y Configurar Entorno
```bash
git clone https://github.com/.../CD-2026-Proyecto-EquipoEMCR.git
cd CD-2026-Proyecto-EquipoEMCR

# Crear y activar entorno virtual (opcional pero recomendado)
python -m venv .venv
# En Windows:
.venv\Scripts\activate
# En Linux/macOS:
source .venv/bin/activate
```

### 2. Instalar Dependencias
```bash
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

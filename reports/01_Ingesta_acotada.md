# Informe Técnico: Ingesta Acotada de Microdatos Judiciales
## Entidad de Estudio: Audiencias Realizadas (Competencia Familia)
**Jurisdicción:** Corte de Apelaciones de Valparaíso (Código 30)  
**Período Temporal:** 2015 – 2025 (11 períodos anuales completos)  
**Proyecto:** CD-2026-Proyecto-EquipoEMCR  
**Fecha de Emisión:** Octubre 2026  

---

## 1. Resumen Ejecutivo y Ficha Técnica

El presente documento detalla el proceso de **extracción, validación, tipificación estricta y consolidación columnar** de los microdatos estadísticos de **Audiencias Realizadas** provenientes de la API abierta del Poder Judicial de Chile (PJUD). 

Alineado con el nuevo enfoque analítico del proyecto, el pipeline se configuró de manera acotada y focalizada sobre una única entidad de negocio relevante: las audiencias celebradas ante los tribunales con competencia de Familia en la jurisdicción de Valparaíso a lo largo de una década.

| Parámetro | Detalle |
| :--- | :--- |
| **Entidad Analizada** | `audiencias_realizadas_competencia_detalle` |
| **Fuente de Datos** | API Oficial PJUD (`estadisticaservices.pjud.cl/pjen`) |
| **Jurisdicción** | Corte de Apelaciones de Valparaíso (Código `30`) |
| **Competencia** | `Familia` |
| **Tribunales Involucrados** | `34` tribunales en la región (Código `0` = Consolidado de la Corte) |
| **Horizonte Temporal** | `2015` a `2025` (11 años ininterrumpidos) |
| **Payload Crudo Total** | **250,513,579 bytes (~238.9 MB)** distribuidos en 11 archivos JSON |
| **Dataset Parquet Consolidado** | **8,084,393 bytes (7.71 MB)** con compresión Snappy |
| **Volumen de Registros** | **466,178 filas × 22 columnas** |
| **Tasa de Reducción de Espacio** | **96.77%** de ahorro de almacenamiento respecto al JSON crudo |

---

## 2. Arquitectura de Conexión a la API del PJUD

La conexión e ingesta automatizada se gestionó a través del cliente centralizado en [`src/Api_Caller/pjud_client.py`](../src/Api_Caller/pjud_client.py), estructurado bajo la clase `PJUDClient`.

### 2.1. Patrón de URL y Endpoint REST
El endpoint consultado responde a la especificación OpenAPI documentada en [`src/Api_Caller/swagger.json`](../src/Api_Caller/swagger.json):

```http
GET https://estadisticaservices.pjud.cl/pjen/audiencias_realizadas_competencia_detalle/{corte}/{tribunal}/{competencia}/{anio}
```

#### Parámetros de Ruta:
1. `{corte}` (Integer): Código institucional de la Corte de Apelaciones. Valor fijado: `30` (C.A. de Valparaíso).
2. `{tribunal}` (Integer): Código del tribunal específico o `0` para extraer el consolidado total de todos los tribunales adscritos a dicha Corte. Valor fijado: `0`.
3. `{competencia}` (String): Nombre canónico de la materia jurídica con mayúscula inicial. Valor fijado: `Familia`.
4. `{anio}` (Integer): Año calendario consultado. Rango parametrizado: `2015` al `2025`.

*Ejemplo de llamada concreta (Año 2023):*
```
https://estadisticaservices.pjud.cl/pjen/audiencias_realizadas_competencia_detalle/30/0/Familia/2023
```

### 2.2. Parámetros de Sesión y Resiliencia HTTP
Dada la sensibilidad y volumen del servidor judicial, se implementó una política de cliente robusta:
- **Pool de Conexiones:** `requests.Session()` con reutilización de conexiones TCP.
- **Estrategia de Reintentos:** Adaptador `HTTPAdapter` con `Retry` exponencial:
  - Total de reintentos: `3` intentos por petición fallida.
  - Factor de backoff: `1.5` segundos (`t = 1.5 * (2 ** (retry - 1))`).
  - Códigos HTTP con reintento automático: `429` (Rate limit), `500`, `502`, `503`, `504`.
- **Timeouts:** `60` segundos por petición.
- **Rate Limiting / Cortesía:** Pausa controlada de `0.5` segundos entre llamadas consecutivas (`time.sleep(0.5)`).
- **Encabezados HTTP (Headers):**
  - `User-Agent: PJUD-ApiCaller/2.0 (EquipoEMCR)`
  - `Accept: application/json`

---

## 3. Catálogo de Archivos JSON Crudos (`data/raw/05_muestras/`)

Cada respuesta exitosa (HTTP `200 OK`) fue persistida íntegramente en disco local bajo la convención estándar:  
`{endpoint}__{corte}_{tribunal}_{competencia}_{anio}.json`

### 3.1. Inventario Detallado de Descargas

| # | Archivo JSON Crudo | Año | Tamaño (Bytes) | Tamaño (MB) | Filas / Registros | Status HTTP |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| 1 | `audiencias_realizadas_competencia_detalle__30_0_Familia_2015.json` | 2015 | 23,563,357 | 22.47 MB | 44,827 | 200 OK |
| 2 | `audiencias_realizadas_competencia_detalle__30_0_Familia_2016.json` | 2016 | 22,572,777 | 21.53 MB | 42,948 | 200 OK |
| 3 | `audiencias_realizadas_competencia_detalle__30_0_Familia_2017.json` | 2017 | 22,489,553 | 21.45 MB | 42,572 | 200 OK |
| 4 | `audiencias_realizadas_competencia_detalle__30_0_Familia_2018.json` | 2018 | 22,554,922 | 21.51 MB | 43,260 | 200 OK |
| 5 | `audiencias_realizadas_competencia_detalle__30_0_Familia_2019.json` | 2019 | 22,933,995 | 21.87 MB | 43,450 | 200 OK |
| 6 | `audiencias_realizadas_competencia_detalle__30_0_Familia_2020.json` | 2020 | 16,045,450 | 15.30 MB | 31,080 | 200 OK |
| 7 | `audiencias_realizadas_competencia_detalle__30_0_Familia_2021.json` | 2021 | 23,000,278 | 21.93 MB | 42,462 | 200 OK |
| 8 | `audiencias_realizadas_competencia_detalle__30_0_Familia_2022.json` | 2022 | 23,836,654 | 22.73 MB | 43,378 | 200 OK |
| 9 | `audiencias_realizadas_competencia_detalle__30_0_Familia_2023.json` | 2023 | 24,189,958 | 23.07 MB | 43,380 | 200 OK |
| 10 | `audiencias_realizadas_competencia_detalle__30_0_Familia_2024.json` | 2024 | 25,177,421 | 24.01 MB | 44,750 | 200 OK |
| 11 | `audiencias_realizadas_competencia_detalle__30_0_Familia_2025.json` | 2025 | 24,149,214 | 23.03 MB | 44,071 | 200 OK |
| **Total** | **11 archivos consolidados** | **2015-2025** | **250,513,579** | **~238.9 MB** | **466,178** | **100% Exitoso** |

### 3.2. Estructura de un Registro Crudo en JSON
Cada elemento del array JSON contiene las siguientes llaves originales (tipadas como flotantes, cadenas o nulos):

```json
{
  "ID_AUDIENCIA": 899132.0,
  "ID_CAUSA": 9599244.0,
  "COD_CORTE": 30.0,
  "CORTE": "C.A. de Valparaíso",
  "COD_TRIBUNAL": 88.0,
  "TRIBUNAL": "Juzgado de Letras y Garantía de Petorca",
  "RIT": "21- 2-2384696-0",
  "TIPO_PROCEDIMIENTO": "X",
  "TIPO_AUDIENCIA": "Cumplimiento",
  "FECHA_INGRESO": "Inmediata",
  "FECHA_PROGRAMACION": "23-06-2021",
  "FECHA_FIRMA": "07-02-2023",
  "PLAZO_AGENDAMIENTO": 0.0,
  "HORA_INICIO": "11:35",
  "HORA_FIN": "11:58",
  "VIDEOCONFERENCIA": "SI",
  "ANO_AUDIENCIA": 2023.0,
  "COMPETENCIA": "Familia",
  "TOTAL_AUDIENCIAS": 1.0,
  "RUC": null
}
```

---

## 4. Pipeline de Consolidación y Tipado Fuerte

La transformación desde los 11 JSONs crudos hacia el Parquet consolidado ejecutó las siguientes 4 fases técnicas:

1. **Concatenación Vectorial con Inyección de Metadatos:**
   - Lectura iterativa mediante `pd.json_normalize()`.
   - Limpieza de prefijos de MongoDB (`_id.`).
   - Normalización de nombres de columnas a mayúsculas puras sin caracteres especiales mediante `norm_col()`.
   - Inyección garantizada de `COMPETENCIA = 'Familia'` y `ANO_PROCESO = anio`.

2. **Tipificación Temporal Robusta:**
   - Para las columnas de fecha (`FECHA_INGRESO`, `FECHA_PROGRAMACION`, `FECHA_AUDIENCIA`, `FECHA_FIRMA`), se implementó un parser con soporte de doble formato (`%Y-%m-%d` y `%d-%m-%Y`).
   - *Hallazgo crítico de tipado:* En la columna `FECHA_INGRESO`, los sistemas judiciales ingresan a veces el texto descriptivo `"Inmediata"`. El parser coerciona dichos textos no temporales a `NaT` de forma controlada, evitando errores de parada en el pipeline.

3. **Casteo Seguro de Identificadores y Enteros (`Int64`):**
   - Las columnas `COD_CORTE`, `COD_TRIBUNAL`, `ID_CAUSA`, `ID_AUDIENCIA` y `TOTAL_AUDIENCIAS` fueron convertidas a `Int64` de Pandas (soporte nativo de `pd.NA`), erradicando la representación flotante artificial (`30.0` $\rightarrow$ `30`).

4. **Persistencia Columnar Snappy:**
   - Exportación mediante el motor `pyarrow` con compresión `snappy` e índice no persistido (`index=False`).

---

## 5. Auditoría Técnica del Parquet Consolidado

**Archivo de Destino:** [`data/raw/parquet/audiencias_realizadas_competencia_detalle.parquet`](../data/raw/parquet/audiencias_realizadas_competencia_detalle.parquet)  
**Tamaño en Disco:** `8,084,393 bytes` (7.71 MB)  
**Registros Consolidados:** `466,178`  
**Dimensiones:** `(466178, 22)`

### 5.1. Diccionario de Datos y Análisis de Calidad de Columnas

| Variable / Columna | Tipo de Dato Parquet | Valores No Nulos | Valores Nulos | % Nulos | Descripción y Calidad de la Variable |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `COD_CORTE` | `Int64` | 466,178 | 0 | 0.00% | Código de la Corte de Apelaciones (100% igual a `30`). |
| `CORTE` | `str` | 466,178 | 0 | 0.00% | Glosa textual de la Corte (`C.A. de Valparaíso`). |
| `COD_TRIBUNAL` | `Int64` | 466,178 | 0 | 0.00% | Código único del juzgado (34 tribunales distintos). |
| `TRIBUNAL` | `str` | 466,178 | 0 | 0.00% | Nombre formal del juzgado que presidió la audiencia. |
| `RIT` | `str` | 466,178 | 0 | 0.00% | Rol Interno del Tribunal (identificador procesal). |
| `TIPO_PROCEDIMIENTO` | `str` | 466,178 | 0 | 0.00% | Procedimiento judicial (ej. Contenciosa, Medidas de Protección). |
| `TIPO_AUDIENCIA` | `str` | 466,178 | 0 | 0.00% | Clasificación procesal (Preparatoria, Juicio, Especial, etc.). |
| `FECHA_INGRESO` | `datetime64[ns]` | 422,798 | 43,380 | 9.31% | Fecha de ingreso de la causa al tribunal (nulos por `"Inmediata"`). |
| `FECHA_PROGRAMACION`| `datetime64[ns]` | 458,146 | 8,032 | 1.72% | Fecha en que se dictó la resolución de agendamiento. |
| `FECHA_AUDIENCIA` | `datetime64[ns]` | 464,982 | 1,196 | 0.26% | Fecha efectiva de celebración de la audiencia. |
| `PLAZO_AGENDAMIENTO` | `float64` | 466,081 | 97 | 0.02% | Días hábiles/corridos entre programación y realización. |
| `HORA_INICIO` | `str` | 466,178 | 0 | 0.00% | Hora de inicio registrada por el tribunal (`HH:MM`). |
| `HORA_FIN` | `str` | 466,176 | 2 | 0.00% | Hora de término de la sesión (`HH:MM`). |
| `ANO_AUDIENCIA` | `float64` | 466,178 | 0 | 0.00% | Año calendario de la fecha de audiencia. |
| `COMPETENCIA` | `str` | 466,178 | 0 | 0.00% | Materia jurídica (`Familia` en el 100% de los casos). |
| `TOTAL_AUDIENCIAS` | `Int64` | 466,178 | 0 | 0.00% | Conteo unitario de la sesión (`1` en todos los casos). |
| `ID_CAUSA` | `Int64` | 132,201 | 333,977 | 71.64% | Identificador interno de base de datos de la causa. |
| `RUC` | `str` | 44,071 | 422,107 | 90.55% | Rol Único de Causa (Ministerio Público / SITFA). |
| `ID_AUDIENCIA` | `Int64` | 175,579 | 290,599 | 62.34% | Identificador numérico de la audiencia en el sistema de origen. |
| `VIDEOCONFERENCIA` | `str` | 218,041 | 248,137 | 53.23% | Indicador de modalidad telemática (`SI`, `NO`, etc.). |
| `ANO_PROCESO` | `int64` | 466,178 | 0 | 0.00% | Año del lote de extracción de la API (`2015` a `2025`). |
| `FECHA_FIRMA` | `datetime64[ns]` | 173,970 | 292,208 | 62.68% | Fecha de firma electrónica del acta de la audiencia. |

---

## 6. Perfilado Inicial de la Entidad de Estudio

### 6.1. Evolución Temporal del Volumen Anual (`ANO_PROCESO`)
La serie histórica permite dimensionar la capacidad de respuesta del fuero de Familia en la Quinta Región:

```
  2015  ████████████████████████ 44,827
  2016  ███████████████████████  42,948
  2017  ███████████████████████  42,572
  2018  ███████████████████████  43,260
  2019  ███████████████████████  43,450
  2020  ████████████████         31,080  <-- Caída COVID-19 (-28.5%)
  2021  ███████████████████████  42,462  <-- Recuperación vía Zoom
  2022  ███████████████████████  43,378
  2023  ███████████████████████  43,380
  2024  ████████████████████████ 44,750
  2025  ███████████████████████  44,071
```

- **Estabilidad Operacional:** Entre 2015 y 2019 la tasa de audiencias se mantuvo sumamente estable, en torno a las 43,000 audiencias anuales.
- **Impacto de la Emergencia Sanitaria (2020):** Se registró una caída drástica del **28.5%** de audiencias celebradas (31,080 vs 43,450 de 2019) debido a la suspensión de términos y audiencias presenciales al inicio de la pandemia.
- **Resiliencia y Virtualidad (2021-2025):** Para 2021 el sistema se recuperó completamente a los niveles prepandemia (42,462 audiencias), impulsado por la habilitación legal de audiencias remotas vía Zoom/Videoconferencia.

### 6.2. Distribución Jurisdiccional: Top 10 Tribunales con Mayor Actividad
De los 34 tribunales de la Corte de Valparaíso, el volumen se concentra fuertemente en el eje urbano costero e interior:

| Posición | Tribunal | Total Audiencias (2015-2025) | % de Participación |
| :---: | :--- | :---: | :---: |
| 1 | **Juzgado de Familia Viña del Mar** | 72,520 | 15.56% |
| 2 | **Juzgado de Familia Valparaíso** | 51,088 | 10.96% |
| 3 | **Juzgado de Familia Los Andes** | 29,916 | 6.42% |
| 4 | **Juzgado de Familia Villa Alemana** | 29,688 | 6.37% |
| 5 | **Juzgado de Familia Quillota** | 27,403 | 5.88% |
| 6 | **Juzgado de Familia Quilpué** | 25,622 | 5.50% |
| 7 | **Juzgado de Familia San Felipe** | 24,057 | 5.16% |
| 8 | **Juzgado de Familia San Antonio** | 23,803 | 5.11% |
| 9 | **Juzgado de Letras y Garantía de La Calera** | 20,442 | 4.38% |
| 10 | **Juzgado de Familia Limache** | 19,819 | 4.25% |

Los primeros 5 tribunales concentran cerca del **45.2%** de todas las audiencias realizadas en la región.

### 6.3. Hallazgos Forenses para la Fase de EDA
La auditoría de este Parquet entrega insumos inmediatos para el Análisis Exploratorio de Datos (EDA):
1. **Unificación Semántica:** Existen discrepancias tipográficas en `TIPO_PROCEDIMIENTO` (`'Contenciosa'` vs `'CONTENCIOSA'`) y `TIPO_AUDIENCIA` (`'Audiencia Preparatoria'` vs `'AUDIENCIA PREPARATORIA'`) que requerirán normalización a mayúsculas o títulos homogéneos.
2. **Saneamiento de la Variable `VIDEOCONFERENCIA`:** 
   - Pre-2020: Presenta `NaN` en su totalidad porque la modalidad remota no existía como atributo en los registros estadísticos.
   - Post-2020: Presenta valores heterogéneos (`'SI'`, `'NO'`, `'0.0'`, `'1.0'`, `'0,0'`, `'1,0'`) que deben convertirse a booleano puro (`True` / `False`).
3. **Cálculo de Duración Efectiva:** Las variables `HORA_INICIO` y `HORA_FIN` permiten computar `DURACION_MINUTOS` y estudiar la dispersión real de tiempos por juez y tribunal.

---

## 7. Disponibilidad y Próximos Pasos

El pipeline de ingesta acotada se encuentra finalizado y verificado:
- **Datos Listos para Consumo:** El archivo `audiencias_realizadas_competencia_detalle.parquet` se encuentra depositado y validado en [`data/raw/parquet/`](../data/raw/parquet).
- **Interfaz Interactiva:** La aplicación Streamlit en [`src/App/`](../src/App) refleja en tiempo real las métricas y gráficos del fuero de Familia (2015-2025).
- **Próxima Fase:** Construcción del notebook integral de análisis exploratorio ([`notebooks/01_EDA_Audiencias_Realizadas.ipynb`](../notebooks)) para modelar la duración, tiempos de espera y el impacto de la virtualidad procesal.

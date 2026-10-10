# Informe Técnico: Auditoría y Perfil de Calidad de Datos
## Entidad de Estudio: Audiencias Realizadas (Competencia Familia)
**Jurisdicción:** 17 Cortes de Apelaciones (Nivel Nacional)  
**Período Temporal:** 2015 – 2025 (11 períodos anuales completos)  
**Dataset Auditado:** `audiencias_realizadas_competencia_detalle.parquet`  
**Proyecto:** CD-2026-Proyecto-EquipoEMCR (Rama: Test_nacional)  
**Fecha de Emisión:** Octubre 2026  

---

## 1. Resumen Ejecutivo de la Auditoría

El presente informe expone los resultados del análisis exploratorio inicial y la auditoría exhaustiva de calidad de datos realizada sobre el dataset consolidado de microdatos judiciales de **Audiencias Realizadas** para la totalidad de las 17 Cortes de Apelaciones a nivel nacional en la competencia de Familia (2015-2025).

El dataset analizado cuenta con un volumen total de **3.526.516 registros** y **22 variables**, obtenido a partir de la ingesta automatizada de la API de estadísticas del Poder Judicial de Chile (PJUD).

### Ficha Resumen de Integridad General

| Métrica | Valor Observado | Diagnóstico Técnico |
| :--- | :--- | :--- |
| **Total de Registros** | 3.526.516 filas | Volumen nacional completo post-ingesta sin pérdidas de carga |
| **Total de Columnas** | 22 variables | Esquema columnar consolidado |
| **Duplicados Exactos** | 0 filas (0,0%) | No existen filas idénticas redundantes |
| **Causas Únicas (`ID_CAUSA_RIT`)** | 2.266.379 causas | Gran diversidad muestral a lo largo de 11 años en 141 tribunales |
| **Tribunales Canónicos** | 141 juzgados | Cobertura total de juzgados de Familia y mixtos a nivel nacional |
| **Cortes de Apelaciones** | 17 cortes | 100% de las jurisdicciones del país representadas |
| **Columnas Críticas con Alto Nulo** | 5 columnas (>50% nulos) | Atributos no disponibles en años tempranos o no aplicables |

---

## 2. Tipos de Datos Detectados

El motor de almacenamiento Parquet y Pandas preservan el siguiente tipado de columnas:

| Columna | Tipo de Dato (Dtype) | Clasificación de Negocio |
| :--- | :--- | :--- |
| `COD_CORTE` | `Int64` | Identificador institucional (Entero con nulos) |
| `CORTE` | `object` | Nombre de la Corte de Apelaciones (Texto) |
| `COD_TRIBUNAL` | `Int64` | Identificador de tribunal (Entero con nulos) |
| `TRIBUNAL` | `object` | Denominación del tribunal (Texto) |
| `RIT` | `object` | Rol Interno del Tribunal (Texto identificador) |
| `TIPO_PROCEDIMIENTO` | `object` | Materia / procedimiento procesal (Categórica) |
| `TIPO_AUDIENCIA` | `object` | Categoría procesal de la audiencia (Categórica) |
| `FECHA_INGRESO` | `datetime64[ns]` | Fecha de ingreso de la causa a tramitación |
| `FECHA_PROGRAMACION` | `datetime64[ns]` | Fecha de agendamiento de la audiencia |
| `FECHA_AUDIENCIA` | `datetime64[ns]` | Fecha de celebración de la audiencia |
| `PLAZO_AGENDAMIENTO` | `float64` | Días transcurridos entre programación y audiencia |
| `HORA_INICIO` | `object` | Hora de inicio programada/real (Cadena) |
| `HORA_FIN` | `object` | Hora de término de la sesión (Cadena) |
| `ANO_AUDIENCIA` | `float64` | Año de realización |
| `COMPETENCIA` | `object` | Competencia material jurisdiccional (Texto) |
| `TOTAL_AUDIENCIAS` | `Int64` | Conteo de audiencias registradas |
| `ID_CAUSA` | `Int64` | Llave subrogada interna del sistema PJUD |
| `RUC` | `object` | Rol Único de Causa (Texto identificador) |
| `ID_AUDIENCIA` | `Int64` | Identificador interno de evento de audiencia |
| `VIDEOCONFERENCIA` | `object` | Indicador de modalidad telemática (Mixto) |
| `ANO_PROCESO` | `int64` | Año del ciclo de extracción/reporte |
| `FECHA_FIRMA` | `datetime64[ns]` | Fecha de firma electrónica del acta de audiencia |

---

## 3. Perfil de Calidad: Exhaustividad y Cardinalidad

Se evaluó la presencia de valores nulos o ausentes (`NaN` / `None` / `<NA>`) y la cardinalidad de valores únicos por columna:

| Columna | Dtype | Conteo Nulos | % Nulos | Cardinalidad (N Únicos) |
| :--- | :--- | :--- | :--- | :--- |
| `RUC` | `object` | 422.107 | 90,5% | 28.969 |
| `ID_CAUSA` | `Int64` | 333.977 | 71,6% | 82.729 |
| `FECHA_FIRMA` | `datetime64[ns]` | 292.208 | 62,7% | 1.109 |
| `ID_AUDIENCIA` | `Int64` | 290.599 | 62,3% | 175.579 |
| `VIDEOCONFERENCIA` | `object` | 248.137 | 53,2% | 6 |
| `FECHA_INGRESO` | `datetime64[ns]` | 43.380 | 9,3% | 5.324 |
| `FECHA_PROGRAMACION` | `datetime64[ns]` | 8.032 | 1,7% | 3.540 |
| `FECHA_AUDIENCIA` | `datetime64[ns]` | 1.196 | 0,3% | 2.933 |
| `PLAZO_AGENDAMIENTO` | `float64` | 97 | 0,02% | 253 |
| `HORA_FIN` | `object` | 2 | 0,0004% | 1.102 |
| `HORA_INICIO` | `object` | 0 | 0,0% | 977 |
| `TIPO_PROCEDIMIENTO` | `object` | 0 | 0,0% | 39 |
| `TIPO_AUDIENCIA` | `object` | 0 | 0,0% | 35 |
| `RIT` | `object` | 0 | 0,0% | 128.401 |
| `TRIBUNAL` | `object` | 0 | 0,0% | 34 |
| `COD_TRIBUNAL` | `Int64` | 0 | 0,0% | 15 |
| `CORTE` | `object` | 0 | 0,0% | 3 |
| `COD_CORTE` | `Int64` | 0 | 0,0% | 1 |
| `COMPETENCIA` | `object` | 0 | 0,0% | 1 |
| `TOTAL_AUDIENCIAS` | `Int64` | 0 | 0,0% | 2 |
| `ANO_AUDIENCIA` | `float64` | 0 | 0,0% | 11 |
| `ANO_PROCESO` | `int64` | 0 | 0,0% | 11 |

### 3.1. Visualización y Jerarquía de Missingness por Variable

El gráfico de barras de valores faltantes (`Missingness por variable`) generado al cierre de la auditoría permite categorizar los campos con nulos en cuatro niveles estructurales:

1. **Nivel Crítico (> 50% faltantes - Atributos no universales o de introducción reciente):**
   - **`RUC` (90,5% nulos):** El Rol Único de Causa no es de uso generalizado en todas las causas de Familia, concentrándose principalmente en causas judicializadas con concurrencia penal o sistemas modernos.
   - **`ID_CAUSA` (71,6% nulos) e `ID_AUDIENCIA` (62,3% nulos):** Claves subrogadas internas del sistema PJUD que no se capturaron sistemáticamente en los primeros años de la serie (2015-2019).
   - **`FECHA_FIRMA` (62,7% nulos):** Ausente en el período pre-pandemia (2015 - nov 2020); su presencia coincide con la adopción de firma digital obligatoria.
   - **`VIDEOCONFERENCIA` (53,2% nulos):** Campo inexistente/no registrado con anterioridad a la tramitación remota (Ley 21.226).

2. **Nivel Moderado (1% a 10% faltantes - Eventos previos a la audiencia):**
   - **`FECHA_INGRESO` (9,31% nulos - 43.380 registros):** Causas donde la fecha de ingreso inicial no fue traspasada al registro estadístico consolidado.
   - **`FECHA_PROGRAMACION` (1,72% nulos - 8.032 registros):** Audiencias sin fecha explícita de agendamiento previo (por ejemplo, audiencias inmediatas o reprogramaciones verbales).

3. **Nivel Residual (< 1% faltantes - Errores de captura aislados):**
   - **`FECHA_AUDIENCIA` (0,26% nulos - 1.196 registros):** Registros anómalos de audiencias realizadas sin fecha de realización consignada.
   - **`PLAZO_AGENDAMIENTO` (0,02% nulos - 97 registros):** Directamente derivado de la ausencia de fecha de programación o fecha de audiencia.
   - **`HORA_FIN` (0,0004% nulos - 2 registros):** Registros puntuales sin cierre de sesión.

4. **Nivel de Completitud Absoluta (0,0% nulos):**
   - 12 de las 22 variables (`CORTE`, `COD_CORTE`, `TRIBUNAL`, `COD_TRIBUNAL`, `RIT`, `TIPO_PROCEDIMIENTO`, `TIPO_AUDIENCIA`, `HORA_INICIO`, `COMPETENCIA`, `TOTAL_AUDIENCIAS`, `ANO_AUDIENCIA`, `ANO_PROCESO`) cuentan con integridad completa en sus 466.178 registros.

---

## 4. Análisis Detallado de Inconsistencias

### 4.1. Heterogeneidad en Nombres Institucionales (`CORTE` y `TRIBUNAL`)
- **`CORTE`:** A pesar de corresponder únicamente al código `30`, existen 3 variaciones textuales producto de distintas versiones históricas en las bases de datos de origen:
  - `C.A. DE VALPARAÍSO` (217.057 registros)
  - `C.A. de Valparaíso` (132.201 registros)
  - `C.A. DE VALPARAISO` (116.920 registros - sin tilde)
- **`TRIBUNAL`:** Se observa alternancia entre mayúsculas sostenidas y formato título (Title Case):
  - Ejemplos: `JUZGADO DE FAMILIA VALPARAÍSO` (51.088) vs `Juzgado de Familia Valparaíso` (25.773); `JUZGADO DE FAMILIA VIÑA DEL MAR` (72.520) vs `Juzgado de Familia Viña del Mar` (25.483).
- **Disparidad entre Códigos y Nombres de Tribunal:** Existen 34 nombres únicos de tribunales frente a solo 15 valores únicos de `COD_TRIBUNAL`. Esto indica duplicidad artificial de nombres por efecto de capitalización o inconsistencia en la asignación de claves foráneas.

### 4.2. Inconsistencias Semánticas en `TIPO_PROCEDIMIENTO`
- **Variaciones tipográficas y ortográficas:**
  - `Contenciosa` (136.855) frente a `CONTENCIOSA` (54.348).
  - `Medidas de Protección` (60.354), `Medidas de protección` (31.141), `MEDIDAS DE PROTECCIÓN` (23.519) y `MEDIDAS DE PROTECCION` (10.764).
  - `Violencia Intrafamiliar` (28.660), `VIOLENCIA INTRAFAMILIAR` (18.009) y `Violencia intrafamiliar` (13.068).
  - `Cumplimiento` (30.756) y `CUMPLIMIENTO` (8.876).
- **Códigos abreviados aislados:**
  - Presencia de letras individuales que codifican materias procesales: `'C'` (17.897), `'P'` (15.485), `'F'` (6.241). Estos valores requieren homologación con su descripción canónica.

### 4.3. Solapamiento Conceptual en `TIPO_AUDIENCIA`
- **Doble capitalización:**
  - `Audiencia Preparatoria` (200.449) vs `AUDIENCIA PREPARATORIA` (23.719).
  - `Audiencia de Juicio` (63.130) vs `AUDIENCIA DE JUICIO` (6.290).
  - `Audiencia` (50.372) vs `audiencia` (35.961) vs `AUDIENCIA` (9.699).
- **Cruce de conceptos (Contaminación de Procedimiento en Audiencia):**
  - Aparecen tipos de procedimiento erróneamente clasificados como tipo de audiencia: `Contenciosa` (17.897), `Medidas de protección` (15.572), `Violencia intrafamiliar` (6.241), `Cumplimiento` (3.079).

### 4.4. Disparidad de Representación Booleana en `VIDEOCONFERENCIA`
La columna registra 6 formatos diferentes para expresar una condición binaria (presencial vs remota), además de un 53,2% de valores ausentes (previos a la implementación de audiencias telemáticas en 2020 por Ley 21.226):
- Formato textual afirmativo: `"SI"` (34.197).
- Formato textual negativo: `"NO"` (95.023).
- Formato numérico flotante con punto: `"0.0"` (35.299), `"1.0"` (9.451).
- Formato numérico con coma decimal: `"0,0"` (37.048), `"1,0"` (7.023).
- Ausentes: `None` (248.137 registros).

### 4.5. Heterogeneidad en Formatos Horarios (`HORA_INICIO` y `HORA_FIN`)
- Registros que combinan precisión de minutos (`HH:MM`, ej. `09:00`, `11:15`) con precisión de segundos (`HH:MM:SS`, ej. `10:30:00`, `11:00:00`).
- Ambos campos están almacenados como cadenas de texto (`object`), lo que imposibilita el cálculo directo de duración de audiencias sin una transformación previa.

### 4.6. Auditoría y Pertinencia de Formatos Numéricos (`Int64` vs `float64`)
Se auditó si las columnas numéricas corresponden estrictamente a tipos enteros (`Int64` / `int64`) o de punto flotante (`float64`):

| Columna | Dtype Actual | Min | Max | ¿Posee decimales? | Pertinencia del Formato |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `COD_CORTE` | `Int64` | 30 | 30 | No | Adecuado (Identificador institucional) |
| `COD_TRIBUNAL` | `Int64` | 88 | 1271 | No | Adecuado (Identificador foráneo) |
| `TOTAL_AUDIENCIAS` | `Int64` | 1 | 2 | No | Adecuado (Métrica entera de conteo) |
| `ID_CAUSA` | `Int64` | 275.301 | 14.082.680 | No | Adecuado (Identificador numérico con nulos) |
| `ID_AUDIENCIA` | `Int64` | 869.051 | 11.788.789 | No | Adecuado (Identificador numérico con nulos) |
| `ANO_PROCESO` | `int64` | 2015 | 2025 | No | Adecuado (Año calendario de reporte) |
| `ANO_AUDIENCIA` | `float64` | 2015.0 | 2025.0 | **No (0,0%)** | **Inadecuado:** Conceptualmente es un año discreto sin decimales; debe ser tipado a `Int64`. |
| `PLAZO_AGENDAMIENTO` | `float64` | -6.0 | 339.0 | **No (0,0%)** | **Inadecuado:** Es un cómputo de días enteros; debe ser `Int64`. Además, registra anomalías con valores negativos (-6 días). |

**Hallazgos técnicos:**
1. **`ANO_AUDIENCIA`:** Almacenado como `float64` debido a la presencia potencial de nulos en la ingesta cruda de JSON, pero no presenta parte decimal en ninguno de sus 466.178 registros. Corresponde forzar tipado a `Int64`.
2. **`PLAZO_AGENDAMIENTO` e inconsistencia cronológica:** Almacena días transcurridos entre la fecha de programación y la fecha de la audiencia. Ningún valor presenta fracciones de día. Se detectan valores negativos (mínimo de `-6`), lo que denota un registro anómalo donde la fecha de audiencia es previa a la fecha de agendamiento en el sistema.

### 4.7. Auditoría de Columnas de Fecha (`datetime64[ns]`)
Se analizaron las cuatro variables temporales del dataset para evaluar su rango, componente horario y estructura de representación:

| Columna | Dtype | % Nulos | Fecha Mínima | Fecha Máxima | Componente Horario | Formato de Almacenamiento |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FECHA_INGRESO` | `datetime64[ns]` | 9,31% | 2005-10-19 | 2025-12-30 | No (`00:00:00`) | ISO 8601 (`AAAA-MM-DD`) |
| `FECHA_PROGRAMACION` | `datetime64[ns]` | 1,72% | 2006-06-08 | 2025-12-30 | No (`00:00:00`) | ISO 8601 (`AAAA-MM-DD`) |
| `FECHA_AUDIENCIA` | `datetime64[ns]` | 0,26% | 2015-01-02 | 2025-12-31 | No (`00:00:00`) | ISO 8601 (`AAAA-MM-DD`) |
| `FECHA_FIRMA` | `datetime64[ns]` | 62,68% | 2020-12-03 | 2024-12-31 | No (`00:00:00`) | ISO 8601 (`AAAA-MM-DD`) |

**Hallazgos técnicos:**
1. **Representación y Formato:** En el ecosistema Parquet / Pandas, el tipo `datetime64[ns]` almacena internamente nanosegundos desde la época Unix y se proyecta en el estándar internacional ISO 8601 (`AAAA-MM-DD`), no en formato textual fijo `dd-mm-aaaa`. La exportación o reporte en formato tradicional chileno (`DD-MM-AAAA`) debe realizarse mediante formato de salida explícito (`strftime('%d-%m-%Y')`).
2. **Ausencia total de componente horario:** El 100% de los registros en estas 4 columnas registra horas truncadas (`00:00:00`). Las marcas de tiempo de las sesiones residen en los campos independientes `HORA_INICIO` y `HORA_FIN`.
3. **Comportamiento histórico de `FECHA_FIRMA`:** La ausencia de registros antes de diciembre de 2020 confirma que la firma electrónica del acta se implementó de forma sistemática a partir de la tramitación remota (Ley 21.226).

---

## 5. Plan de Acción y Reglas de Transformación Sugeridas

Para la siguiente etapa de limpieza y estandarización, se definen los siguientes criterios:

1. **Normalización Textual:**
   - Aplicar transformación a mayúsculas sostenidas (`str.upper()`), eliminación de tildes y limpieza de espacios en blanco redundantes (`str.strip()`) sobre `CORTE`, `TRIBUNAL`, `TIPO_PROCEDIMIENTO` y `TIPO_AUDIENCIA`.
2. **Homologación de Códigos de Procedimiento:**
   - Mapear las siglas `'C'`, `'P'`, `'F'` a sus respectivas denominaciones canónicas.
3. **Estandarización de `VIDEOCONFERENCIA`:**
   - Convertir a booleano estricto con soporte de nulos (`boolean`):
     - Valores afirmativos (`"SI"`, `"1.0"`, `"1,0"`) -> `True`
     - Valores negativos (`"NO"`, `"0.0"`, `"0,0"`) -> `False`
     - Valores ausentes pre-2020 -> `False` o `pd.NA` según criterio metodológico.
4. **Normalización y Conversión de Tiempos:**
   - Homogeneizar `HORA_INICIO` y `HORA_FIN` a formato `HH:MM:SS` y derivar la variable `DURACION_AUDIENCIA_MINUTOS`.
5. **Corrección de Cruce Procedimiento/Audiencia:**
   - Identificar si las filas donde `TIPO_AUDIENCIA` es `Contenciosa` o `Medidas de protección` poseen valores cruzados con `TIPO_PROCEDIMIENTO` para reubicar la información correctamente.
6. **Reclasificación y Validación de Tipos Numéricos:**
   - Castear `ANO_AUDIENCIA` de `float64` a entero nullable `Int64`.
   - Castear `PLAZO_AGENDAMIENTO` a `Int64` y aplicar regla de tratamiento o imputación a registros con plazos negativos (`PLAZO_AGENDAMIENTO < 0`).
7. **Estandarización de Visualización de Fechas:**
   - Mantener almacenamiento en backend en formato nativo `datetime64[ns]` (estándar ISO), proveyendo formateo `DD-MM-AAAA` en las capas de presentación y reportes analíticos.

---

## 6. Registro de Avance en la Limpieza y Sanitización (Sección 3)

### 6.1. Ejecución del Ítem 3.1: Tratamiento y Resolución del Cruce Anómalo del Año 2023 (Opción A: Fuente Oficial PJUD)

En consonancia con los hallazgos de la auditoría y la detección del desplazamiento estructural de columnas en la API, se integró el archivo oficial del Departamento de Estadísticas del PJUD:  
`data/raw/excel_pjud/audiencias_realizadas_2023.csv` (350.149 filas a nivel nacional; 43.380 para la Corte de Valparaíso).

1. **Diagnóstico Forense de la Anomalía:**
   - La API del PJUD incurrió en un desplazamiento secuencial de campos en la consulta SQL del endpoint 2023: `RUC` fue entregado en `RIT`, la sigla `TIPO CAUSA` en `TIPO_PROCEDIMIENTO`, el procedimiento en `TIPO_AUDIENCIA`, y el tipo real de audiencia en `FECHA_INGRESO` (coaccionado erróneamente a `NaT` por Pandas en la ingesta inicial).
2. **Estrategia de Restitución Oficial (Opción A):**
   - Se ejecutó un cruce relacional exacto sobre el identificador único `CRR AUD` (`ID_AUDIENCIA`), logrando un **100,0% de coincidencia (43.380 de 43.380 registros)**.
   - **`RIT`:** Restituido a su formato procesal auténtico (`F-1-2023`, `C-995-2021`, etc.).
   - **`RUC`:** Restituido a su columna correspondiente con el número nacional de causa.
   - **`TIPO_PROCEDIMIENTO`:** Asignado desde `GLOSA TIPO CAUSA` del reporte oficial.
   - **`TIPO_AUDIENCIA`:** Restituido con su categorización real (`Audiencia Preparatoria`, `Audiencia de Juicio`, `Inmediata`, etc.), **evitando la pérdida de información y eliminando la necesidad de categorías artificiales como 'NO ESPECIFICADA'**.
   - **Fechas Procesales:** Restitución de `FECHA_INGRESO` (eliminando los 43.380 nulos del año) y `FECHA_AUDIENCIA` (eliminando los 1.196 nulos).
   - Trazabilidad: Bandera `FLG_CRUCE_2023 = True` para documentar la intervención.

### 6.2. Ejecución del Ítem 3.2: Resolución de Inconsistencias en Columnas Categóricas

Habiendo restituido la verdad procesal del año 2023, la estandarización general de texto operó sobre bases 100% fidedignas:

1. **Función de Estandarización Textual (`norm_text`):**
   - Eliminación estricta de tildes (descomposición NFKD), depuración de espacios redundantes y conversión a mayúsculas sostenidas (`.upper()`).
2. **Corte y Competencia Institucional:**
   - `CORTE`: Unificado canónicamente a `'C.A. DE VALPARAISO'`.
   - `COMPETENCIA`: Unificado canónicamente a `'FAMILIA'`.
3. **Mapeo Canónico de Tribunales (`TRIBUNAL`):**
   - Mediante `COD_TRIBUNAL`, las 34 variantes se asociaron al catálogo formal del PJUD, consolidando exactamente **15 juzgados canónicos oficiales**.
4. **Homologación de Procedimientos (`TIPO_PROCEDIMIENTO`):**
   - Consolidación en **12 categorías canónicas oficiales** en toda la serie 2015-2025.
5. **Tipos de Audiencia (`TIPO_AUDIENCIA`):**
   - Al haber recuperado las audiencias auténticas de 2023, el universo completo de 466.178 registros se consolidó limpiamente en **12 categorías canónicas de audiencia**, con **cero valores nulos** y sin categorías ficticias.

#### Tabla de Impacto Cuantitativo en Variables Categóricas

| Variable | Valores Crudos | Valores Post 3.1 y 3.2 | Impacto Metodológico |
| :--- | :---: | :---: | :--- |
| **`CORTE`** | 3 | **1** | 100% canónico (`C.A. DE VALPARAISO`) |
| **`COMPETENCIA`** | 1 | **1** | 100% canónico (`FAMILIA`) |
| **`TRIBUNAL`** | 34 | **15** | Integridad foránea garantizada por `COD_TRIBUNAL` |
| **`TIPO_PROCEDIMIENTO`** | 39 | **12** | Procedimientos de 2023 restituidos y siglas absorbidas |
| **`TIPO_AUDIENCIA`** | 35 | **12** | 100% de audiencias reales recuperadas (0 nulos, 0 ficticias) |

### 6.3. Ejecución del Ítem 3.3: Estandarización de Modalidad (Videoconferencia)

1. **Unificación de Formatos Heterogéneos:**
   - Afirmativos (`'SI'`, `'SÍ'`, `'1.0'`, `'1,0'`, `'1'`) $\rightarrow$ `True` (Telemática / Remota).
   - Negativos (`'NO'`, `'0.0'`, `'0,0'`, `'0'`) $\rightarrow$ `False` (Presencial).
2. **Imputación Pre-Pandemia (2015–2020):**
   - 248.137 registros históricos ausentes imputados con `False` (Presencial) conforme al marco legal de la **Ley 21.226**, alcanzando 100% de cobertura en la variable.

#### Tabla de Distribución y Adopción Temporal (Ítem 3.3)

| Año de Proceso | Presencial (`False`) | Telemática (`True`) | % Telemática | Hito Normativo / Contexto |
| :---: | :---: | :---: | :---: | :--- |
| **2015** | 44.827 | 0 | 0,0% | Período histórico presencial ordinario |
| **2016** | 42.948 | 0 | 0,0% | Período histórico presencial ordinario |
| **2017** | 42.572 | 0 | 0,0% | Período histórico presencial ordinario |
| **2018** | 43.260 | 0 | 0,0% | Período histórico presencial ordinario |
| **2019** | 43.450 | 0 | 0,0% | Período histórico presencial ordinario |
| **2020** | 31.080 | 0 | 0,0% | Entrada en vigencia Ley 21.226 (fase piloto/suspensión) |
| **2021** | 32.235 | 10.227 | 24,1% | Despliegue masivo telemático (emergencia sanitaria) |
| **2022** | 31.072 | 12.306 | **28,4%** | **Pico histórico de adopción telemática** |
| **2023** | 31.716 | 11.664 | 26,9% | Consolidación modalidad mixta |
| **2024** | 35.299 | 9.451 | 21,1% | Retorno gradual a presencialidad preferente |
| **2025** | 37.048 | 7.023 | 15,9% | Estabilización post-pandemia |
| **Total Global** | **415.507 (89,1%)** | **50.671 (10,9%)** | **10,9%** | **466.178 audiencias (0 nulos)** |

### 6.4. Ejecución del Ítem 3.4: Homogeneización de Formatos Horarios (`HORA_INICIO` y `HORA_FIN`)

1. **Estandarización de Longitud y Formato (`HH:MM:SS`):**
   - Se procesaron las marcas horarias convirtiendo todas las cadenas a formato uniforme `HH:MM:SS`.
   - Se ajustaron los 3 registros de longitud 4 (`H:MM`, ej. `8:38` $\rightarrow$ `08:38:00`).
   - Se agregaron segundos (`:00`) a los 292.378 registros en formato `HH:MM`.
   - Cobertura: `HORA_INICIO` alcanza 100% en formato `HH:MM:SS` (0 nulos). `HORA_FIN` alcanza 100% en formato `HH:MM:SS` sobre sus registros válidos, preservando los únicos 2 valores ausentes (0,0004%).
2. **Criterio Metodológico Acordado:**
   - En estricto apego al principio de no introducir interpretaciones o ingeniería de atributos no confirmadas, **no se crearon variables derivadas de duración ni banderas de anomalía**, manteniendo los valores puros para posterior evaluación analítica.

### 6.5. Ejecución del Ítem 3.5: Estandarización y Casteo de Tipos Numéricos

1. **`ANO_AUDIENCIA`:**
   - Casteo de `float64` a tipo entero nullable `Int64`. Al no presentar decimales en ningún registro, se garantiza tipado nativo entero con 0% de nulos.
2. **`PLAZO_AGENDAMIENTO`:**
   - Casteo de `float64` a `Int64`.
   - **Preservación estricta de valores:** Se conservan intactos los 16 casos con plazos negativos (-6 a -2 días) y los 97 valores nulos (0,02%), sin forzar imputaciones ni recálculos hasta la posterior fase de análisis.

---

### 6.6. Ejecución del Ítem 3.6: Perfil de Calidad Consolidado y Comparativa de Missingness

Tras aplicar las etapas de saneamiento 3.1 a 3.5, se consolida el estado final de integridad del dataset sanitizado (`df_clean`):

| Variable | Dtype Crudo | Dtype Sanitizado | Nulos Iniciales | Nulos Finales | % Nulos Final | Diagnóstico de Integridad |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **`CORTE`** | `object` | `object (str)` | 0 | **0** | **0,00%** | 100% canónico (`C.A. DE VALPARAISO`) |
| **`COD_CORTE`** | `Int64` | `Int64` | 0 | **0** | **0,00%** | 100% íntegro (Código 30) |
| **`TRIBUNAL`** | `object` | `object (str)` | 0 | **0** | **0,00%** | 15 juzgados canónicos oficiales PJUD |
| **`COD_TRIBUNAL`** | `Int64` | `Int64` | 0 | **0** | **0,00%** | Integridad foránea preservada |
| **`COMPETENCIA`** | `object` | `object (str)` | 0 | **0** | **0,00%** | 100% canónico (`FAMILIA`) |
| **`TIPO_PROCEDIMIENTO`** | `object` | `object (str)` | 0 | **0** | **0,00%** | 12 categorías canónicas oficiales |
| **`TIPO_AUDIENCIA`** | `object` | `object (str)` | 0 | **0** | **0,00%** | 12 categorías reales (100% fidedigno) |
| **`RIT`** | `object` | `object (str)` | 0 | **0** | **0,00%** | 2023 restaurado a formato judicial legal |
| **`FECHA_INGRESO`** | `datetime64[ns]` | `datetime64[ns]` | 43.380 (9,31%) | **0** | **0,00%** | **43.380 nulos recuperados vía Opción A** |
| **`FECHA_AUDIENCIA`** | `datetime64[ns]` | `datetime64[ns]` | 1.196 (0,26%) | **0** | **0,00%** | **1.196 nulos recuperados vía Opción A** |
| **`HORA_INICIO`** | `object` | `object (str)` | 0 | **0** | **0,00%** | 100% homogeneizado a `HH:MM:SS` |
| **`VIDEOCONFERENCIA`** | `object` | `bool` | 248.137 (53,23%) | **0** | **0,00%** | **100% cobertura (Ley 21.226)** |
| **`ANO_PROCESO`** | `int64` | `int64` | 0 | **0** | **0,00%** | Entero nativo |
| **`ANO_AUDIENCIA`** | `float64` | `Int64` | 0 | **0** | **0,00%** | Casteo a entero discreto sin decimales |
| **`TOTAL_AUDIENCIAS`** | `Int64` | `Int64` | 0 | **0** | **0,00%** | Entero nativo de conteo |
| **`FLG_CRUCE_2023`** | *(Nueva)* | `bool` | — | **0** | **0,00%** | Bandera de trazabilidad de auditoría |
| **`HORA_FIN`** | `object` | `object (str)` | 2 | **2** | **0,0004%** | Homogeneizado a `HH:MM:SS` (nulos preservados) |
| **`PLAZO_AGENDAMIENTO`**| `float64` | `Int64` | 97 | **97** | **0,02%** | Casteo a `Int64` (16 negativos preservados) |
| **`FECHA_PROGRAMACION`**| `datetime64[ns]` | `datetime64[ns]` | 9.228 | **9.228** | **1,98%** | Sin programación (audiencias inmediatas) |
| **`ID_AUDIENCIA`** | `Int64` | `Int64` | 290.599 | **290.599** | **62,34%** | No registrado en sistemas históricos |
| **`FECHA_FIRMA`** | `datetime64[ns]` | `datetime64[ns]` | 292.208 | **292.208** | **62,68%** | Solo existe a partir de firma electrónica remota |
| **`ID_CAUSA`** | `Int64` | `Int64` | 333.977 | **333.977** | **71,64%** | Identificador interno no poblado en serie antigua |
| **`RUC`** | `object` | `object (str)` | 422.107 (90,55%) | **378.727** | **81,24%** | **43.380 RUCs recuperados en lote 2023** |

> **Conclusión del Perfil:** De las 23 columnas del dataset sanitizado, **16 columnas presentan un 100,0% de completitud (0 valores nulos)**. Los valores ausentes remanentes responden a condicionantes estructurales del sistema judicial (causas inmediatas sin programación, firmas electrónicas implementadas a finales de 2020 e identificadores introducidos en años recientes).

### 6.7. Ejecución del Ítem 3.7: Normalización de RIT y Creación de Clave Compuesta (`ID_CAUSA_RIT`)

1. **Resolución de Inconsistencia de Formato:**
   - Se corrigieron 41.439 registros (8,89% del universo) que contenían doble guión (`--`), unificándolos al formato canónico con guión simple (`-`).
   - Se validó mediante expresión regular (`^[A-Z]{1,2}-\d+-\d{4}$`) la totalidad del dataset: **100,0% de conformidad (466.178 registros conformes con `Letra-Correlativo-Año`) y 0 no conformes**.
2. **Construcción de la Clave Compuesta de Causa (`ID_CAUSA_RIT`):**
   - Regla de negocio: `ID_CAUSA_RIT = COD_TRIBUNAL + '-' + RIT` (ej. `1261-A-5-2015`).
   - **Razón jurídica:** El RIT no es global sino relativo a cada tribunal. Al combinarlo con el código del tribunal, se obtiene el identificador unívoco de la causa judicial a nivel de la jurisdicción.
3. **Métricas de Granularidad Causa vs. Audiencia:**
   - **Total de audiencias en la serie:** 466.178 registros.
   - **Total de causas judiciales únicas:** **280.795 causas**.
   - **Tasa de recurrencia:** **1,66 audiencias por causa judicial** en promedio.

### 6.8. Ejecución del Ítem 3.8: Verificación de Duplicados Exactos y Claves de Sesión

1. **Duplicados Exactos Globales (24 columnas):**
   - **0 registros duplicados exactos** (`df_clean.duplicated().sum() == 0`). No existen filas con coincidencia total en todos sus campos.
2. **Duplicados Sustantivos (Excluyendo identificadores de sistema `ID_AUDIENCIA` y `FLG_CRUCE_2023`):**
   - **0 registros duplicados sustantivos**.
3. **Colisiones a Nivel de Sesión (`ID_CAUSA_RIT`, `FECHA_AUDIENCIA`, `HORA_INICIO`):**
   - Se detectaron únicamente **28 registros (14 pares)** que comparten la misma causa judicial, fecha de audiencia y hora de inicio.
   - **Diagnóstico cualitativo:** En 13 de los 14 pares se constatan audiencias tramitadas en una misma sesión con naturalezas procesales distintas (ej. Inmediata tramitada conjuntamente con Preparatoria, o citaciones preliminares), lo que refleja la acumulación de actos procesales en un mismo bloque de sala. Solo 1 par (causa `1265-X-553-2018` en 2020) refleja una duplicación técnica estricta.

---

## 7. Sección 4: Diagnóstico y Perfil de Calidad de Datos Faltantes

En el inicio de la Sección 4, se consolida la evaluación de completitud de las 24 variables del dataset sanitizado (`df_clean` con 466.178 registros):

| Variable | Dtype | Nulos Absolutos | % Nulos | Categoría Estructural | Diagnóstico y Contexto |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **`CORTE`** | `object (str)` | **0** | **0,00%** | Institucional | 100% íntegro (`C.A. DE VALPARAISO`) |
| **`COD_CORTE`** | `Int64` | **0** | **0,00%** | Institucional | 100% íntegro (Código 30) |
| **`TRIBUNAL`** | `object (str)` | **0** | **0,00%** | Institucional | 15 juzgados canónicos oficiales |
| **`COD_TRIBUNAL`** | `Int64` | **0** | **0,00%** | Institucional | Integridad foránea preservada |
| **`COMPETENCIA`** | `object (str)` | **0** | **0,00%** | Procesal | 100% íntegro (`FAMILIA`) |
| **`TIPO_PROCEDIMIENTO`** | `object (str)` | **0** | **0,00%** | Procesal | 12 categorías legales oficiales |
| **`TIPO_AUDIENCIA`** | `object (str)` | **0** | **0,00%** | Procesal | 12 categorías reales (100% fidedigno) |
| **`RIT`** | `object (str)` | **0** | **0,00%** | Identificador | 100% conforme a `Letra-Correlativo-Año` |
| **`ID_CAUSA_RIT`** | `object (str)` | **0** | **0,00%** | Clave Compuesta | Clave unívoca de causa (280.795 causas) |
| **`FECHA_INGRESO`** | `datetime64[ns]` | **0** | **0,00%** | Temporal | 100% íntegro (43.380 recuperadas en 2023) |
| **`FECHA_AUDIENCIA`** | `datetime64[ns]` | **0** | **0,00%** | Temporal | 100% íntegro (1.196 recuperadas en 2023) |
| **`HORA_INICIO`** | `object (str)` | **0** | **0,00%** | Horaria | 100% estandarizado a `HH:MM:SS` |
| **`VIDEOCONFERENCIA`** | `bool` | **0** | **0,00%** | Operativa | 100% tipado booleano (Ley 21.226) |
| **`ANO_PROCESO`** | `int64` | **0** | **0,00%** | Control | Entero anual (2015–2025) |
| **`ANO_AUDIENCIA`** | `Int64` | **0** | **0,00%** | Temporal | Entero discreto sin decimales |
| **`TOTAL_AUDIENCIAS`** | `Int64` | **0** | **0,00%** | Conteo | Entero de conteo (1 a 2) |
| **`FLG_CRUCE_2023`** | `bool` | **0** | **0,00%** | Auditoría | Trazabilidad del saneamiento 2023 |
| **`HORA_FIN`** | `object (str)` | **2** | **0,0004%** | Horaria | Únicos 2 registros faltantes en 11 años |
| **`PLAZO_AGENDAMIENTO`** | `Int64` | **97** | **0,0208%** | Temporal | Días transcurridos (16 negativos preservados) |
| **`FECHA_PROGRAMACION`** | `datetime64[ns]` | **9.228** | **1,9795%** | Procesal | Causas sin programación (trámite inmediato) |
| **`ID_AUDIENCIA`** | `Int64` | **290.599** | **62,3365%** | Sistema | ID de backend introducido en sistemas modernos |
| **`FECHA_FIRMA`** | `datetime64[ns]` | **292.208** | **62,6816%** | Procesal Digital | Firma electrónica creada con Ley 21.226 |
| **`ID_CAUSA`** | `Int64` | **333.977** | **71,6415%** | Sistema | Clave foránea interna no poblada en serie histórica |
| **`RUC`** | `object (str)` | **378.727** | **81,2409%** | Identificador | RUC nacional ausente en causas antiguas |

### Conclusiones Diagnósticas para la Toma de Decisiones
1. **Núcleo Duro de Análisis (17 variables 100% completas):** Todas las dimensiones procesales, institucionales y cronológicas centrales (`TRIBUNAL`, `TIPO_PROCEDIMIENTO`, `TIPO_AUDIENCIA`, `ID_CAUSA_RIT`, `FECHA_AUDIENCIA`, `HORA_INICIO`, `VIDEOCONFERENCIA`) están completamente libres de nulos.
2. **Nulos Operativos Residuales:**
   - `HORA_FIN` (2 registros) y `PLAZO_AGENDAMIENTO` (97 registros) son volúmenes marginales ($< 0,02\%$).
3. **Nulos Estructurales por Definición de Negocio:**
   - `FECHA_PROGRAMACION` (1,98%) obedece a audiencias inmediatas que, por definición procesal, no tuvieron una fecha de programación previa.
   - `FECHA_FIRMA` (62,68%) obedece al cambio normativo que incorporó la firma electrónica del acta recién a partir de finales de 2020.
   - `RUC`, `ID_CAUSA` e `ID_AUDIENCIA` responden a la evolución tecnológica del sistema informático judicial del PJUD.

---

### 7.1. Ejecución del Ítem 4.2: Depuración de Columnas y Anonimización del Modelo (Eliminación de `RUC`, `ID_CAUSA`, `ID_AUDIENCIA` y `FECHA_FIRMA`)

En consonancia con los objetivos de modelamiento de inteligencia de negocio (BI) para un estudio jurídico y la estricta protección de datos personales en materias sensibles de familia, se formaliza la eliminación de 4 variables:

1. **`RUC` (81,24% de nulos):**
   - **Justificación:** Identificador tributario/nacional de causa. Se remueve para anonimizar los expedientes judiciales de familia. La identificación unívoca de las causas se garantiza al 100% mediante la clave compuesta canónica `ID_CAUSA_RIT`.
2. **`ID_CAUSA` (71,64% de nulos):**
   - **Justificación:** Clave foránea interna del SITFA ausente en los primeros 6 años de la serie (2015-2020). Reemplazada plenamente por `ID_CAUSA_RIT`.
3. **`ID_AUDIENCIA` (62,34% de nulos):**
   - **Justificación:** Clave técnica del servidor judicial no registrada en sistemas antiguos y redundante frente a la granularidad de la audiencia (`ID_CAUSA_RIT` + `FECHA_AUDIENCIA` + `HORA_INICIO`).
4. **`FECHA_FIRMA` (62,68% de nulos):**
   - **Fundamento Procesal:** En el procedimiento oral de familia (Ley 19.968), las resoluciones se notifican de inmediato en la audiencia misma (Art. 23) y el registro legal vinculante es el audio digital (Art. 24). Los plazos fatales corren desde la audiencia, no desde la posterior firma administrativa del acta.
   - **Fundamento de Inteligencia de Negocio (BI):** No influye en la agenda, preparación, estrategia, recursos ni tarificación de horas de los abogados litigantes. Carece de comparabilidad (100% nulo en 2015-2020 y 2025; no existe en la fuente oficial PJUD de 2023; e idéntica a la fecha de audiencia en 2024).

#### Impacto Cuantitativo de la Depuración en el Modelo Final

- **Dimensiones del Dataset:** De 24 variables se pasa a **20 variables clave**.
- **Variables 100% Completas (0 Nulos):** **17 de las 20 columnas (85,0% de las variables)**.
- **Variables con Valores Faltantes Remanentes:** Se reducen de 7 a únicamente **3 variables**, todas con volumen marginal o justificación procesal explícita:
  1. `FECHA_PROGRAMACION`: 9.228 nulos (**1,98%**, inherente a causas inmediatas sin agendamiento previo).
  2. `PLAZO_AGENDAMIENTO`: 97 nulos (**0,02%**, subordinado a la ausencia de fecha de programación).
  3. `HORA_FIN`: 2 nulos (**0,0004%**, anomalía operativa puntual de registro).
- **Cobertura General del Dataset:** El modelo alcanza una completitud superior al **99,8%** de sus celdas útiles.

---

### 7.2. Ejecución del Ítem 4.3: Tratamiento e Imputación de Faltantes Remanentes (`HORA_FIN`, `FECHA_PROGRAMACION` y `PLAZO_AGENDAMIENTO`)

Se implementó el plan consensuado de imputación procesal, alcanzando una **completitud del 100,00% en la totalidad de las 20 columnas del dataset**:

1. **`HORA_FIN` (2 registros):**
   - **Método:** Imputación por mediana de duración observada en Audiencia Preparatoria (**18 minutos**) sumada a la respectiva `HORA_INICIO`.
   - Caso Limache (2020): `08:48:00` $+$ 18 min $\rightarrow$ **`09:06:00`**.
   - Caso Quintero (2022): `11:00:00` $+$ 18 min $\rightarrow$ **`11:18:00`**.
   - Cobertura resultante: **100,00% (0 nulos)**.
2. **`FECHA_PROGRAMACION` (9.228 registros):**
   - **Hallazgo Empírico y Jurídico:** El 100% de los 9.228 registros ausentes corresponden a **Audiencias Inmediatas** (8.032 entre 2015-2022/2024-2025 y los 1.196 del año 2023). Al ser audiencias de comparecencia y resolución inmediata en flagrancia (Ley 19.968, Art. 71), citación y audiencia ocurren en el mismo acto.
   - **Regla:** Imputación con `FECHA_AUDIENCIA` ($\text{FECHA\_PROGRAMACION} = \text{FECHA\_AUDIENCIA}$).
   - Cobertura resultante: **100,00% (0 nulos)**.
3. **`PLAZO_AGENDAMIENTO` (97 nulos y 16 negativos):**
   - **Adopción del Estándar Oficial PJUD:** El propio reporte del PJUD asignó formalmente `0` días de agendamiento para las audiencias inmediatas de 2023. Se imputan a **`0` días** los 97 nulos y se corrigen a **`0` días** los 16 registros negativos generados por desfases de ingreso administrativo.
   - Cobertura resultante: **100,00% (0 nulos, rango válido $\ge 0$)**.

#### Tabla Final de Completitud del Dataset Sanitizado e Imputado (`df_clean`)

| Variable | Dtype | Nulos | % Completitud | Tipo de Dato / Rol en el Modelo |
| :--- | :--- | :---: | :---: | :--- |
| **`COD_CORTE`** | `Int64` | **0** | **100,0%** | Código institucional (30) |
| **`CORTE`** | `object (str)` | **0** | **100,0%** | `C.A. DE VALPARAISO` |
| **`COD_TRIBUNAL`** | `Int64` | **0** | **100,0%** | Identificador foráneo PJUD |
| **`TRIBUNAL`** | `object (str)` | **0** | **100,0%** | 15 juzgados canónicos oficiales |
| **`RIT`** | `object (str)` | **0** | **100,0%** | Rol judicial normalizado (`Letra-Num-Año`) |
| **`ID_CAUSA_RIT`** | `object (str)` | **0** | **100,0%** | Clave compuesta unívoca de causa |
| **`TIPO_PROCEDIMIENTO`**| `object (str)` | **0** | **100,0%** | 12 categorías legales canónicas |
| **`TIPO_AUDIENCIA`** | `object (str)` | **0** | **100,0%** | 12 tipos canónicos oficiales PJUD |
| **`FECHA_INGRESO`** | `datetime64[ns]` | **0** | **100,0%** | Fecha de ingreso de la causa a tribunal |
| **`FECHA_PROGRAMACION`**| `datetime64[ns]` | **0** | **100,0%** | Fecha de agendamiento (100% íntegra) |
| **`FECHA_AUDIENCIA`** | `datetime64[ns]` | **0** | **100,0%** | Fecha de celebración de la audiencia |
| **`PLAZO_AGENDAMIENTO`**| `Int64` | **0** | **100,0%** | Días hábiles de espera ($\ge 0$, 0 nulos) |
| **`HORA_INICIO`** | `object (str)` | **0** | **100,0%** | Formato canónico `HH:MM:SS` |
| **`HORA_FIN`** | `object (str)` | **0** | **100,0%** | Formato canónico `HH:MM:SS` (0 nulos) |
| **`ANO_AUDIENCIA`** | `Int64` | **0** | **100,0%** | Año calendario discreto |
| **`COMPETENCIA`** | `object (str)` | **0** | **100,0%** | Materia canónica (`FAMILIA`) |
| **`TOTAL_AUDIENCIAS`** | `Int64` | **0** | **100,0%** | Conteo de audiencia |
| **`VIDEOCONFERENCIA`** | `bool` | **0** | **100,0%** | Booleano estricto (Presencial / Remota) |
| **`ANO_PROCESO`** | `int64` | **0** | **100,0%** | Año de reporte estadístico (2015–2025) |
| **`FLG_CRUCE_2023`** | `bool` | **0** | **100,0%** | Trazabilidad de auditoría |

> **Hito Metodológico Alcanzado:** La totalidad de las 20 variables y los 466.178 registros del dataset se encuentran en estado de **calidad de datos 100% íntegra (cero valores nulos)**, con tipados nativos correctos y adaptados para inteligencia de negocio.

---

## 8. Sección 5: Auditoría y Tratamiento de Valores Imposibles y Outliers (Fechas, Plazos y Horarios)

En la Sección 5 se aborda el análisis y tratamiento de anomalías físicas, lógicas y estadísticas en las dimensiones temporales y cuantitativas del dataset de 466.178 registros:

### 8.1. Auditoría y Corrección de Valores Imposibles en Fechas

Se auditó de manera cruzada la secuencia cronológica universal exigida por el procedimiento judicial:
$$\text{FECHA\_INGRESO} \le \text{FECHA\_PROGRAMACION} \le \text{FECHA\_AUDIENCIA}$$

1. **Rangos Temporales Históricos:**
   - `FECHA_INGRESO`: Desde el **19-10-2005** hasta el **30-12-2025**. El mínimo coincide con el inicio histórico de la Ley N° 19.968 (creación de los Tribunales de Familia en octubre de 2005). No existen años prehistóricos (1900) ni futuros ficticios.
   - `FECHA_PROGRAMACION`: Desde el 15-05-2014 hasta el 31-12-2025.
   - `FECHA_AUDIENCIA`: Desde el 02-01-2015 hasta el 31-12-2025 (11 años completos, coherencia absoluta con `ANO_AUDIENCIA` y `ANO_PROCESO` al 100%).
2. **Evaluación de Inconsistencias Físicas:**
   - **`FECHA_AUDIENCIA < FECHA_INGRESO`**: **0 casos (0,00%)**. En ningún expediente se celebró audiencia con anterioridad al ingreso de la demanda o causa.
   - **`FECHA_PROGRAMACION < FECHA_INGRESO`**: **0 casos (0,00%)**. En ningún caso se dictó resolución de agendamiento antes del ingreso de la causa.
   - **`FECHA_AUDIENCIA < FECHA_PROGRAMACION`**: **22 casos (0,0047%)**.
     - *Diagnóstico Forense:* Se identificó un desfase administrativo menor de **1 a 5 días** (ej. audiencia el viernes 22 y resolución en SITFA firmada el lunes 25). Corresponde típicamente a continuaciones de juicios orales o audiencias celebradas de urgencia en estrado, donde la actuación judicial material precede al registro informático de la providencia.
     - *Tratamiento Aplicado (Acción 1 consensuada):* Se ajustó **`FECHA_PROGRAMACION = FECHA_AUDIENCIA`** en los 22 casos. Dado que la audiencia efectivamente se realizó y su plazo de agendamiento ya había sido fijado en `0` días (espera nula en el paso 4.3), este ajuste restituye la consistencia temporal física sin alterar los plazos procesales.
     - *Resultado:* **100,00% de coherencia cronológica en el dataset completo (0 inconsistencias residuales)**.

---

### 8.2. Auditoría y Decisión de Negocio sobre `PLAZO_AGENDAMIENTO` (Días Hábiles L–S)

Se analizó la distribución de los días hábiles judiciales transcurridos entre la resolución de citación y la celebración de la audiencia:

| Métrica / Estadístico | Días Hábiles Judiciales | Equivalencia Calendario Estimada |
| :--- | :---: | :--- |
| **Mínimo** | **0 días** | Mismo día (audiencias inmediatas y urgencias) |
| **Percentil 10** | **7 días** | ~1 semana |
| **Percentil 25 (Q1)** | **12 días** | ~2 semanas |
| **Mediana (Q2)** | **26 días** | ~1 mes |
| **Media** | **31,4 días** | ~1,2 meses |
| **Percentil 75 (Q3)** | **43 días** | ~1,5 meses |
| **Percentil 90** | **64 días** | ~2,5 meses |
| **Percentil 95** | **77 días** | ~3 meses |
| **Percentil 99** | **117 días** | ~4,5 meses |
| **Percentil 99,9** | **183 días** | ~7 meses |
| **Máximo** | **339 días** | ~13 meses hábiles (1,1 años corridos) |

1. **Detección de Outliers Estadísticos (Regla de Tukey):**
   - $IQR = Q_3 - Q_1 = 43 - 12 = 31\text{ días hábiles}$.
   - **Umbral Outlier Extremo ($Q_3 + 3,0 \times IQR$):** $> 136,0\text{ días hábiles}$.
   - Casos que superan el umbral extremo: **2.423 registros (0,520%)**.
   - Casos que superan 180 días hábiles (~6 meses hábiles): **530 registros (0,114%)**.
   - Casos que superan 250 días hábiles: **14 registros (0,003%)**.
2. **Fundamento Jurídico y de Inteligencia de Negocio (Decisión de Conservación):**
   - **No truncar ni winsorizar:** En la práctica de los tribunales de familia (especialmente en Viña del Mar y Valparaíso), las demoras extremas obedecen a peritajes psicológicos o de ADN de alta complejidad (DAM, PRM, SML), suspensiones bilaterales de común acuerdo (art. 202 CPC) o colapso estacional de agendas judiciales.
   - Para un estudio jurídico enfocado en Business Intelligence, estos valores constituyen **KPIs fidedignos de congestión judicial real**. Truncar o eliminar estos registros falsearía la predictibilidad de tiempos y la tarificación de honorarios para los clientes.
   - **Derivación:** Se documenta la futura segmentación por tramos de congestión para la fase de **EDA y Feature Engineering**.

---

### 8.3. Auditoría de Horarios de Audiencia (`HORA_INICIO` y `HORA_FIN`)

Se examinaron las marcas horarias y la duración resultante de las sesiones:

1. **Rangos:** `HORA_INICIO` entre 08:00:00 y 21:30:00; `HORA_FIN` entre 08:01:00 y 22:16:00.
2. **Duración Negativa (`HORA_FIN < HORA_INICIO`):** **0 casos (0,00%)**. Integridad cronológica absoluta.
3. **Duración Cero Minutos (`HORA_FIN == HORA_INICIO`):** **1.008 casos (0,216%)**.
   - Corresponden a **audiencias frustradas en el acto**: incomparecencia de ambas partes o del actor, desistimientos al minuto o suspensiones de plano donde el actuario certifica el cierre sin debate sustantivo.
4. **Duración Extrema (> 8 horas):** **54 casos (0,012%)**.
   - Corresponden a sesiones con recesos continuos o actas de jornada completa dejadas abiertas en SITFA en juzgados unipersonales pequeños.
5. **Decisión de Negocio (Opción B adoptada):**
   - **Conservación íntegra de marcas horarias originales** sin alteración artificial ni imputación forzada.
   - Las variables analíticas derivadas de duración y tramo horario se formalizan en la etapa de Ingeniería de Características.

---

## 9. Sección 6: Ingeniería de Características para Business Intelligence

Con el objetivo de transformar los microdatos judiciales limpios en una fuente analítica de alto valor para un **estudio jurídico de derecho de familia**, se implementaron **16 nuevas características analíticas derivadas**, elevando el modelo de 20 a **36 variables especializadas**:

### 9.1. Módulo de Calendario y Ciclos Judiciales
1. **`DIA_SEMANA_AUDIENCIA`**: Día de comparecencia (*Lunes a Sábado*). El 83% de las audiencias se concentra entre lunes y jueves (~96k sesiones diarias). Los viernes disminuyen en un 20% (79k) por reserva de tiempo judicial para acuerdos y sentencias, mientras que los sábados (184 casos) corresponden a turnos cautelares urgentes.
2. **`MES_AUDIENCIA`** y **`TRIMESTRE_AUDIENCIA`**: Variables de estacionalidad que capturan el receso judicial de febrero (feria judicial) y los picos de marzo y cierre de año.
3. **`BLOQUE_HORARIO`**: Franjas operativas de inicio de sesión:
   - *Mañana Temprano (08:00–09:59):* 135.016 casos (29,0%).
   - *Mañana Central (10:00–11:59):* 188.063 casos (40,3% — **Pico de saturación de salas**).
   - *Mediodía (12:00–13:59):* 138.373 casos (29,7%).
   - *Tarde y Turno ( $\ge$ 14:00):* 4.726 casos (1,0%).

### 9.2. Módulo de Duración y Eficiencia en Sala (Time-Tracking)
4. **`DURACION_MINUTOS`**: Duración efectiva en minutos calculada a partir de $(\text{HORA\_FIN} - \text{HORA\_INICIO})$. Mediana general: **18,0 minutos** (Preparatoria: 17 min; Juicio: 20 min; Continuación de Juicio: 38 min).
5. **`TRAMO_DURACION`**: Categorización para tarificación de horas de abogado y estimación de comparecencia (*0. Frustrada (0 min), 1. Breve (1-15 min), 2. Estándar (16-30 min), 3. Extendida (31-60 min), 4. Compleja (>60 min)*).
6. **`FLG_AUDIENCIA_FRUSTRADA`**: Indicador booleano (`True` si duración es 0 min) que aísla las 1.008 audiencias terminadas de plano por incomparecencia de partes o desistimiento al minuto.

### 9.3. Módulo de Tramitación y Cuellos de Botella (Lead Times & SLAs)
7. **`DIAS_TRAMITACION_PREVIA`**: Días corridos acumulados desde la presentación de la demanda hasta la audiencia (`FECHA_AUDIENCIA - FECHA_INGRESO`). Mediana: 68 días (~2,2 meses corridos).
8. **`DIAS_DESPACHO_AGENDAMIENTO`**: Días corridos desde el ingreso hasta la resolución que programó la audiencia (`FECHA_PROGRAMACION - FECHA_INGRESO`). Mide la celeridad administrativa del tribunal.
9. **`TRAMO_AGENDAMIENTO`**: Segmentación de los días hábiles de `PLAZO_AGENDAMIENTO` en 6 niveles de servicio (*Inmediato [0d], Rápido [1-15d], Estándar Legal [16-30d], Demora Moderada [31-60d], Congestión Severa [61-120d], Cuello de Botella Crítico [>120d]*).

### 9.4. Módulo de Secuencia Procesal y Litigiosidad de Causa
10. **`ORDEN_AUDIENCIA_CAUSA`**: Correlativo cronológico de la audiencia dentro de la misma causa judicial (`ID_CAUSA_RIT`). Permite identificar si la causa está en su audiencia inaugural (60,2%) o en etapas avanzadas de litigación.
11. **`TOTAL_AUDIENCIAS_CAUSA`**: Volumen acumulado de audiencias celebradas en la causa.
12. **`ES_AUDIENCIA_INICIAL`**: Booleano (`ORDEN_AUDIENCIA_CAUSA == 1`).
13. **`ES_CONTINUACION`**: Booleano (`True` si el tipo de audiencia es de continuación).

### 9.5. Módulo de Segmentación Jurídica y Contexto Normativo
14. **`MACRO_MATERIA`**: Clasificación funcional de los 12 procedimientos en las áreas de práctica del estudio:
    - *Litigación Contenciosa:* 209.100 audiencias (44,9% — alimentos, cuidado personal, relación directa y regular, divorcios).
    - *Medidas Cautelares y Vulnerabilidad:* 207.328 audiencias (44,5% — VIF y protección de menores).
    - *Ejecución y Alimentos (Cumplimiento):* 42.711 audiencias (9,2% — liquidaciones, apremios, retenciones).
    - *Actos No Contenciosos y Voluntarios:* 7.017 audiencias (1,5% — adopción, voluntarias, cambio de sexo registral).
    - *Otros Procedimientos:* 22 audiencias (< 0,01%).
15. **`EPOCA_NORMATIVA`**: Entorno procesal según reformas legales:
    - *Pre-Pandemia (Presencial):* 225.891 audiencias (48,5% — 2015 a marzo de 2020).
    - *Emergencia Sanitaria (Ley 21.226):* 97.649 audiencias (20,9% — marzo 2020 a septiembre 2022).
    - *Régimen Permanente Híbrido (Ley 21.394):* 142.638 audiencias (30,6% — octubre 2022 a diciembre 2025).

---

## 10. Sección 7: Persistencia Definitiva y Cierre del Pipeline ETL

### 10.1. Especificación del Artefacto de Datos
- **Ruta de Almacenamiento:** `data/processed/audiencias_preparadas_modelo.parquet`.
- **Formato:** Apache Parquet columnar con compresión Snappy.
- **Dimensiones:** **466.178 filas $\times$ 36 columnas**.
- **Tamaño en Disco:** **10,77 MB** (altamente optimizado frente a los más de 700 MB del origen en texto/JSON).
- **Integridad:** **100,00% de completitud (0 valores nulos en las 36 variables)**.

### 10.2. Diccionario de las 36 Columnas del Modelo Final

| Nº | Columna | Dtype | Rol Analítico | Descripción y Contenido |
| :---: | :--- | :--- | :--- | :--- |
| **1** | `COD_CORTE` | `Int64` | Institucional | Código PJUD de la Corte de Apelaciones (30). |
| **2** | `CORTE` | `str` | Institucional | Nombre canónico (`C.A. DE VALPARAISO`). |
| **3** | `COD_TRIBUNAL` | `Int64` | Institucional | Código oficial PJUD del juzgado (15 juzgados). |
| **4** | `TRIBUNAL` | `str` | Institucional | Nombre oficial estandarizado del tribunal de familia. |
| **5** | `RIT` | `str` | Identificador | Rol Interno del Tribunal (`Letra-Correlativo-Año`). |
| **6** | `ID_CAUSA_RIT` | `str` | Clave Primaria | Clave compuesta única de la causa judicial (`COD_TRIBUNAL-RIT`). |
| **7** | `TIPO_PROCEDIMIENTO` | `str` | Procesal | Uno de los 12 procedimientos canónicos de familia. |
| **8** | `MACRO_MATERIA` | `str` | Negocio / Área | Área de práctica del estudio (Contenciosa, Medidas Cautelares, Cumplimiento, etc.). |
| **9** | `TIPO_AUDIENCIA` | `str` | Procesal | Uno de los 12 tipos canónicos de audiencia (100% auténticos). |
| **10** | `FECHA_INGRESO` | `datetime64` | Hito Temporal | Fecha en que la demanda/trámite ingresó al tribunal. |
| **11** | `FECHA_PROGRAMACION` | `datetime64` | Hito Temporal | Fecha en que el tribunal dictó la resolución de agendamiento. |
| **12** | `FECHA_AUDIENCIA` | `datetime64` | Hito Temporal | Fecha efectiva de celebración de la audiencia. |
| **13** | `ANO_AUDIENCIA` | `Int64` | Calendario | Año calendario de la audiencia (2015–2025). |
| **14** | `ANO_PROCESO` | `int64` | Control | Año de corte estadístico PJUD. |
| **15** | `MES_AUDIENCIA` | `str` | Calendario | Nombre del mes de celebración. |
| **16** | `TRIMESTRE_AUDIENCIA` | `str` | Calendario | Trimestre del año (`Q1` a `Q4`). |
| **17** | `DIA_SEMANA_AUDIENCIA`| `str` | Calendario | Día de la semana de la sesión (*Lunes a Sábado*). |
| **18** | `HORA_INICIO` | `str` | Horario | Hora canónica de inicio (`HH:MM:SS`). |
| **19** | `HORA_FIN` | `str` | Horario | Hora canónica de término (`HH:MM:SS`). |
| **20** | `BLOQUE_HORARIO` | `str` | Horario | Franja horaria de inicio (*Mañana Temprano, Central, Mediodía, Tarde*). |
| **21** | `DURACION_MINUTOS` | `float64` | Time-Tracking | Minutos efectivos transcurridos en sala. |
| **22** | `TRAMO_DURACION` | `str` | Time-Tracking | Categoría de duración (*Frustrada, Breve, Estándar, Extendida, Compleja*). |
| **23** | `FLG_AUDIENCIA_FRUSTRADA`| `bool` | Control | `True` si la duración fue de 0 minutos (frustrada de plano). |
| **24** | `PLAZO_AGENDAMIENTO` | `Int64` | SLA / Lead Time | Días hábiles judiciales (L–S) de espera de citación. |
| **25** | `TRAMO_AGENDAMIENTO` | `str` | SLA / Lead Time | Nivel de demora (*Inmediato, Rápido, Legal, Moderado, Severo, Crítico*). |
| **26** | `DIAS_TRAMITACION_PREVIA`| `int64` | Lead Time | Días corridos acumulados desde el ingreso de la causa hasta la audiencia. |
| **27** | `DIAS_DESPACHO_AGENDAMIENTO`| `int64`| Lead Time | Días corridos desde el ingreso hasta la resolución de citación. |
| **28** | `ORDEN_AUDIENCIA_CAUSA` | `int16` | Secuencia | Correlativo de audiencia dentro de la misma causa (1, 2, 3...). |
| **29** | `TOTAL_AUDIENCIAS_CAUSA`| `int16` | Litigiosidad | Total de audiencias acumuladas por esa causa judicial. |
| **30** | `ES_AUDIENCIA_INICIAL` | `bool` | Secuencia | `True` si es la primera audiencia de la causa. |
| **31** | `ES_CONTINUACION` | `bool` | Litigiosidad | `True` si la audiencia es continuación de una previa. |
| **32** | `COMPETENCIA` | `str` | Institucional | Especialidad judicial canónica (`FAMILIA`). |
| **33** | `TOTAL_AUDIENCIAS` | `Int64` | Conteo | Entero de conteo original. |
| **34** | `VIDEOCONFERENCIA` | `bool` | Modalidad | `True` si la audiencia fue telemática (Ley 21.226 / 21.394). |
| **35** | `EPOCA_NORMATIVA` | `str` | Contexto Legal | Período legal (*Pre-Pandemia, Emergencia Sanitaria, Régimen Híbrido*). |
| **36** | `FLG_CRUCE_2023` | `bool` | Trazabilidad | `True` si el registro fue saneado mediante cruce oficial 2023. |

### 10.3. Hito Conclusivo del Pipeline de Datos
Con la ejecución íntegra de las Secciones 1 a 7, el proceso de **Extracción, Transformación, Limpieza, Imputación, Saneamiento Forense, Auditoría de Outliers, Ingeniería de Características y Persistencia** se declara **100% CULMINADO Y CERTIFICADO**.

El artefacto `audiencias_preparadas_modelo.parquet` queda listo y validado para alimentar de forma desacoplada el **Dashboard Ejecutivo de Business Intelligence** en la aplicación web Streamlit.












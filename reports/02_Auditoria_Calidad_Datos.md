# Informe Técnico: Auditoría y Perfil de Calidad de Datos
## Entidad de Estudio: Audiencias Realizadas (Competencia Familia)
**Jurisdicción:** Corte de Apelaciones de Valparaíso (Código 30)  
**Período Temporal:** 2015 – 2025 (11 períodos anuales completos)  
**Dataset Auditado:** `audiencias_realizadas_competencia_detalle.parquet`  
**Proyecto:** CD-2026-Proyecto-EquipoEMCR  
**Fecha de Emisión:** Octubre 2026  

---

## 1. Resumen Ejecutivo de la Auditoría

El presente informe expone los resultados del análisis exploratorio inicial y la auditoría exhaustiva de calidad de datos realizada sobre el dataset consolidado de microdatos judiciales de **Audiencias Realizadas** para la jurisdicción de la Corte de Apelaciones de Valparaíso (2015-2025).

El dataset analizado cuenta con un volumen total de **466.178 registros** y **22 variables**, obtenido a partir de la ingesta automatizada de la API de estadísticas del Poder Judicial de Chile (PJUD).

### Ficha Resumen de Integridad General

| Métrica | Valor Observado | Diagnóstico Técnico |
| :--- | :--- | :--- |
| **Total de Registros** | 466.178 filas | Volumen completo post-ingesta sin pérdidas de carga |
| **Total de Columnas** | 22 variables | Esquema columnar consolidado |
| **Duplicados Exactos** | 0 filas (0,0%) | No existen filas idénticas redundantes |
| **RIT con Registros Múltiples** | 337.777 filas | Consistente con la naturaleza procesal (múltiples audiencias por causa) |
| **Causas Únicas (por RIT)** | 128.401 causas | Gran diversidad muestral a lo largo de 11 años |
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


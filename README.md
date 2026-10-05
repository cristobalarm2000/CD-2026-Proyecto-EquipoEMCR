# Inteligencia Judicial & Eficiencia Procesal (PJUD Chile)

## Contexto del Proyecto
El proyecto analiza microdatos públicos del **Poder Judicial de Chile (PJUD)** centrados en las **Audiencias Realizadas**, abordando inicialmente la competencia de **Familia**.

- **Cliente Objetivo:** Estudios jurídicos y abogados.
- **Meta General:** Proveer inteligencia de negocio para comparar la eficiencia del sistema judicial entre distintas ramas del derecho y optimizar la gestión estratégica de carteras de causas a nivel regional.
- **Objetivo Actual (MVP):** Generación de un Producto Mínimo Viable (MVP) para validar los pipelines de extracción, transformación y carga (ETL) y el análisis exploratorio de datos (EDA) en la materia de Familia, estableciendo la base analítica para incorporar progresivamente otras materias (Civil, Laboral, Penal) y consolidar la solución final.

---

## Ingesta y Consolidación de Datos
Se realizó la ingesta automatizada de microdatos mediante la API estadística del PJUD bajo los siguientes parámetros:
- **Corte:** Código `30` (Corte de Apelaciones de Valparaíso).
- **Tribunal:** Código `0` (Consolidado regional de los 34 tribunales de la jurisdicción).
- **Materia:** `Familia`.
- **Rango temporal:** `2015` a `2025` (11 períodos anuales).

El proceso extrajo 11 archivos crudos en formato JSON (~238.9 MB en total), los cuales se consolidaron en un dataset columnar **Parquet** de **466.178 registros y 22 columnas** (~7.71 MB), alcanzando una tasa de compresión y ahorro de almacenamiento del 96.8%.

---

## Hallazgos Esenciales de Calidad de Datos
A partir de la auditoría y análisis exploratorio del dataset consolidado, se identificaron los siguientes aspectos clave:

- **Volumen e Integridad General:** Se auditaron 466.178 filas que abarcan 128.401 causas únicas (por RIT). No existen duplicados exactos (0,0%) y 12 de las 22 variables cuentan con completitud absoluta (0% nulos).
- **Variables con Alta Ausencia de Datos:** Campos como `RUC` (90,5%), `ID_CAUSA` (71,6%), `FECHA_FIRMA` (62,7%) y `VIDEOCONFERENCIA` (53,2%) presentan alta tasa de nulos debido a la evolución de los sistemas informáticos judiciales y a cambios normativos (por ejemplo, la obligatoriedad de firma electrónica y audiencias telemáticas introducidas por la Ley 21.226 a partir de finales de 2020).
- **Heterogeneidad Categórica y Textual:** Disparidad en capitalización (mayúsculas y títulos) y acentuación en nombres de tribunales y categorías procesales (`TIPO_PROCEDIMIENTO` y `TIPO_AUDIENCIA`).
- **Disparidad de Formatos:** La modalidad de `VIDEOCONFERENCIA` coexiste en múltiples representaciones (`SI`, `NO`, `1.0`, `0,0`), las marcas horarias se registran como texto (`object`), y las fechas siguen la representación estándar ISO 8601 (`AAAA-MM-DD`) sin componente de hora.

---

## Estructura del Repositorio

```text
├── data/
│   ├── raw/           # JSON crudos extraídos de la API y parquet intermedio
│   └── processed/     # Datasets consolidados y procesados
├── notebooks/         # Cuadernos Jupyter para ETL y análisis exploratorio (EDA)
├── reports/           # Informes técnicos detallados
│   ├── 01_Ingesta_acotada.md
│   └── 02_Auditoria_Calidad_Datos.md
├── src/
│   ├── Api_Caller/    # Cliente de conexión y extracción hacia la API de PJUD
│   └── App/           # Lógica modular y aplicaciones
└── README.md
```

---

## Informes de Referencia
Para consultar el detalle metodológico y los resultados de cada etapa:
- [Informe Técnico de Ingesta Acotada](reports/01_Ingesta_acotada.md)
- [Informe Técnico de Auditoría y Calidad de Datos](reports/02_Auditoria_Calidad_Datos.md)

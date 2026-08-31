# Planificación Semestral: Análisis Predictivo de Congestión en Tribunales de Familia

Este documento detalla la hoja de ruta del proyecto incremental para el taller de ciencia de datos. El objetivo central es identificar qué variables operativas impactan matemáticamente en la prolongación de los juicios de familia y predecir el riesgo de colapso jurisdiccional, utilizando datos centralizados a nivel nacional y aplicando segmentación geográfica programática.

---

## 📍 Avance 1 (Semana 4): Fundamentos, Entorno y Problemática Refinada

* **Pregunta Analítica:** ¿Cuáles son las variables operativas (ej. volumen de ingresos, tiempos efectivos de audiencia) que tienen el mayor peso matemático en la duración de un juicio de familia, y cuál es la probabilidad de colapso en jurisdicciones específicas (ej. C.A. de Valparaíso)?
* **Estrategia de Datos:** 
  * Se utilizan los 6 archivos maestros nacionales del Poder Judicial (Ingresos, Términos, Tramitación, Duración, Audiencias Realizadas, Duración de Audiencias).
  * La segmentación regional se ejecuta **programáticamente mediante código**, evitando descargas fragmentadas y sesgadas desde portales interactivos.
* **Infraestructura y Entorno:** 
  * Inicialización del repositorio único en GitHub.
  * Estructuración base de directorios: `data/raw/`, `data/processed/`, `notebooks/`, `src/`.
  * Configuración de seguridad perimetral mediante `.gitignore` para excluir datasets pesados y entornos virtuales.

---

## 📍 Avance 2 (Semana 7): Pipeline de Preprocesamiento y Diseño Relacional

* **Modelado Entidad-Relación:** 
  * Unificación de los 6 archivos independientes en un *dataframe* analítico maestro.
  * Uso de llaves primarias y foráneas (`ID_CAUSA`, `RIT`, `COD_TRIBUNAL`) para garantizar la trazabilidad de cada caso judicial sin generar redundancias estructurales.
* **Limpieza e Imputación:** 
  * Desarrollo de un pipeline en `pandas` para el tratamiento de valores nulos (ej. fechas de término faltantes) y corrección de anomalías en duraciones de audiencias.
* **Ingeniería de Características (Feature Engineering):** 
  * Creación de variables predictoras derivadas, tales como `tasa_resolucion_mensual` (Ingresos vs. Términos) y `delta_dias_audiencia`.

---

## 📍 Avance 3 (Semana 11): Análisis Exploratorio (EDA) y Modelado Predictivo

* **Análisis Exploratorio (EDA):** 
  * Mapeo visual de cuellos de botella operativos y geográficos.
  * Evaluación de correlaciones entre el tiempo invertido en audiencias y el volumen de causas en tramitación.
* **Entrenamiento de Modelos de Machine Learning:** 
  * **Regresión:** Para estimar la cantidad de días hábiles que durará un proceso.
  * **Clasificación/Series de Tiempo:** Para alertar sobre niveles críticos de saturación en juzgados específicos.
* **Importancia de Variables (Feature Importance):** 
  * Extracción de los pesos matemáticos asignados por el algoritmo a cada factor, entregando la base cuantitativa que explica las demoras operativas (ej. el impacto porcentual de la cantidad de audiencias en la duración total).

---

## 📍 Entrega Final (Semana 15): Automatización y Consolidación Técnica

* **Pipeline Autónomo:** 
  * Refinamiento de los scripts modulares en la carpeta `src/`. El código debe ser capaz de ingerir la data cruda, aplicar filtros jurisdiccionales, cruzar las llaves y exportar predicciones sin intervención manual.
* **Documentación Central:** 
  * Consolidación del `README.md` técnico con instrucciones de despliegue para replicar el entorno desde cero, justificación del esquema de modelado y conclusiones operativas.
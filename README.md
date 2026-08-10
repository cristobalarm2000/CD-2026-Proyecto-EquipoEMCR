# CD-2026-Proyecto-EquipoEMCR
**TALLER 01**

**Integrantes:**
* Cristóbal Rojas
* Emanuel Herrera 

---

# Proyecto 1: Predicción de demanda energética - Cristóbal Rojas

## Comprender el problema

**Contexto:** 
En Chile, la transición hacia una matriz energética basada en energías renovables variables (solar en el norte y eólica en el centro-sur) ha generado un desafío crítico de estabilidad en el Sistema Eléctrico Nacional (SEN). En este escenario realista, la Zona Central y la Región de Valparaíso enfrentan picos severos de demanda durante las horas punta nocturnas (18:00 a 23:00 hrs), justo cuando la generación solar cae a cero. Aunque existen centrales hidroeléctricas de pasada y parques de baterías BESS (System Battery Energy Storage), estos tienen capacidades de almacenamiento limitadas y tiempos de rampa de despacho ajustados. Si la demanda real supera la oferta programada por el Coordinador Eléctrico Nacional, se deben encender de emergencia centrales térmicas de respaldo (altamente costosas y contaminantes) o aplicar cortes no programados por desprendimiento de carga para evitar el colapso de las subestaciones.

**¿Cuál es el problema?**
La alta volatilidad de la demanda en horas punta, combinada con la intermitencia renovable y el alto costo de la generación de respaldo en Chile. El desfase de la curva pato genera riesgos de saturación en la red y obliga a encender plantas térmicas lentas y contaminantes.

**¿Quién toma decisiones?**
* **Coordinador Eléctrico Nacional (CEN):** Opera el sistema y despacha la energía en tiempo real. 
* **Generadoras y Distribuidoras:** Ajustan ofertas y distribución local. 
* **Ministerio de Energía y CNE:** Definen normativas, regulación y metas de descarbonización.

**¿Qué impacto tendría resolverlo?**
Reducción del costo marginal, mayor aprovechamiento de energía limpia con menos emisiones y estabilidad en la red eléctrica.

---

## Preguntas analíticas

### Pregunta Analítica 1: Enfoque de Regresión (Demanda Máxima)
**Pregunta:** ¿Cuál será la demanda máxima de energía (en MW) en el subsistema Central del SEN entre las 18:00 y las 23:00 horas, considerando la temperatura ambiental proyectada, la humedad relativa y la tendencia de consumo de los últimos 7 días?
*   **Variable Objetivo:** Demanda máxima de energía en horas punta (continua, en MW).
*   **Variables Predictoras:** Temperatura mínima y máxima proyectada (°C), Humedad relativa (HL), Consumo registrado en el mismo bloque horario durante los 1, 7 y 14 días previos (MW).
*   **Temporalidad:** Análisis retrospectivo de los últimos 14 días para predecir el comportamiento en la ventana horaria de 18:00 a 23:00 hrs del día en curso.

### Pregunta Analítica 2: Enfoque de Clasificación (Sobrecarga)
**Pregunta:** ¿Cuál es la probabilidad de que una subestación de distribución regional supere el 90% de su capacidad nominal durante un día hábil de invierno, en función del pronóstico del tiempo, el calendario escolar y laboral, y la tasa de electrificación de calefacción en la zona?
*   **Variable Objetivo:** Estado de sobrecarga de la subestación (binaria: `1` = Mayor o igual a 90% / `0` = Bajo 90%).
*   **Variables Predictoras:** Alerta de ola de frío (variable categórica: Sí/No), Tipo de día (día hábil, fin de semana, feriado), Consumo promedio por cliente residencial en las últimas 4 horas, Índice de radiación solar efectiva acumulada durante el día.
*   **Temporalidad:** Predicción orientada a días hábiles de invierno, utilizando acumulados del día y métricas de las últimas 4 horas para inferir el riesgo de sobrecarga inminente.

### Pregunta Analítica 3: Enfoque de Regresión (BESS)
**Pregunta:** ¿Cuánta energía (en MWh) deberán entregar los sistemas de almacenamiento de baterías (BESS) durante la rampa de caída solar (18:30 a 20:00 hrs) para compensar la pérdida de generación fotovoltaica sin encender centrales térmicas?
*   **Variable Objetivo:** Energía total requerida de descarga BESS (continua, en MWh).
*   **Variables Predictoras:** Tasa de caída de la generación solar (MW/minuto) en el norte chico y zona central, Velocidad de viento proyectada en parques eólicos de la Región de Coquimbo y Valparaíso, Tasa de incremento de demanda residencial (MW/minuto).
*   **Temporalidad:** Horizonte de predicción ultra-específico durante el período de rampa (18:30 a 20:00 hrs), evaluando la tasa de cambio minuto a minuto.

---

## Relacionar el proyecto con CRISP-DM

| Fase | ¿Cómo se aplicaría en su proyecto? |
| :--- | :--- |
| **Business Understanding** | Definir la meta de reducir un 15% el uso de generación térmica de respaldo en horas punta y evitar cortes por sobrecarga en el SEN. El éxito se basa en lograr predecir la demanda energética horaria con un MAPE < 1.5% para habilitar el despacho óptimo de renovables y sistemas BESS. |
| **Data Understanding** | Extraer y explorar telemetría y generación desde la API del CEN, clima de la DMC y registros de distribuidoras. Analizar la estacionalidad (invierno/verano), el desfase de la curva pato y la correlación entre temperaturas extremas y consumo. |
| **Data Preparation** | Realizar limpieza mediante el filtrado de anomalías e imputación de telemetría faltante. Construir variables temporales (lags, transformaciones senoidales para horas/días, Grados Día de Calefacción) y resamplear series a intervalos de 15 minutos. |
| **Modeling** | Entrenar modelos aptos para relaciones no lineales (LightGBM, XGBoost) y temporales (redes LSTM/TFT). Utilizar validación expansiva (*Time Series Split*) para evitar filtración de datos y ajustar hiperparámetros enfocados en penalizar errores en los picos máximos. |
| **Evaluation** | Validar el desempeño con métricas como RMSE, MAE y MAPE en conjuntos de prueba cronológicos. Simular el impacto financiero (ahorro en MWh térmicos) y ejecutar pruebas de estrés (ej. frentes de frío repentinos). |
| **Deployment** | Implementar los modelos a través de una API REST integrada al centro de control del CEN. Monitorear derivas de concepto (*Concept Drift*) en tiempo real y establecer un pipeline de reentrenamiento continuo semanal. |

---

# Proyecto 2: Esperas Hospitalarias - Emanuel Herrera

## Comprender el problema

**¿Cuál es el problema?**
La alta congestión y tiempos de espera impredecibles en el Servicio de Urgencias del hospital. Esto provoca la frustración de los pacientes, el abandono de los recintos sin recibir atención y una severa sobrecarga reactiva para el personal de salud.

**¿Quién toma decisiones?**
La dirección del hospital y la jefatura médica de Urgencias. Ellos son los responsables directos de gestionar los recursos clínicos, asignar al personal de turno y administrar la disponibilidad de camas.

**¿Qué impacto tendría resolverlo?**
Contar con estimaciones de espera permitiría gestionar transparentemente las expectativas del paciente. Además, habilitaría a los tomadores de decisiones para anticipar cuellos de botella y reasignar personal proactivamente, reduciendo el colapso, optimizando los escasos recursos y mejorando radicalmente la calidad y oportunidad de la atención clínica.

---

## Preguntas analíticas

### Pregunta Analítica 1: Enfoque de Regresión
**Pregunta:** ¿Qué factores operativos, temporales y demográficos determinan el tiempo exacto que un paciente deberá esperar en Urgencias antes de recibir su primera atención médica?
*   **Variable objetivo:** Tiempo de espera total (medido en minutos continuos desde la finalización del triage hasta el primer contacto médico).
*   **Variables predictoras posibles:** Nivel de urgencia asignado en el triage (C1 - C5), Cantidad total de pacientes que ya se encuentran en la sala de espera, Número de médicos especialistas y generales con turno activo, Edad del paciente, Hora de llegada y día de la semana.
*   **Temporalidad:** Entrenamiento utilizando registros históricos continuos de los últimos 2 a 3 años. La predicción se realiza en **tiempo real** en el instante exacto en que el paciente finaliza su triage, con variables operativas actualizándose en ventanas de 15 a 30 minutos.

### Pregunta Analítica 2: Enfoque de Clasificación
**Pregunta:** ¿Qué variables influyen en la probabilidad de que un paciente de urgencias supere el umbral crítico de tolerancia establecido por el hospital (por ejemplo, más de 120 minutos de espera)?
*   **Variable objetivo:** Alerta de espera prolongada (Variable binaria: `1` si el paciente espera más de 120 minutos, `0` si espera 120 minutos o menos).
*   **Variables predictoras posibles:** Tasa de ocupación actual de camas de hospitalización, Categoría de triage del paciente, Mes del año (para capturar la estacionalidad de enfermedades), Medio de llegada al hospital, Proporción de pacientes respecto al personal médico en el momento del ingreso.
*   **Temporalidad:** Entrenamiento basado en ciclos anuales completos (mínimo 2 años) para capturar los picos estacionales de invierno y verano. El horizonte de inferencia es **inmediato al ingreso**, evaluando el riesgo de espera prolongada desde el momento en que el paciente cruza la puerta.

---

## Relacionar el proyecto con CRISP-DM

| Fase | ¿Cómo se aplicaría en su proyecto? |
| :--- | :--- |
| **Business Understanding** | Comprender el problema de congestión en Urgencias del hospital, definiendo el objetivo de negocio: predecir los tiempos de espera para optimizar la asignación proactiva de recursos médicos y gestionar las expectativas de los pacientes. |
| **Data Understanding** | Extraer y explorar los registros históricos del hospital (últimos 2-3 años). Analizar qué datos están disponibles (niveles de triage, horas de ingreso, personal de turno) y evaluar su calidad (identificar registros incompletos o inconsistentes). |
| **Data Preparation** | Limpiar los datos manejando valores nulos y eliminando anomalías (outliers) en los tiempos registrados. Construir nuevas variables (feature engineering), como el cálculo de "pacientes en sala" o la categorización de "bloques horarios". |
| **Modeling** | Seleccionar y entrenar algoritmos de Machine Learning (enfocados en regresión, como Random Forest o Regresión Lineal) utilizando los datos históricos preparados para predecir la variable objetivo: el tiempo de espera en minutos. |
| **Evaluation** | Medir la precisión de las predicciones del modelo utilizando métricas de error (como MAE o RMSE). Validar con la dirección del hospital y la jefatura médica si el nivel de exactitud alcanzado cumple con los requerimientos operativos reales. |
| **Deployment** | Integrar el modelo predictivo en los sistemas informáticos del hospital para que genere estimaciones en tiempo real. Desplegar un panel de control (dashboard) para la jefatura y conectar los tiempos estimados a las pantallas de la sala de espera. |
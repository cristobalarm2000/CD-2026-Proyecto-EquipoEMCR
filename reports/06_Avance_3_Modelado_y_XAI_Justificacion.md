# Reporte Técnico y Guía de Defensa — Avance 3: Modelado Supervisado, Evaluación de Errores y Explicabilidad (XAI)

**Proyecto:** Plataforma de Inteligencia Judicial & Eficiencia Procesal (Competencia Familia — C.A. de Valparaíso, 2015–2025)  
**Equipo:** EMCR  
**Asignatura:** Taller de Ciencia de Datos — Profesor Jesús A. Parra  
**Alineación Metodológica:** Estrictamente ceñido a **Taller 5 (`Clase 06 - Modelos`)**, **Taller 6 (`Clase 07 - Validación, Bootstrap y XAI`)** y la pauta oficial de evaluación **`Avance 3.pdf` (100 puntos)**.

---

## 1. Diagnóstico Especializado del Proyecto desde la Ciencia de Datos Jurídica (LegalTech)

Actuando como especialista en Ciencia de Datos y consultor estratégico para estudios jurídicos y litigantes en Derecho de Familia, el análisis integral del repositorio (`CD-2026-Proyecto-EquipoEMCR`) permite establecer la trazabilidad completa entre lo construido en los Avances 1–2 y la solución predictiva del Avance 3:

1. **Solidez del Activo de Datos (`data/processed/audiencias_preparadas_modelo.parquet`)**:
   - Universo auditado de **466.178 audiencias realizadas** correspondientes a **280.795 causas únicas (`ID_CAUSA_RIT`)** tramitadas en los **15 tribunales con competencia de Familia** de la jurisdicción de la Corte de Apelaciones de Valparaíso (Código 30) entre **2015 y 2025**.
   - Saneamiento forense documentado en `reports/02_Auditoria_Calidad_Datos.md`: rescate íntegro del lote 2023 mediante cruce por clave compuesta, resolución de 62.587 colisiones de `RIT` agregando el prefijo de `COD_TRIBUNAL`, eliminación de registros truncados post-corte e imputación determinista verificada (0,0% nulos y 0,0% duplicados exactos).

2. **Conexión Directa entre los Hallazgos del EDA (Avance 2) y las Decisiones de Modelado (Avance 3)**:
   - **Asimetría extrema y colas pesadas en `PLAZO_AGENDAMIENTO`**: El plazo en días hábiles (Lunes a Sábado entre `FECHA_PROGRAMACION` y `FECHA_AUDIENCIA`) presenta mediana de 26 días, media de 31,4 días, P75 de 43 días, P90 de 64 días y máximo de 339 días.
   - **Poder discriminante de `TIPO_AUDIENCIA` ($\eta^2 = 10,9\%$)** y **brecha territorial de 2,5x a 3,0x entre tribunales**: En el EDA se demostró que mientras una audiencia cautelar o inmediata se fija en $< 10$ días y una preparatoria en Limache demora una mediana de 13 días, una `Audiencia de Juicio` en Viña del Mar o Casablanca duplica o triplica la espera (56 a 62 días de mediana). Esto justifica comparar modelos lineales aditivos (`LogisticRegression`) frente a **ensambles basados en árboles (`RandomForest`, `CatBoost`, `XGBoost`)** capaces de capturar interacciones no lineales específicas `TRIBUNAL × TIPO_AUDIENCIA × TIPO_PROCEDIMIENTO`.
   - **Cambio de régimen estructural post-2020 (Ley N° 21.226 y Ley N° 21.394)**: La tasa de audiencias con **Congestión Severa ($> 60$ días hábiles)** pasó de **1,7%–4,7% en 2015–2019** a **22,0%–25,2% en 2021–2023**, estabilizándose en **15,6% en 2024–2025**. Este hallazgo fundamenta nuestra decisión de **entrenar sobre el régimen vigente post-pandemia (`2021–2023`)** y evaluar sobre el futuro (`2024–2025`), demostrando empíricamente que mezclar datos pre-2020 degrada severamente la calibración y hunde el *Recall*.

---

## 2. Definición Rigurosa del Problema ($X$, $y$, $T$) e Higiene Anti-Fuga (*Zero Data Leakage*)

### 2.1 Pregunta Predictiva y Utilidad en el Estudio Jurídico
- **Pregunta Predictiva:** *Al instante exacto $T = \text{FECHA\_PROGRAMACION}$ en que el tribunal dicta la resolución que fija una audiencia de Familia, ¿superará la espera los **60 días hábiles** ($y = 1$, más del doble del plazo legal máximo de 30 días establecido en los artículos 59 y 61 de la Ley N° 19.968)?*
- **Utilidad Práctica para Abogados:**
  1. **Cotización inteligente de honorarios (*Smart Pricing*):** Evita pactar honorarios fijos subvalorados en causas que sufrirán demoras severas ($> 3$ meses calendario), permitiendo estructurar cobros por hitos procesales.
  2. **Acción cautelar temprana:** Cuando el modelo emite una alerta de congestión severa ($\hat{p} \ge 0,35$), el abogado litigante solicita de inmediato alimentos provisorios, régimen comunicacional provisorio o presenta escrito de habilitación de sala.
  3. **Gestión de expectativas del patrocinado:** Sustituye estimaciones intuitivas por probabilidades empíricas respaldadas por explicabilidad local (`SHAP Waterfall`).

### 2.2 Especificación de Entradas ($X$), Salida ($y$) y Variables Prohibidas
- **Salida ($y$):** `Y_SEVERA = 1` si `PLAZO_AGENDAMIENTO > 60` días hábiles L–S; `0` si `PLAZO_AGENDAMIENTO <= 60`.
- **Entradas Válidas en $T = \text{FECHA\_PROGRAMACION}$ ($X$ — 8 predictores):**
  1. `TRIBUNAL_CORTO` (Categórica, 15 juzgados de la C.A. de Valparaíso).
  2. `TIPO_AUDIENCIA` (Categórica: `AUDIENCIA DE JUICIO`, `AUDIENCIA PREPARATORIA`, `AUDIENCIA ESPECIAL`, `INMEDIATA`, etc.).
  3. `TIPO_PROCEDIMIENTO` (Categórica: `ORDINARIO`, `VIOLENCIA INTRAFAMILIAR`, `PROTECCION`, `ESPECIAL`, etc.).
  4. `MACRO_MATERIA` (Categórica derivada del prefijo RIT: `Ordinario_Contencioso_C`, `Violencia_Intrafamiliar_F`, `Proteccion_NNA_P`, etc.).
  5. `VIDEOCONFERENCIA_INT` (Binaria 0/1 fijada en la resolución de programación).
  6. `ORDEN_AUDIENCIA_CAUSA` (Numérica discreta: $1^{\text{a}}, 2^{\text{a}}, 3^{\text{a}}\dots$ audiencia agendada en la misma causa `ID_CAUSA_RIT` hasta la fecha $T$).
  7. `MES_PROG` (Numérica 1–12: captura estacionalidad judicial como feriado de febrero e ingreso masivo de marzo).
  8. `DIA_SEM_PROG` (Numérica Lunes–Sábado).
- **Variables Prohibidas Excluidas por Fuga de Información (*Data Leakage*):**
  - `DIAS_TRAMITACION_PREVIA` ($= \text{FECHA\_AUDIENCIA} - \text{FECHA\_INGRESO}$, contiene la fecha futura de la audiencia), `FECHA_AUDIENCIA`, `ANO_AUDIENCIA`, `MES_AUDIENCIA`, `DURACION_MINUTOS`, `TRAMO_DURACION`, `FLG_AUDIENCIA_FRUSTRADA`, `TOTAL_AUDIENCIAS_CAUSA` y `TRAMO_AGENDAMIENTO`.

---

## 3. Resultados de Validación Cruzada, Rendimiento en Test, Umbral y Bootstrap

### 3.1 Estabilidad en Validación Cruzada Estratificada (5-Fold `StratifiedKFold` en Train 2021–2023, $n = 130.057$)

Siguiendo estrictamente el flujo de **Taller 6 (`1. Separar Test -> 2. Validar en Train con CV -> 3. Evaluar en Test`)**, encapsulamos el preprocesamiento (`ColumnTransformer`: `OneHotEncoder(handle_unknown='ignore')` + `StandardScaler()`) dentro de un `Pipeline` para que se ajuste exclusivamente sobre los folds de entrenamiento:

| Modelo / Algoritmo | ROC-AUC Medio ($M_{CV}$) | Desv. Est. ROC-AUC ($s_{CV}$, `ddof=1`) | Average Precision Media ($M_{CV}$) | Desv. Est. AP ($s_{CV}$, `ddof=1`) | Recall Medio (@0,50) | F1 Medio (@0,50) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **0. Dummy Basal (`most_frequent`)** | 0,5000 | 0,0000 | 0,2343 | 0,0000 | 0,0000 | 0,0000 |
| **1. Regresión Logística (`Pipeline`)** | 0,8286 | 0,0035 | 0,5775 | 0,0048 | 0,4683 | 0,5364 |
| **2. Random Forest (`Pipeline`)** | 0,8705 | 0,0024 | 0,6659 | 0,0037 | 0,4733 | 0,5794 |
| **3. CatBoost (`Pipeline`)** | 0,8834 | 0,0023 | 0,6860 | 0,0055 | 0,5692 | 0,6236 |
| **4. XGBoost (`Pipeline`)** | **0,8829** | **0,0020** | **0,6857** | **0,0040** | **0,5679** | **0,6226** |

- **Interpretación de Estabilidad (Taller 6):** La desviación estándar entre folds es extraordinariamente baja ($s_{CV} \le 0,0055$ en AP y $\le 0,0035$ en ROC-AUC), y la ventaja de los ensambles de árboles sobre la Regresión Logística ($+0,108$ puntos de AP en CV) supera en más de **20 veces** la desviación estándar entre folds, confirmando una superioridad real y no atribuible al azar de la partición.

### 3.2 Rendimiento Comparado en Conjunto de Prueba Out-of-Time (`2024–2025`, $n = 83.410$, Prevalencia Positiva $= 15,59\%$)

| Algoritmo | Train ROC-AUC | Test ROC-AUC | Test AP (Lift vs. Azar) | Acc (@0,50) | Prec (@0,50) | Recall (@0,50) | F1 (@0,50) | Prec (@0,35) | Recall (@0,35) | F1 (@0,35) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0. Dummy Basal** | 0,5000 | 0,5000 | 0,1559 (1,0x) | 0,8441 | 0,0000 | 0,0000 | 0,0000 | 0,0000 | 0,0000 | 0,0000 |
| **1. Regresión Logística** | 0,8290 | 0,8265 | 0,4493 (2,9x) | 0,8372 | 0,4713 | 0,3658 | 0,4119 | 0,4353 | 0,5724 | 0,4945 |
| **2. Random Forest** | 0,8738 | 0,8518 | 0,4795 (3,1x) | **0,8541** | **0,5478** | 0,3650 | 0,4381 | **0,4168** | 0,6041 | 0,4932 |
| **3. CatBoost** | 0,8880 | **0,8608** | 0,4801 (3,1x) | 0,8468 | 0,5089 | 0,4809 | 0,4945 | 0,4048 | 0,6718 | 0,5052 |
| **4. XGBoost (Elegido)** | 0,8869 | 0,8600 | **0,4843 (3,1x)** | 0,8466 | 0,5081 | **0,4863** | **0,4970** | 0,4079 | **0,6792** | **0,5097** |

### 3.3 Demostración Empírica del Cambio de Régimen (Train `2015–2023` vs. Train `2021–2023`)
- Si entrenamos `XGBoost` sobre la serie histórica completa `2015–2023` ($N = 379.745$, donde la prevalencia de demora $>60$d era de solo $10,77\%$ por la época pre-pandemia), al evaluar en el mismo Test `2024–2025` el **Recall (@0,50) cae de 48,6% a 17,3%** y el **AP cae de 0,484 a 0,420**.
- **Justificación:** Incluir el régimen pre-pandemia sesga el valor base $E[f(X)]$ hacia abajo, haciendo que el modelo subestime sistemáticamente las demoras actuales. Entrenar en `2021–2023` alinea el modelo con la operación judicial vigente bajo la Ley N° 21.394.

### 3.4 Cuantificación de Incertidumbre en Test vía Bootstrap ($B = 500$ réplicas con reemplazo)
Siguiendo el procedimiento del **Taller 6**:
- **XGBoost AP en Test:** `0,4843` — **IC 95% Percentil:** `[0,4752, 0,4928]` (0 réplicas omitidas).
- **Random Forest AP en Test:** `0,4795` — **IC 95% Percentil:** `[0,4704, 0,4893]`.
- **Regresión Logística AP en Test:** `0,4493` — **IC 95% Percentil:** `[0,4402, 0,4587]`.
- **Remuestreo Pareado $\Delta\text{AP} = \text{AP}_{\text{XGBoost}} - \text{AP}_{\text{LogReg}}$:** Puntual `+0,0351` — **IC 95% Percentil:** `[+0,0289, +0,0418]`. Como el intervalo excluye completamente el `0`, la ventaja del ensamble no lineal sobre el modelo lineal es estadísticamente significativa al 95%.
- **Qué variabilidad captura y cuál no (Concepto clave de Taller 6):** Este bootstrap mantiene fijo el modelo ajustado en `Train`; por tanto, mide la incertidumbre debida al muestreo finito del conjunto de prueba (`Test`), pero **no** captura la variabilidad de reentrenar el algoritmo sobre muestras de entrenamiento distintas (la cual ya fue evaluada mediante el `StratifiedKFold` en `Train`).

---

## 4. Explicabilidad Global y Local con SHAP (Criterios 6 y 7 — 30 puntos)

### 4.1 Explicabilidad Global (`shap.plots.beeswarm` sobre $n = 2.000$ observaciones estratificadas de Test)
- **Escala declarada:** Salida del `TreeExplainer` en **log-odds** ($\ln\frac{p}{1-p}$), donde valores positivos empujan la predicción hacia Congestión Severa ($> 60$ días hábiles) y valores negativos hacia agendamiento normal ($\le 60$ días).
- **Top Variables y Coherencia con el EDA:**
  1. `Audiencia: AUDIENCIA DE JUICIO` y `Procedimiento: ORDINARIO`: Aportan los mayores valores SHAP positivos (más de $+1,0$ log-odds), reflejando la escasez de bloques largos de sala para rendición de prueba.
  2. `Procedimiento: VIOLENCIA INTRAFAMILIAR` y `PROTECCION` / `Audiencia: INMEDIATA` o `ESPECIAL`: Aportan valores SHAP fuertemente negativos ($-1,5$ a $-3,0$ log-odds) debido al mandato legal de priorización cautelar.
  3. **Efecto Territorial (`TRIBUNAL`):** Juzgados con alta congestión en juicio o preparatoria (`J.F. Viña del Mar`, `J.F. Casablanca`, `J.F. La Ligua`) desplazan el log-odds al alza, mientras que `J.F. Limache`, `J.F. Quilpué` y `J.F. San Antonio` restan riesgo de demora severa.
  4. `N° Orden Audiencia en Causa`: A mayor número de audiencias previas en la misma causa RIT (continuaciones de juicio o reprogramaciones), mayor contribución positiva al riesgo de demora.
- **Principio de No Causalidad (Taller 6):** SHAP describe cómo el modelo utiliza las correlaciones del conjunto de datos para predecir, pero **no demuestra causalidad intervencional**.

### 4.2 Explicabilidad Local (`shap.plots.waterfall` en 3 Casos Concretos de Test)
Partiendo del valor base del modelo en log-odds $E[f(X)] = -1,291$ (equivalente a una probabilidad base de $\sim 21,6\%$):

1. **Caso Local 1 — Acierto de Alto Riesgo (Verdadero Positivo: `RIT 1271-C-1836-2024`)**:
   - **Contexto:** `AUDIENCIA DE JUICIO` en procedimiento `ORDINARIO` ante el `J.F. Viña del Mar`.
   - **Real vs. Predicho:** Espera real $y = 98$ días hábiles ($y = 1$). El modelo `XGBoost` predice $\hat{p} = 87,0\%$ ($f(x) = +1,90$ log-odds).
   - **Factores impulsores (`Waterfall`):** La combinación de `Audiencia: AUDIENCIA DE JUICIO`, `Tribunal: J.F. Viña del Mar`, `Procedimiento: ORDINARIO` y mes de programación suma $+3,19$ log-odds sobre la línea base. Permite al estudio jurídico anticipar más de 4 meses calendario de espera.

2. **Caso Local 2 — Acierto de Vía Rápida (Verdadero Negativo: `RIT 1268-P-931-2025`)**:
   - **Contexto:** Audiencia `INMEDIATA` en procedimiento de `PROTECCION` ante el `J.F. San Felipe`.
   - **Real vs. Predicho:** Espera real $y = 0$ días hábiles ($y = 0$, agendada en el día). El modelo `XGBoost` predice $\hat{p} = 0,0\%$ ($f(x) = -8,41$ log-odds).
   - **Contraste con Caso 1:** Aquí la naturaleza cautelar urgente (`PROTECCION` + `INMEDIATA`) empuja los valores SHAP masivamente hacia la izquierda, descartando cualquier alerta de congestión.

3. **Caso Local 3 — Error Relevante para Diagnóstico Forense (Falso Negativo: `RIT 1264-F-416-2023`)**:
   - **Contexto:** Audiencia en materia de `VIOLENCIA INTRAFAMILIAR` ante el `J.F. Los Andes`.
   - **Real vs. Predicho:** Espera real $y = 91$ días hábiles ($y = 1$), pero `XGBoost` predijo $\hat{p} = 12,0\%$ (`Random Forest` $= 11,4\%$, `Regresión Logística` $= 10,8\%$).
   - **¿Por qué fallaron los tres algoritmos?:** El gráfico *Waterfall* muestra que todas las variables estructurales observables en el agendamiento (`VIF`, `J.F. Los Andes`) empujan hacia una tramitación rápida ($f(x) = -1,99$ log-odds). Sin embargo, en la práctica forense de Familia, ciertas causas sufren demoras extremas por **factores exógenos no registrados en la tabla estadística de agendamiento** (solicitud de informes periciales externos al SML o DAM, imposibilidad de notificar personalmente al denunciado por receptor judicial o suspensión previa de común acuerdo).

---

## 5. Cumplimiento Íntegro de la Rúbrica Oficial (`Avance 3.pdf` — 100 Puntos)

| Criterio de Evaluación (`Avance 3.pdf`) | Pond. | Cómo se cumple al 100% en nuestra entrega | Lámina PPTX |
| :--- | :---: | :--- | :---: |
| **1. Motivación y objetivo** | **5%** | Problema jurídico-económico en Familia, pregunta predictiva en $T=\text{FECHA\_PROGRAMACION}$, criterio de éxito cuantitativo. | Lámina 1 |
| **2. Datos, $X$, $y$ y EDA** | **5%** | 466.178 audiencias PJUD, 8 predictores sin fuga, 2 hallazgos visuales del EDA (cambio de régimen post-2020 y $\eta^2=10,9\%$ de `TIPO_AUDIENCIA`). | Lámina 2 |
| **3. Solución y validación** | **15%** | 4 algoritmos de distintas familias + `Dummy` basal, encapsulados en `Pipeline`, partición temporal + 5-Fold `StratifiedKFold` y comparación Train vs Test. | Láminas 3 y 4 |
| **4. Métricas de rendimiento** | **10%** | Tabla completa en CV, Train y Test (`ROC-AUC`, `AP`, `Accuracy`, `Precision`, `Recall`, `F1`), declarando clase positiva ($15,6\%$) y umbrales $0,50$ vs $0,35$. | Lámina 4 |
| **5. Gráficos y análisis de errores** | **15%** | Curvas ROC y Precision–Recall con `predict_proba` y línea de prevalencia positiva + Matrices de Confusión + Bootstrap $B=500$ e interpretación del costo FN vs FP. | Láminas 5 y 6 |
| **6. Explicabilidad global** | **15%** | `shap.plots.beeswarm` sobre muestra identificada de Test ($n=2.000$), escala en `log-odds`, sentido de efectos, vínculo con EDA y advertencia de no causalidad. | Lámina 7 |
| **7. Explicabilidad local** | **15%** | 3 casos reales del Test (`VP`, `VN` y `FN` forense) con `shap.plots.waterfall`, relacionando $E[f(X)]$, $\phi_j$ y $f(x)$ con interpretación jurídica. | Láminas 8 y 9 |
| **8. Conclusión** | **10%** | Recomendación fundamentada de `XGBoost` (umbral $0,35$), 1 limitación concreta (variables periciales latentes/supervivencia) y 1 mejora (cola móvil 30d + Jurimetría). | Lámina 10 |
| **9. Comunicación y defensa** | **10%** | Diseño ejecutivo de 10 láminas para 7 minutos (40s/lámina) + 2 láminas de anexo con el árbol individual (`max_depth=3`) y respuestas a las 4 preguntas del profesor. | Láminas 1–12 |

---

## 6. Guion Cronometrado de Exposición (7 Minutos Exactos)

- **Minuto 0:00 – 0:45 (Lámina 1 — Motivación y Objetivo):** Presentar el dolor real de un estudio jurídico en Familia: la ley promete audiencias en 30 días hábiles, pero la cola llega a 339 días. Definir la pregunta predictiva en $T = \text{FECHA\_PROGRAMACION}$: predecir si la audiencia superará los **60 días hábiles** ($y=1$) para ajustar honorarios y activar cautelares.
- **Minuto 0:45 – 1:30 (Lámina 2 — Datos, $X$, $y$ y EDA):** Destacar las 466.178 audiencias oficiales de los 15 tribunales de Valparaíso, las 8 variables conocidas sin fuga de futuro y los 2 gráficos del EDA: el salto estructural post-2020 y el dominio de `TIPO_AUDIENCIA` ($\eta^2 = 10,9\%$).
- **Minuto 1:30 – 2:20 (Lámina 3 — Solución y Validación):** Explicar el flujo de Taller 5 y 6: `Pipeline` con `OneHotEncoder` y `StandardScaler` ajustado solo en `train`, validación cruzada estratificada de 5 folds en el régimen vigente (`2021–2023`) y la prueba empírica de que entrenar con `2015–2023` hunde el Recall por sesgo pre-pandemia.
- **Minuto 2:20 – 3:10 (Lámina 4 — Tabla de Métricas):** Mostrar por qué `Accuracy` engaña ($84,4\%$ en el modelo `Dummy` con $0\%$ de Recall), destacar la ausencia de sobreajuste entre Train y Test, y comparar `Regresión Logística` ($AP = 0,449$) vs `Random Forest` ($0,480$) vs `XGBoost` ($0,484$, **3,1 veces mejor que el azar**).
- **Minuto 3:10 – 4:15 (Láminas 5 y 6 — Curvas ROC/PR, Umbral y Bootstrap):** Señalar en la curva PR la línea de prevalencia positiva ($15,6\%$) y el cambio de umbral de $0,50$ a $0,35$ para reducir los Falsos Negativos (elevando el Recall de $48,6\%$ a **$67,9\%$**). Mencionar el intervalo bootstrap 95% de la diferencia $\Delta\text{AP}$ (`[+0,029, +0,042]`) que confirma superioridad estadística.
- **Minuto 4:15 – 5:10 (Lámina 7 — Explicabilidad Global SHAP):** Explicar el *Beeswarm* en escala `log-odds` sobre $n = 2.000$ casos de Test: `Audiencia de Juicio` y tribunales como Viña del Mar o Casablanca empujan el riesgo hacia arriba; `VIF`, `Protección` y tribunales como Limache lo reducen. Recordar que SHAP no implica causalidad.
- **Minuto 5:10 – 6:15 (Láminas 8 y 9 — Explicabilidad Local en 3 Casos):** Contrastar el **Caso 1 (VP: Juicio en Viña del Mar, 98 días reales, $\hat{p}=87\%$)** y el **Caso 2 (VN: Inmediata en San Felipe, 0 días, $\hat{p}=0\%$)** con el **Caso 3 (FN: Audiencia VIF en Los Andes que tardó 91 días pese a $\hat{p}=12\%$)**, explicando que el error se debe a diligencias externas no registradas (peritajes SML/DAM o notificación por receptor).
- **Minuto 6:15 – 7:00 (Lámina 10 — Conclusión):** Cerrar recomendando `XGBoost` en `Pipeline` con umbral $0,35$, declarar la limitación de variables exógenas latentes y proponer como siguiente paso incorporar el *rolling backlog* de 30 días y cruzar con las 40.446 sentencias del módulo de Jurimetría PJUD.

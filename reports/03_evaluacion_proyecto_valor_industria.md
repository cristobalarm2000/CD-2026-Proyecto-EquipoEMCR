# Evaluación del proyecto EMCR y su valor para la industria legal

**Alcance revisado:** README, app Streamlit (5 páginas), notebooks ETL/EDA, informes en `reports/`, infografía y el parquet final (lo validé directamente: 466.178 filas × 36 columnas, 15 tribunales, 280.795 causas, mediana de espera de 26 días, P75 de 43 y P90 de 64).

---

## 1. Veredicto general

| Dimensión | Nota (1–5) | Comentario |
|---|:---:|---|
| Ingeniería de datos (ETL) | **4,5** | Es el punto más fuerte. Rescataron el lote 2023, crearon la clave `ID_CAUSA_RIT`, dejaron 0 nulos con criterio jurídico y pasaron de unos 700 MB a 10,8 MB. |
| Rigor analítico (EDA) | **4,0** | Identifican la fuga de información, la no independencia por causa y la paradoja de Simpson en la modalidad remota. Pocos proyectos académicos llegan a este nivel de detalle. |
| Producto / UX | **3,5** | Hay un dashboard funcional con 5 vistas de negocio, pero sigue orientado al analista y no al abogado (no entrega una respuesta directa del tipo "¿cuándo será mi audiencia?"). |
| Propuesta de valor | **3,5** | El problema es real y está bien planteado. El valor demostrado hoy es **descriptivo**: el predictivo y el prescriptivo están prometidos, pero no construidos. |
| Preparación comercial | **2,0** | Sin modelo predictivo, sin actualización automática ni despliegue, y con alcance de 1 corte de 17 y 1 materia. |
| **Global** | **≈ 3,5 / 5** | Es un **MVP analítico sólido** con valor comercial **plausible pero todavía no validado**. |

---

## 2. ¿Qué valor genera para la industria?

### 2.1 Problema que resuelve
Hoy los plazos judiciales se estiman por **intuición del abogado senior**. El proyecto muestra con datos que esa intuición falla de forma sistemática:

- **Brecha territorial de unas 2,5×:** la mediana va de 16–19 días (Isla de Pascua, Quilpué, Limache) a 35–40 días (Quintero, La Ligua). En 2022–2025 la brecha llega a 18 contra 74 días.
- **Deriva temporal:** la mediana subió de 19 días (2015) a 42 (2022) y volvió a 28–29 (2024–25). Un abogado que se basa en su experiencia previa a 2020 subestima la espera.
- **El tipo de audiencia es el principal factor** (η² ≈ 11 %): una causa que no se resuelve en la preparatoria suma unos 2 meses antes del juicio.

### 2.2 Valor por tipo de cliente

| Segmento | Dolor | Valor que entrega el proyecto | Disposición a pagar |
|---|---|---|---|
| **Estudios de familia pequeños y medianos** (mayoría del mercado) | Clientes ansiosos que preguntan "¿cuándo?" y presupuestos que se desfasan | Rangos de plazo por tribunal y tipo de audiencia para comunicar al cliente y cotizar | Media-baja (son sensibles al precio) |
| **Clínicas jurídicas, CAJ, Defensoría, OPD/Mejor Niñez** | Asignar abogados con carga de causas masiva | Planificación de capacidad por semana, tribunal y bloque horario | Media (presupuesto público, ciclo de venta largo) |
| **Departamentos legales corporativos / aseguradoras** | Provisionar contingencias y plazos | Benchmarks de duración por jurisdicción | Alta, pero Familia les interesa poco: **el valor aparece cuando escalen a Laboral y Civil** |
| **Poder Judicial / CAPJ / Ministerio de Justicia / academia** | Gestión de congestión y evaluación de políticas (Ley 21.226 / 21.394) | Diagnóstico de cuellos de botella y efecto de la virtualidad | Baja en lo monetario, **alta en reputación y alianzas** |
| **Legaltech existentes** (Lemontech CaseTracking, Lexgo, etc.) | Ya siguen causas, pero no predicen plazos | Módulo de "predicción de plazo" vía API o licencia de datos | **Probablemente el canal más realista** |

### 2.3 Cuantificación ilustrativa
> [!NOTE]
> Los supuestos son hipotéticos y hay que validarlos con entrevistas a estudios. Sirven para dimensionar el orden de magnitud, no como proyección.

Para un estudio de familia con **150 causas activas** (≈ 2,6 audiencias por causa según el dataset, unas 390 audiencias al año):

- **Comunicación con el cliente:** si una estimación confiable evita unos 20 minutos de llamadas o correos por causa al año → **≈ 50 h/año**.
- **Pricing:** cotizar con el riesgo de continuación (P75 en vez de la mediana) reduce el trabajo no cobrado en tarifas planas. Basta con evitar un 5 % de subcobro para cubrir varias veces el costo de una suscripción.
- **Agenda:** el mapa de saturación por día y bloque reduce los choques de comparecencia entre abogados del mismo estudio.

Con estos supuestos, una suscripción de **1–3 UF/mes por estudio** sería defendible para el segmento pequeño y mediano.

---

## 3. Ventajas competitivas y debilidades estratégicas

**Fortalezas defendibles**
- **Conocimiento de la calidad de los datos del PJUD:** el lote 2023 con columnas corridas, los 41.439 RIT inválidos y las inversiones de fecha. Esto no se replica en una tarde y es la barrera de entrada real.
- **Fundamento jurídico de las decisiones** (Ley 19.968 para eliminar `FECHA_FIRMA`, las épocas normativas). Da credibilidad frente a abogados.
- **Escalamiento ya probado:** los JSON **nacionales** de Familia (`__0_0_Familia_*`, unos 1,9 GB contra 0,27 GB de Valparaíso, cerca de **7×**) ya se descargaron con éxito una vez. Ya no están en disco, pero siguen en el historial de git (commit `352dcd4`).

**Debilidades**
- **Los datos son públicos:** el valor depende del procesamiento y de la actualización continua, no del dato en sí. Un competidor con recursos (Lemontech) podría replicarlo.
- **No hay datos de resultado** (sentencias, acuerdos, montos de alimentos). No se puede ofrecer la "probabilidad de ganar", que es lo que más se paga en litigation analytics.
- **Sesgo de supervivencia:** el dataset contiene solo audiencias **realizadas**. `FLG_AUDIENCIA_FRUSTRADA` = 0,2 %, así que la tasa real de suspensión es invisible y el "riesgo de costos" queda subestimado.
- **Métrica parcial:** `PLAZO_AGENDAMIENTO` mide de la programación a la audiencia. Al cliente le importa más **del ingreso a la primera audiencia** y **del ingreso al término**, que se pueden calcular con `FECHA_INGRESO`.

---

## 4. Inconsistencias que conviene corregir antes de presentar

> [!WARNING]
> Un evaluador o un cliente las detectará y restan credibilidad a un proyecto cuyo argumento central es la calidad de los datos.

1. ✅ **Corregido. Número de tribunales:** la [infografía](file:///c:/Users/frero/CD-2026-Proyecto-EquipoEMCR/visualizacion%20BI/infografia_audiencias_familia.html) decía **"34 tribunales"** (variantes de escritura del nombre en el dato crudo), pero los tribunales reales son **15**.
2. ✅ **Corregido (infografía, app y notebook 03). Cifras por tribunal:** Quintero 74 → 75 y P75 90 → 93; se rotularon el período y el criterio de selección; en el hallazgo 1, "37 a 42" → "39 a 42" y "casi 3x" → "2,5x general / 3x en preparatorias"; y en la sección 8, "cuadruplican" → "triplican".
3. ✅ **Corregido (ETL, EDA app y notebooks 01, 02 y 03). Videoconferencia (2020 vs 2021):** se precisó que los 248.137 nulos abarcan 2015–2020 completo (la API comenzó a poblar el campo en 2021); se sincronizó la nota de correlación y se calculó la composición de la paradoja de Simpson para 2021–2025 (15,1 % vs 38,6 % Juicios) junto con el acumulado histórico, explicitando la imputación de 2020.
4. ✅ **Corregido. `requirements.txt` y `README.md`:** se generó `requirements.txt` con las dependencias exactas y se actualizó `README.md` incorporando la página 5, los notebooks de EDA 02 y 03, el árbol de archivos actualizado y removiendo todos los emojis.
5. ✅ **Corregido. Rutas absolutas eliminadas:** se reemplazaron los fallbacks rígidos `C:\Users\frero\...` en todas las páginas de `src/App/pages/` (páginas 1, 2, 3 y 4) por resoluciones dinámicas relativas (`Path(__file__).resolve().parents[2]`).
6. ✅ **Resuelto por el equipo. Informe de auditoría duplicado:** se eliminó `reports/03_Auditoria_Calidad_Datos.md`.

---

## 5. Hoja de ruta para aumentar el valor (priorizada por impacto/esfuerzo)

| # | Acción | Impacto en valor | Esfuerzo |
|---|---|:---:|:---:|
| 1 | Corregir las inconsistencias de la sección 4 | Credibilidad | Bajo |
| 2 | **"Estimador de plazo":** el abogado ingresa tribunal + tipo de audiencia + mes y recibe un rango P25–P75. Puede partir con cuantiles empíricos, sin ML | **Alto:** convierte el BI en producto | Bajo |
| 3 | Modelo predictivo (regresión cuantílica / LightGBM) con *split* temporal y agrupado por causa, sin las variables con fuga. Reportar el MAE frente a la línea base "mediana del tribunal" | Alto: valida la promesa "predictiva" | Medio |
| 4 | Agregar la métrica **del ingreso a la primera audiencia** y **la duración total de la causa** | Alto: es la pregunta que hace el cliente | Bajo |
| 5 | Escalar a **cobertura nacional de Familia** (los JSON nacionales se pueden recuperar del commit `352dcd4` o volver a descargar con `Api_Caller`) | Alto: mercado unas 7× mayor | Medio |
| 6 | Pipeline de actualización mensual vía API + despliegue (Streamlit Cloud / contenedor) | Requisito para cobrar | Medio |
| 7 | **Validación con 5–10 abogados de familia:** ¿pagarían? ¿cuánto? ¿qué pregunta responden primero? | Crítico: hoy el valor es hipotético | Bajo |
| 8 | Extender a **Laboral** (mayor disposición a pagar en empresas) | Muy alto | Alto |

---

## 6. Conclusión

El proyecto tiene una **base técnica clara, por encima del promedio académico**, y ataca un problema real: la falta de predictibilidad de plazos en Familia. Hoy su valor para la industria es el de un **diagnóstico descriptivo de alta calidad**, útil sobre todo como evidencia y como prototipo. Para que tenga **valor comercial** le faltan tres cosas: (1) una respuesta directa al abogado con el estimador de plazo, (2) la validación con usuarios reales y (3) cobertura nacional con actualización continua. El camino de monetización más realista en el corto plazo es **licenciar el módulo predictivo a legaltech que ya tienen la base de clientes**, o bien ofrecerlo a instituciones públicas con alta carga de causas.

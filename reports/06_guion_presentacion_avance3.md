# Guion de presentación · Avance 3: Modelado y Resultados

**Duración sugerida:** 10–12 minutos · **Soporte:** página **6.- Modelado y Resultados** de la app (`streamlit run src/App/Inicio.py`, ruta `/modelado`).
**Respaldo técnico:** notebook `04_Modelado_audienciasparquet.ipynb`.

---

## 0. Apertura (30 s) · Indicadores superiores

**Mostrar:** los 4 indicadores de la parte superior.

**Decir:**
- "Nuestra pregunta es: cuando un abogado agenda una audiencia de Familia, ¿qué probabilidad hay de que espere poco, lo normal o mucho?"
- "Con datos que el modelo nunca vio (2024–2025), el log-loss baja de 1,084 sin información a 0,868, y la accuracy sube de 48 % a 62 %."
- "Además, la alerta de espera mayor a 60 días logra un ROC-AUC de 0,85."

---

## 1. Planteamiento (2 min)

**Mostrar:** las tres tarjetas y luego el gráfico "Audiencias con espera larga, por año".

**Decir sobre qué predecimos:**
- Tres tramos: Rápido (≤ 15 días), Estándar (16–30) y Demora (> 30). Entregamos **probabilidades**, no solo un tramo.
- Una alerta aparte: probabilidad de espera severa (> 60 días).

**Decir sobre las variables:**
- Solo usamos lo que el abogado sabe al agendar: tribunal, tipo de procedimiento y tipo de audiencia.
- Excluimos:
  - **Macro materia:** es una función exacta del procedimiento, así que repite la misma información.
  - **Días de tramitación previa y de despacho:** se calculan con la misma fecha de la audiencia. Usarlas sería hacer trampa (fuga de información).
  - **Fecha y duración de la audiencia:** no se conocen al momento de agendar.

**Decir sobre la validación (gráfico "Qué años usa cada etapa"):**
- Usamos un **origen móvil**: simulamos estar en una fecha y solo usamos los años anteriores.
- **Validación:** desde inicios de 2023 predecimos 2023. Aquí elegimos el modelo.
- **Prueba ciega:** desde inicios de 2024 predecimos 2024–2025. Solo se usa para reportar, nunca para elegir.
- Nunca partimos los datos al azar, porque las audiencias de una misma causa no son independientes.
- Comparamos 3 modelos × 2 ventanas de entrenamiento × con y sin calibración.
- Regla fijada antes de ver resultados: si dos candidatos difieren menos de 0,002 de log-loss, gana el más simple.
- Se puede mover el selector de ventana y el interruptor de calibración para mostrar cómo cambian los años usados.

**Decir sobre el gráfico de espera larga:**
- La proporción de audiencias con espera mayor a 30 días subió de 22 % (2015) a 64 % (2022) y bajó a cerca de 48 % en 2024–2025.
- Las esperas mayores a 60 días pasaron de 1,5 % a 29 % en 2022.
- El salto coincide con la emergencia sanitaria y el paso al régimen híbrido.
- **Consecuencia:** un modelo entrenado con años antiguos subestima la demora actual. Por eso comparamos una ventana completa (desde 2015) contra una reciente (últimos 2 años).

---

## 2. Resultados (3 min)

**Mostrar:** la tabla y el gráfico de barras de log-loss. Dejar la ventana "Reciente" y la calibración apagada.

**Decir sobre la tabla:**
- Las **reglas** (clase mayoritaria y moda por celda) no entregan probabilidades, por eso no tienen log-loss.
- El **bayesiano jerárquico** estima la probabilidad de cada tramo para cada combinación de tribunal × procedimiento × tipo de audiencia. Si una combinación tiene pocos casos, se apoya en el nivel superior (por ejemplo, solo el tipo de audiencia).
- La fila resaltada es el modelo elegido.
- Gradient Boosting se promedia sobre 3 semillas.

**Decir sobre el modelo elegido:**
- En validación, Gradient Boosting y el bayesiano quedaron a menos de 0,002 de log-loss. Por la regla de simplicidad elegimos el bayesiano.
- En la prueba ciega, la diferencia entre ambos es −0,0001 (IC 95 % −0,0005 a +0,0004): **no concluyente**.
- Con estas 3 variables, el modelo complejo aprende lo mismo que el bayesiano. El bayesiano además se puede explicar celda por celda.
- Los intervalos de confianza se obtienen con bootstrap por causa: se remuestrean causas completas.

**Mostrar:** cambiar la ventana a "Completa (desde 2015)".
- "Con todos los años, todos los modelos empeoran. Los datos recientes pesan más que el algoritmo."
- Activar la calibración: "Calibrar ayuda cuando se entrena con años antiguos, pero no si ya usamos datos recientes."

**Mostrar:** el gráfico "¿Las probabilidades dicen la verdad?".
- Cada punto agrupa el 10 % de las audiencias de prueba.
- Si la curva queda bajo la diagonal, el modelo exagera la probabilidad; sobre ella, la subestima.
- Para Demora, la curva queda algo bajo la diagonal: en 2024–2025 la demora bajó respecto de 2022–2023, por eso el modelo exagera un poco.

**Mostrar:** la matriz de confusión.
- Detecta casi toda la Demora (97 %) y acierta 43 % de los Rápido.
- El tramo Estándar es el más difícil (12 %): queda en medio de los otros dos.
- Por eso conviene mirar las **probabilidades** y no solo el tramo pronosticado.

**Mostrar:** el gráfico "¿Agregar variables mejora el modelo?".
- Probamos agregar modalidad, mes y día de programación, y la congestión del tribunal en los 90 días previos.
- Ninguna mejora; al contrario, empeoran la prueba (0,868 → 0,932 y 1,020). Por eso el simulador usa solo las 3 variables base.

**Mostrar:** cambiar el objetivo a "Alerta: espera severa (> 60 d)".
- Curva precisión–recall: PR-AUC 0,52 frente a 0,18 de una alerta al azar. La alerta concentra unas 2,9 veces más casos severos que el azar.

---

## 3. Simulador: mi causa (2 min)

**Mostrar (ejemplo preparado):** Contenciosa · Audiencia preparatoria · Viña del Mar. Luego cambiar a Los Andes.

**Decir:**
- El abogado ingresa los datos de la audiencia que va a agendar.
- El modelo responde con la probabilidad de cada tramo, estimada con los dos últimos años (2024–2025).
- A la derecha se ve lo que ocurrió en 2024–2025 en ese tribunal: mediana, rango típico (P25–P75) y cantidad de audiencias, comparado con el promedio regional.
- La recomendación se genera con reglas simples sobre las probabilidades:
  - Probabilidad de espera severa ≥ 25 %: marcar la causa como de riesgo.
  - Probabilidad de demora ≥ 60 %: informar al cliente un plazo de 1 a 2 meses.
  - Probabilidad de Rápido ≥ 50 %: preparar documentos y prueba desde ya.
- Si hay pocos casos recientes, se advierte que la estimación es menos firme.
- Las probabilidades describen el comportamiento reciente del tribunal; no son una garantía.

---

## 4. Comparar tribunales (2 min)

**Mostrar:** Contenciosa · Audiencia preparatoria, coloreado por mediana.

**Decir primero (uso responsable):**
- "Esto sirve solo para elegir entre tribunales **legalmente competentes**, por ejemplo en alimentos, donde la ley permite elegir entre el domicilio del demandante y el del demandado. Cambiar o inventar un domicilio no es legítimo."

**Decir sobre el mapa y el ranking:**
- El color más intenso indica más espera. El tamaño del círculo es la cantidad de audiencias de 2024–2025. La ubicación es aproximada, por comuna.
- Para la misma audiencia, la mediana va de 28 días (Los Andes) a 83 días (Quintero). Entre ciudades vecinas también hay brechas: Quilpué 29 días, Viña del Mar 53 y Valparaíso 67.
- La barra negra es el intervalo de confianza de 95 % (bootstrap de 400 remuestreos). El símbolo ≈ indica que no hay diferencia clara con el más rápido.
- Isla de Pascua queda fuera del mapa y de la selección por defecto, porque no es una alternativa real para causas del continente.
- Se pueden quitar tribunales del selector para dejar solo los que son competentes en un caso concreto.
- Ejemplo a destacar: hay tribunales muy volátiles. En preparatorias contenciosas, Villa Alemana pasó de 9 % de audiencias con demora en 2023 a 88 % en 2025. Por eso el modelo se reentrena con los años más recientes.

---

## 5. Conclusiones (1 min)

**Mostrar:** la pestaña de conclusiones.

**Cerrar con tres ideas:**
1. Las probabilidades sirven y la alerta de espera severa funciona.
2. Un modelo simple y explicable basta: el valor está en *qué tribunal y qué audiencia*.
3. La brecha entre tribunales es el hallazgo más útil para un estudio jurídico.

**Limitaciones a reconocer:**
- Solo hay audiencias realizadas; las suspendidas no aparecen.
- No vemos al juez, la defensa ni el contenido de la causa.
- Es una sola jurisdicción y una sola materia.
- Comparar tribunales muestra asociación, no causa: un tribunal puede recibir causas más complejas.

---

## Preguntas probables y respuestas cortas

| Pregunta | Respuesta |
|---|---|
| ¿Por qué no usaron el modelo más complejo? | Empató con el bayesiano en validación y en la prueba ciega. Ante un empate, elegimos el más simple y explicable; la regla se fijó antes de ver resultados. |
| ¿Por qué log-loss y no solo accuracy? | Entregamos probabilidades. El log-loss mide si esas probabilidades son correctas; la accuracy solo mira el tramo más probable. |
| ¿Por qué no validación cruzada aleatoria? | Las audiencias de una misma causa se parecen y el sistema cambia en el tiempo. Una partición aleatoria daría resultados optimistas. |
| ¿Por qué la calibración no se usa? | La probamos en igualdad de condiciones: reservar el último año para calibrar en vez de entrenar con él. Solo ayuda con la ventana completa. |
| ¿Por qué no predecir si la causa llega a juicio? | Lo evaluamos y lo descartamos: depende del juez, la defensa y el contenido de la causa, que no están en los datos. |
| ¿Qué pasa si los tribunales cambian? | El modelo se regenera con `python src/Modelado/entrenar.py` usando los dos últimos años. |

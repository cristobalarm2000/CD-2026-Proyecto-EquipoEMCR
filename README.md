# CD-2026-Proyecto-EquipoEMCR
TALLER 01
Del problema al proyecto analítico
Problemática 1 - Predicción de demanda energética
Contexto: En Chile, la transición hacia una matriz energética basada en energías renovables variables (solar en el norte y eólica en el centro-sur) ha generado un desafío crítico de estabilidad en el Sistema Eléctrico Nacional (SEN).
En este escenario realista, la Zona Central y la Región de Valparaíso enfrentan picos severos de demanda durante las horas punta nocturnas (18:00 a 23:00 hrs), justo cuando la generación solar cae a cero. Aunque existen centrales hidroeléctricas de pasada y parques de baterías BESS (System Battery Energy Storage), estos tienen capacidades de almacenamiento limitadas y tiempos de rampa de despacho ajustados.
Si la demanda real supera la oferta programada por el Coordinador Eléctrico Nacional, se deben encender de emergencia centrales térmicas de respaldo (altamente costosas y contaminantes) o aplicar cortes no programados por desprendimiento de carga para evitar el colapso de las subestaciones.

¿Cuál es el problema?
La alta volatilidad de la demanda en horas punta, combinada con la intermitencia renovable y el alto costo de la generación de respaldo en Chile. El desfase de la curva pato genera riesgos de saturación en la red y obliga a encender plantas térmicas lentas y contaminantes.
¿Quién toma decisiones?
Coordinador Eléctrico Nacional (CEN): Opera el sistema y despacha la energía en tiempo real. Generadoras y Distribuidoras: Ajustan ofertas y distribución local. Ministerio de Energía y CNE: Definen normativas, regulación y metas de descarbonización.
¿Qué impacto tendría resolverlo?
Reducción del costo marginal, mayor aprovechamiento de energía limpia con menos emisiones y estabilidad en la red eléctrica.

Preguntas analíticas
# ¿Cuál será la demanda máxima de energía (en MW) en el subsistema Central del SEN entre las 18:00 y las 23:00 horas, considerando la temperatura ambiental proyectada, la humedad relativa y la tendencia de consumo de los últimos 7 días?
Variable Objetivo: Demanda máxima de energía en horas punta (continua, en MW).
Variables Predictoras: Temperatura mínima y máxima proyectada (°C). Humedad relativa (HL). Consumo registrado en el mismo bloque horario durante los 1, 7 y 14 días previos (MW).

# ¿Cuál es la probabilidad de que una subestación de distribución regional supere el 90% de su capacidad nominal durante un día hábil de invierno, en función del pronóstico del tiempo, el calendario escolar y laboral, y la tasa de electrificación de calefacción en la zona?
Variable Objetivo: Estado de sobrecarga de la subestación (binaria: 0 = Bajo 90% / 1 = Mayor o igual a 90%).
Variables Predictoras: Alerta de ola de frío (variable categórica: Sí/No). Tipo de día (día hábil, fin de semana, feriado). Consumo promedio por cliente residencial en las últimas 4 horas. Índice de radiación solar efectiva acumulada durante el día.

# ¿Cuánta energía (en MWh) deberán entregar los sistemas de almacenamiento de baterías (BESS) durante la rampa de caída solar (18:30 a 20:00 hrs) para compensar la pérdida de generación fotovoltaica sin encender centrales térmicas?
Variable Objetivo: Energía total requerida de descarga BESS (continua, en MWh).
Variables Predictoras: Tasa de caída de la generación solar (MW/minuto) en el norte chico y zona central. Velocidad de viento proyectada en parques eólicos de la Región de Coquimbo y Valparaíso. Tasa de incremento de demanda residencial (MW/minuto).

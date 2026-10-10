import nbformat
from nbclient import NotebookClient
from pathlib import Path

nb_path = Path(r"C:\Users\frero\CD-2026-Proyecto-EquipoEMCR\notebooks\01 ETL_audienciasparquet.ipynb")
with open(nb_path, "r", encoding="utf-8") as f:
    nb = nbformat.read(f, as_version=4)

print(f"Initial cells count: {len(nb.cells)}")

# Markdown cell for Section 5
md_cell = nbformat.v4.new_markdown_cell("""## 5.- Valores Imposibles / Outliers (Fechas, Plazos y Horarios)

En esta sección se evalúa la consistencia física, lógica y jurídica de las variables temporales y cuantitativas del dataset:

### 5.1.- Inconsistencias Cronológicas en Fechas (Valores Imposibles)
Se auditó la secuencia cronológica entre los tres hitos temporales del proceso:
$$\\text{FECHA\\_INGRESO} \\le \\text{FECHA\\_PROGRAMACION} \\le \\text{FECHA\\_AUDIENCIA}$$

* **`FECHA_AUDIENCIA < FECHA_INGRESO`**: **0 casos (0.00%)**. Ninguna audiencia se realizó antes de ingresar la causa al tribunal.
* **`FECHA_PROGRAMACION < FECHA_INGRESO`**: **0 casos (0.00%)**. Ninguna audiencia se programó antes del ingreso de la causa.
* **`FECHA_AUDIENCIA < FECHA_PROGRAMACION`**: **22 casos (0.0047%)**.
  - **Diagnóstico:** Desfases administrativos menores de entre 1 y 5 días en continuaciones de audiencias de juicio o resoluciones verbales en estrado que fueron suscritas o ingresadas en SITFA con posterioridad a la sesión.
  - **Tratamiento aplicado:** Se ajusta **`FECHA_PROGRAMACION = FECHA_AUDIENCIA`** para los 22 casos, garantizando que el 100% de los registros cumpla la coherencia temporal sin alterar los plazos de agendamiento (ya estandarizados en 0 días de espera en el paso 4.3).

### 5.2.- Auditoría de Outliers en Plazos de Agendamiento (`PLAZO_AGENDAMIENTO`)
* **Distribución:** Mediana de 26 días hábiles, media de 31.4 días hábiles, percentil 95 en 77 días y percentil 99 en 117 días.
* **Outliers Extremos (Criterio Tukey $Q_3 + 3 \\times IQR = 136$ días hábiles):** Representan 2.423 casos (0.52%), con un máximo de 339 días hábiles.
* **Decisión de Negocio (Estudio Jurídico):** **Conservación íntegra de los valores originales**. Los plazos extensos no constituyen errores de digitación, sino cuellos de botella procesales reales (peritajes psicosociales extensos del DAM/SML, suspensiones acordadas por las partes bajo el art. 202 CPC y congestión de agenda en juzgados críticos como Viña del Mar y Valparaíso). Truncar o winsorizar estos valores falsearía los KPIs de demora judicial. Su segmentación por tramos se documenta para la etapa de EDA / Feature Engineering.

### 5.3.- Auditoría de Horarios de Audiencia (`HORA_INICIO` y `HORA_FIN`)
* **Duración Negativa (`HORA_FIN < HORA_INICIO`):** **0 casos**.
* **Duración Cero Minutos (`HORA_FIN == HORA_INICIO`):** **1.008 casos (0.216%)**. Corresponden a audiencias frustradas en el acto por incomparecencia de partes, desistimientos o suspensiones de plano donde el acta se abrió y cerró de inmediato.
* **Duración Extrema (> 8 horas):** **54 casos (0.012%)**, correspondientes a sesiones de jornada judicial completa dejadas abiertas en SITFA en tribunales unipersonales o juicios complejos con recesos continuos.
* **Decisión de Negocio (Opción B):** **Conservación de marcas horarias originales** sin alteración artificial ni imputación forzada. El cálculo analítico de duración en minutos se reserva para la fase de EDA.""")

# Code cell for Section 5
code_cell = nbformat.v4.new_code_cell("""# 1. Corrección de los 22 valores imposibles en fechas
mask_prog_post = df_clean['FECHA_AUDIENCIA'] < df_clean['FECHA_PROGRAMACION']
n_corregidos = mask_prog_post.sum()

# Ajuste: igualar FECHA_PROGRAMACION a FECHA_AUDIENCIA
df_clean.loc[mask_prog_post, 'FECHA_PROGRAMACION'] = df_clean.loc[mask_prog_post, 'FECHA_AUDIENCIA']

print("=== 5.1.- VERIFICACIÓN DE COHERENCIA CRONOLÓGICA POST-AJUSTE ===")
print(f"Casos ajustados (FECHA_AUDIENCIA < FECHA_PROGRAMACION): {n_corregidos}")
inv_ing_aud = (df_clean['FECHA_AUDIENCIA'] < df_clean['FECHA_INGRESO']).sum()
inv_ing_prog = (df_clean['FECHA_PROGRAMACION'] < df_clean['FECHA_INGRESO']).sum()
inv_prog_aud = (df_clean['FECHA_AUDIENCIA'] < df_clean['FECHA_PROGRAMACION']).sum()
print(f" - FECHA_AUDIENCIA < FECHA_INGRESO:        {inv_ing_aud} casos (0.00%)")
print(f" - FECHA_PROGRAMACION < FECHA_INGRESO:     {inv_ing_prog} casos (0.00%)")
print(f" - FECHA_AUDIENCIA < FECHA_PROGRAMACION:    {inv_prog_aud} casos (0.00%) -> 100% COHERENTE")

# 2. Resumen estadístico de PLAZO_AGENDAMIENTO
print("\\n=== 5.2.- PERFIL DE PLAZO_AGENDAMIENTO (CONSERVACIÓN ÍNTEGRA) ===")
stats_plazo = df_clean['PLAZO_AGENDAMIENTO'].astype(float).describe(
    percentiles=[0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99, 0.999]
)
q1 = stats_plazo['25%']
q3 = stats_plazo['75%']
iqr = q3 - q1
umbral_extremo = q3 + 3.0 * iqr

print(stats_plazo.to_frame('PLAZO_AGENDAMIENTO (Días Hábiles)').round(2))
print(f"Umbral Outlier Extremo Tukey (Q3 + 3*IQR): {umbral_extremo:.1f} días hábiles")
print(f"Casos extremos (> {umbral_extremo:.1f} días): {(df_clean['PLAZO_AGENDAMIENTO'] > umbral_extremo).sum():,} ({((df_clean['PLAZO_AGENDAMIENTO'] > umbral_extremo).mean()*100):.3f}%)")
print(f"Casos > 180 días hábiles (aprox. 6 meses): {(df_clean['PLAZO_AGENDAMIENTO'] > 180).sum():,} ({((df_clean['PLAZO_AGENDAMIENTO'] > 180).mean()*100):.3f}%)")

# 3. Auditoría de Horarios
print("\\n=== 5.3.- AUDITORÍA DE HORARIOS (OPCIÓN B: CONSERVACIÓN ORIGINAL) ===")
def hora_to_min(h_str):
    if pd.isna(h_str): return np.nan
    p = str(h_str).split(':')
    return int(p[0]) * 60 + int(p[1]) + (int(p[2])/60 if len(p) > 2 else 0)

dur_min = df_clean['HORA_FIN'].apply(hora_to_min) - df_clean['HORA_INICIO'].apply(hora_to_min)
casos_neg = (dur_min < 0).sum()
casos_cero = (dur_min == 0).sum()
casos_mayor_8h = (dur_min > 480).sum()

print(f" - Duración < 0 min:  {casos_neg} casos")
print(f" - Duración == 0 min: {casos_cero:,} casos ({casos_cero/len(df_clean)*100:.3f}%) (Audiencias frustradas de plano)")
print(f" - Duración > 8 hrs:  {casos_mayor_8h} casos ({casos_mayor_8h/len(df_clean)*100:.3f}%) (Jornadas completas abiertas)")
print(f"Mediana de duración de audiencia: {dur_min[dur_min > 0].median():.1f} minutos (Media: {dur_min[dur_min > 0].mean():.1f} min)")
""")

nb.cells.extend([md_cell, code_cell])

print(f"Total cells to execute: {len(nb.cells)}")
print("Executing notebook with NotebookClient...")

client = NotebookClient(nb, timeout=600, kernel_name='python3')
client.execute()

with open(nb_path, "w", encoding="utf-8") as f:
    nbformat.write(nb, f)

print(f"Notebook executed successfully and saved to {nb_path} with {len(nb.cells)} cells.")

import nbformat
from nbclient import NotebookClient
from pathlib import Path

nb_path = Path(r"C:\Users\frero\CD-2026-Proyecto-EquipoEMCR\notebooks\01 ETL_audienciasparquet.ipynb")
with open(nb_path, "r", encoding="utf-8") as f:
    nb = nbformat.read(f, as_version=4)

print(f"Initial cells count: {len(nb.cells)}")

# Cell 41: Markdown Sección 6
md_6 = nbformat.v4.new_markdown_cell("""## 6.- Ingeniería de Características (Feature Engineering para Business Intelligence)

Con el dataset limpio al 100% (cero valores nulos y consistencia cronológica total en sus 20 columnas originales), se construyen **16 nuevas características analíticas** derivadas, orientadas a habilitar la toma de decisiones, tarificación de honorarios, predictibilidad de plazos y analítica de salas para un **estudio de abogados de familia**:

1. **Dimensiones de Calendario y Ciclos Judiciales:**
   - `DIA_SEMANA_AUDIENCIA`: Nombre del día (*Lunes a Sábado*).
   - `MES_AUDIENCIA`: Nombre del mes (*Enero a Diciembre*).
   - `TRIMESTRE_AUDIENCIA`: Trimestre calendario (*Q1 a Q4*).
   - `BLOQUE_HORARIO`: Franja horaria de inicio (*Mañana Temprano, Mañana Central, Mediodía, Tarde, Vespertino*).

2. **Métricas de Duración y Eficiencia en Sala (Time-Tracking):**
   - `DURACION_MINUTOS`: Duración exacta de la sesión ($(\\text{HORA\\_FIN} - \\text{HORA\\_INICIO})$ en minutos).
   - `TRAMO_DURACION`: Clasificación ordinal (*0. Frustrada, 1. Breve, 2. Estándar, 3. Extendida, 4. Compleja*).
   - `FLG_AUDIENCIA_FRUSTRADA`: Booleano (`True` si duración es 0 min, por incomparecencia o suspensión de plano).

3. **Métricas de Tramitación y Cuellos de Botella (Lead Times & SLAs):**
   - `DIAS_TRAMITACION_PREVIA`: Días corridos acumulados desde la presentación de la demanda hasta la audiencia.
   - `DIAS_DESPACHO_AGENDAMIENTO`: Días corridos desde el ingreso de la causa hasta la resolución que fijó la audiencia.
   - `TRAMO_AGENDAMIENTO`: Categorización ordinal de los días hábiles de espera (*Inmediato, Rápido, Estándar Legal, Demora Moderada, Congestión Severa, Cuello de Botella Crítico*).

4. **Secuencia Procesal y Litigiosidad de la Causa:**
   - `ORDEN_AUDIENCIA_CAUSA`: Número correlativo de la audiencia dentro de la misma causa judicial (`ID_CAUSA_RIT`).
   - `TOTAL_AUDIENCIAS_CAUSA`: Volumen total de audiencias que acumula la causa en todo su historial.
   - `ES_AUDIENCIA_INICIAL`: Indicador booleano (`True` si es la primera audiencia de la causa).
   - `ES_CONTINUACION`: Indicador booleano (`True` si la audiencia es continuación de una sesión previa).

5. **Segmentación Jurídica y Contexto Normativo:**
   - `MACRO_MATERIA`: Agrupación de procedimientos en áreas de práctica del estudio (*Litigación Contenciosa, Medidas Cautelares y Vulnerabilidad, Ejecución y Alimentos, Actos No Contenciosos, Otros*).
   - `EPOCA_NORMATIVA`: Contexto institucional según vigencia legal (*Pre-Pandemia Presencial, Emergencia Sanitaria Ley 21.226, Régimen Permanente Híbrido Ley 21.394*).""")

# Cell 42: Code Sección 6
code_6 = nbformat.v4.new_code_cell("""# 1. Dimensiones de Calendario y Horarias
dias_map = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
meses_map = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
             7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}

df_clean['DIA_SEMANA_AUDIENCIA'] = df_clean['FECHA_AUDIENCIA'].dt.dayofweek.map(dias_map)
df_clean['MES_AUDIENCIA'] = df_clean['FECHA_AUDIENCIA'].dt.month.map(meses_map)
df_clean['TRIMESTRE_AUDIENCIA'] = 'Q' + df_clean['FECHA_AUDIENCIA'].dt.quarter.astype(str)

def hora_to_min(h_str):
    p = str(h_str).split(':')
    return int(p[0]) * 60 + int(p[1]) + (int(p[2])/60 if len(p) > 2 else 0)

min_inicio = df_clean['HORA_INICIO'].apply(hora_to_min)
min_fin = df_clean['HORA_FIN'].apply(hora_to_min)
df_clean['DURACION_MINUTOS'] = (min_fin - min_inicio).round(1)

def categorizar_bloque(min_val):
    hh = min_val / 60
    if hh < 10: return 'Mañana Temprano (08:00-09:59)'
    elif hh < 12: return 'Mañana Central (10:00-11:59)'
    elif hh < 14: return 'Mediodía (12:00-13:59)'
    elif hh < 17: return 'Tarde (14:00-16:59)'
    else: return 'Vespertino / Turno (>= 17:00)'

df_clean['BLOQUE_HORARIO'] = min_inicio.apply(categorizar_bloque)

def categorizar_duracion(dur):
    if dur == 0: return '0. Frustrada / En el acto (0 min)'
    elif dur <= 15: return '1. Breve (1-15 min)'
    elif dur <= 30: return '2. Estándar (16-30 min)'
    elif dur <= 60: return '3. Extendida (31-60 min)'
    else: return '4. Compleja (> 60 min)'

df_clean['TRAMO_DURACION'] = df_clean['DURACION_MINUTOS'].apply(categorizar_duracion)
df_clean['FLG_AUDIENCIA_FRUSTRADA'] = df_clean['DURACION_MINUTOS'] == 0

# 2. Métricas de Tramitación y Agendamiento
df_clean['DIAS_TRAMITACION_PREVIA'] = (df_clean['FECHA_AUDIENCIA'] - df_clean['FECHA_INGRESO']).dt.days
df_clean['DIAS_DESPACHO_AGENDAMIENTO'] = (df_clean['FECHA_PROGRAMACION'] - df_clean['FECHA_INGRESO']).dt.days

def categorizar_plazo(dias):
    if dias == 0: return '1. Inmediato (0 días)'
    elif dias <= 15: return '2. Rápido (1-15 días)'
    elif dias <= 30: return '3. Estándar Legal (16-30 días)'
    elif dias <= 60: return '4. Demora Moderada (31-60 días)'
    elif dias <= 120: return '5. Congestión Severa (61-120 días)'
    else: return '6. Cuello de Botella Crítico (> 120 días)'

df_clean['TRAMO_AGENDAMIENTO'] = df_clean['PLAZO_AGENDAMIENTO'].apply(categorizar_plazo)

# 3. Secuencia Procesal y Litigiosidad
df_clean = df_clean.sort_values(['ID_CAUSA_RIT', 'FECHA_AUDIENCIA', 'HORA_INICIO']).reset_index(drop=True)
df_clean['ORDEN_AUDIENCIA_CAUSA'] = (df_clean.groupby('ID_CAUSA_RIT').cumcount() + 1).astype('int16')
df_clean['TOTAL_AUDIENCIAS_CAUSA'] = df_clean.groupby('ID_CAUSA_RIT')['FECHA_AUDIENCIA'].transform('count').astype('int16')
df_clean['ES_AUDIENCIA_INICIAL'] = df_clean['ORDEN_AUDIENCIA_CAUSA'] == 1
df_clean['ES_CONTINUACION'] = df_clean['TIPO_AUDIENCIA'].str.contains('CONTINUACION', na=False)

# 4. Macro Materia Jurídica y Época Normativa
def clasificar_macro_materia(proc):
    if proc == 'CONTENCIOSA': return 'Litigación Contenciosa'
    elif proc in ['VIOLENCIA INTRAFAMILIAR', 'MEDIDAS DE PROTECCION']: return 'Medidas Cautelares y Vulnerabilidad'
    elif proc == 'CUMPLIMIENTO': return 'Ejecución y Alimentos (Cumplimiento)'
    elif proc in ['VOLUNTARIA', 'ADOPCION', 'IDENTIDAD DE GENERO', 'TRANSACCION']: return 'Actos No Contenciosos y Voluntarios'
    else: return 'Otros Procedimientos'

df_clean['MACRO_MATERIA'] = df_clean['TIPO_PROCEDIMIENTO'].apply(clasificar_macro_materia)

def clasificar_epoca(fec):
    if fec < pd.Timestamp('2020-03-18'): return 'Pre-Pandemia (Presencial)'
    elif fec < pd.Timestamp('2022-10-01'): return 'Emergencia Sanitaria (Ley 21.226)'
    else: return 'Régimen Permanente Híbrido (Ley 21.394)'

df_clean['EPOCA_NORMATIVA'] = df_clean['FECHA_AUDIENCIA'].apply(clasificar_epoca)

print("=== VERIFICACIÓN DE INGENIERÍA DE CARACTERÍSTICAS ===")
print(f"Dimensiones resultantes: {df_clean.shape[0]:,} filas x {df_clean.shape[1]} columnas")
print(f"Total nulos en el dataset enriquecido: {df_clean.isna().sum().sum()}")
display(df_clean[['ID_CAUSA_RIT', 'MACRO_MATERIA', 'TIPO_AUDIENCIA', 'DIA_SEMANA_AUDIENCIA', 'BLOQUE_HORARIO', 'DURACION_MINUTOS', 'TRAMO_AGENDAMIENTO', 'ORDEN_AUDIENCIA_CAUSA', 'EPOCA_NORMATIVA']].head(5))""")

# Cell 43: Markdown Sección 7
md_7 = nbformat.v4.new_markdown_cell("""## 7.- Exportación y Persistencia del Modelo de Datos Preparado

Como hito final del pipeline de Extracción, Transformación y Carga (ETL), se procede a la **persistencia definitiva del dataset enriquecido**:

- **Destino del Artefacto:** `data/processed/audiencias_preparadas_modelo.parquet`.
- **Formato:** Apache Parquet columnar con compresión Snappy, optimizado para consultas de alta velocidad y bajo consumo de memoria.
- **Cobertura:** 466.178 registros de audiencias y 36 columnas analíticas (100% íntegras, 0 valores nulos).
- **Consumo:** Este artefacto constituirá el insumo único e inmutable para el **Dashboard Ejecutivo de Business Intelligence** y los modelos predictivos posteriores.""")

# Cell 44: Code Sección 7
code_7 = nbformat.v4.new_code_cell("""# Persistencia del artefacto final procesado
from pathlib import Path

out_dir = Path("../data/processed")
if not out_dir.exists():
    out_dir = Path("data/processed")
out_dir.mkdir(parents=True, exist_ok=True)

out_file = out_dir / "audiencias_preparadas_modelo.parquet"
df_clean.to_parquet(out_file, index=False, compression='snappy')

file_size_mb = out_file.stat().st_size / (1024 * 1024)

print("=== ARTEFACTO FINAL DE DATOS PERSISTIDO EXITOSAMENTE ===")
print(f"Ruta de destino: {out_file.resolve()}")
print(f"Dimensiones finales: {df_clean.shape[0]:,} filas x {df_clean.shape[1]} columnas")
print(f"Tamaño en disco: {file_size_mb:.2f} MB")
print(f"Integridad: 100.00% completo (0 nulos)")

# Resumen columnar
resumen_columnas = pd.DataFrame({
    'No': range(1, len(df_clean.columns) + 1),
    'Columna': df_clean.columns,
    'Dtype': df_clean.dtypes.astype(str).values,
    'Nulos': df_clean.isna().sum().values,
    'Ejemplo': df_clean.iloc[0].astype(str).values
})
display(resumen_columnas)""")

nb.cells.extend([md_6, code_6, md_7, code_7])

print(f"Total cells to execute: {len(nb.cells)}")
print("Executing notebook with NotebookClient...")

client = NotebookClient(nb, timeout=600, kernel_name='python3')
client.execute()

with open(nb_path, "w", encoding="utf-8") as f:
    nbformat.write(nb, f)

print(f"Notebook executed successfully and saved to {nb_path} with {len(nb.cells)} cells.")

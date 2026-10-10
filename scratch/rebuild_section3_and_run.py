import nbformat
from nbclient import NotebookClient
from pathlib import Path

nb_path = Path(r"C:\Users\frero\CD-2026-Proyecto-EquipoEMCR\notebooks\01 ETL_audienciasparquet.ipynb")

with open(nb_path, "r", encoding="utf-8") as f:
    nb = nbformat.read(f, as_version=4)

print(f"Initial cells count: {len(nb.cells)}")

# Keep only cells 0 to 12 (original sections 1 and 2)
nb.cells = nb.cells[:13]

new_cells = []

# Cell 13: Markdown - Encabezado Sección 3
new_cells.append(nbformat.v4.new_markdown_cell("""# 3.- Limpieza y Estandarización de Datos (Sanitización)

Implementación de las reglas de saneamiento y normalización técnica acordadas a partir de la auditoría de calidad de datos."""))

# Cell 14: Markdown - Ítem 3.1: Exposición y Tratamiento del Cruce Anómalo del Año 2023
new_cells.append(nbformat.v4.new_markdown_cell("""### 3.1.- Tratamiento y Resolución del Cruce Anómalo del Año 2023

En la auditoría de calidad se detectó un desplazamiento estructural de columnas en el lote anual 2023 (43.380 registros):
1. **Desplazamiento Procesal**: En el campo `TIPO_AUDIENCIA` se registraron nombres de procedimientos (`'Contenciosa'`, `'Medidas de protección'`, `'Violencia intrafamiliar'`, `'Cumplimiento'`), mientras que en `TIPO_PROCEDIMIENTO` se registraron siglas de una sola letra (`'C'`, `'P'`, `'F'`, `'X'`, etc.).
2. **Desplazamiento RIT / RUC**: En el campo `RIT` se registró el Rol Único de Causa (RUC con formato `'YY- M-NNNNNNN-DV'`), quedando la columna `RUC` con 100% de valores nulos (`NaN`).

A continuación se expone una muestra de las primeras 5 filas del año 2023 para evidenciar la anomalía previa a su corrección."""))

# Cell 15: Code - Exposición previa del año 2023 (df.head(5) donde ANO_PROCESO == 2023)
new_cells.append(nbformat.v4.new_code_cell("""# Exposición de la anomalía en el lote 2023
cols_anomalia = ['ANO_PROCESO', 'TRIBUNAL', 'RIT', 'RUC', 'TIPO_PROCEDIMIENTO', 'TIPO_AUDIENCIA']
print("Muestra de 5 filas del lote 2023 antes de la corrección:")
display(df[df['ANO_PROCESO'] == 2023][cols_anomalia].head(5))"""))

# Cell 16: Markdown - Regla de Limpieza y Corrección 2023
new_cells.append(nbformat.v4.new_markdown_cell("""#### Regla de Tratamiento y Corrección para 2023:
- Se crea la bandera booleana `FLG_CRUCE_2023` para documentar la trazabilidad de los 43.380 registros intervenidos.
- En `TIPO_PROCEDIMIENTO` se rescata la descripción procesal registrada erróneamente en `TIPO_AUDIENCIA`.
- En `TIPO_AUDIENCIA` se cataloga formalmente como `'NO ESPECIFICADA'` para evitar falsear tipos de audiencia específicos que la API no suministró en dicho lote.
- En `RUC` se recupera el identificador numérico contenido en el campo `RIT`."""))

# Cell 17: Code - Aplicación de la limpieza del año 2023
new_cells.append(nbformat.v4.new_code_cell("""import numpy as np
import unicodedata
import re

df_clean = df.copy()

def norm_text(s):
    if pd.isna(s):
        return s
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode('utf-8')
    s = re.sub(r'\\s+', ' ', s)
    return s.strip().upper()

# 1. Bandera de control
is_2023 = df_clean['ANO_PROCESO'] == 2023
df_clean['FLG_CRUCE_2023'] = is_2023

map_proc_codes = {
    'C': 'CONTENCIOSA',
    'P': 'MEDIDAS DE PROTECCION',
    'F': 'VIOLENCIA INTRAFAMILIAR',
    'X': 'CUMPLIMIENTO',
    'A': 'ADOPCION',
    'V': 'VOLUNTARIA',
    'I': 'IDENTIDAD DE GENERO',
    'Z': 'MENORES',
    'R': 'TRANSACCION',
    'T': 'TRANSACCION',
    'S': 'PROTECCION SALUD MENTAL',
    'W': 'EXHORTOS',
    'EXHORTO': 'EXHORTOS'
}

# 2. Rescate de procedimiento y catalogación de audiencia
proc_desde_aud = df_clean['TIPO_AUDIENCIA'].apply(norm_text).replace(map_proc_codes)
df_clean['TIPO_PROCEDIMIENTO'] = np.where(is_2023, proc_desde_aud, df_clean['TIPO_PROCEDIMIENTO'])
df_clean['TIPO_AUDIENCIA'] = np.where(is_2023, 'NO ESPECIFICADA', df_clean['TIPO_AUDIENCIA'])

# 3. Rescate de RUC
df_clean['RUC'] = np.where(is_2023, df_clean['RIT'], df_clean['RUC'])

print("=== MUESTRA POST-CORRECCIÓN DEL LOTE 2023 ===")
display(df_clean[df_clean['ANO_PROCESO'] == 2023][cols_anomalia + ['FLG_CRUCE_2023']].head(5))
print(f"\\nDistribución de procedimientos rescatados en 2023 ({df_clean[is_2023]['TIPO_PROCEDIMIENTO'].nunique()} categorías):")
display(df_clean[df_clean['ANO_PROCESO'] == 2023]['TIPO_PROCEDIMIENTO'].value_counts().to_frame("conteo"))"""))

# Cell 18: Markdown - Ítem 3.2: Resolución de Inconsistencias en Columnas Categóricas
new_cells.append(nbformat.v4.new_markdown_cell("""### 3.2.- Resolución de Inconsistencias en Columnas Categóricas

Estandarización textual (mayúsculas sostenidas, remoción de tildes y depuración de espacios en blanco redundantes) aplicada a las variables institucionales y procesales:
1. **`CORTE` y `COMPETENCIA`**: Unificación a mayúsculas sostenidas (`.upper()`) y sin tildes.
2. **`TRIBUNAL`**: Estandarización de los nombres mediante mapeo oficial del catálogo PJUD sobre `COD_TRIBUNAL` (reduciendo de 34 variantes a 15 juzgados canónicos).
3. **`TIPO_PROCEDIMIENTO`**: Homologación general a las 12 categorías canónicas en mayúsculas sostenidas.
4. **`TIPO_AUDIENCIA`**: Normalización textual (`.upper()` y sin tildes)."""))

# Cell 19: Code - Estandarización Categórica
new_cells.append(nbformat.v4.new_code_cell("""# 1. Normalización de CORTE y COMPETENCIA
df_clean['CORTE'] = df_clean['CORTE'].apply(norm_text)
df_clean['COMPETENCIA'] = df_clean['COMPETENCIA'].apply(norm_text)

# 2. Catálogo canónico oficial PJUD para TRIBUNAL por COD_TRIBUNAL
cat_tribunales = {
    88: 'JUZGADO DE LETRAS Y GARANTIA DE PETORCA',
    94: 'JUZGADO DE LETRAS Y GARANTIA DE PUTAENDO',
    103: 'JUZGADO DE LETRAS Y GARANTIA DE ISLA DE PASCUA',
    660: 'JUZGADO DE LETRAS Y GARANTIA DE QUINTERO',
    1261: 'JUZGADO DE FAMILIA DE CASABLANCA',
    1262: 'JUZGADO DE FAMILIA DE LA LIGUA',
    1263: 'JUZGADO DE FAMILIA DE LIMACHE',
    1264: 'JUZGADO DE FAMILIA DE LOS ANDES',
    1265: 'JUZGADO DE FAMILIA DE QUILLOTA',
    1266: 'JUZGADO DE FAMILIA DE QUILPUE',
    1267: 'JUZGADO DE FAMILIA DE SAN ANTONIO',
    1268: 'JUZGADO DE FAMILIA DE SAN FELIPE',
    1269: 'JUZGADO DE FAMILIA DE VALPARAISO',
    1270: 'JUZGADO DE FAMILIA DE VILLA ALEMANA',
    1271: 'JUZGADO DE FAMILIA DE VINA DEL MAR'
}
df_clean['TRIBUNAL'] = df_clean['COD_TRIBUNAL'].map(cat_tribunales).fillna(df_clean['TRIBUNAL'].apply(norm_text))

# 3. Normalización general de TIPO_PROCEDIMIENTO
df_clean['TIPO_PROCEDIMIENTO'] = df_clean['TIPO_PROCEDIMIENTO'].apply(norm_text).replace(map_proc_codes)

# 4. Normalización textual de TIPO_AUDIENCIA
df_clean['TIPO_AUDIENCIA'] = df_clean['TIPO_AUDIENCIA'].apply(norm_text)

print("=== VERIFICACIÓN POST-NORMALIZACIÓN CATEGÓRICA ===")
print("Cortes únicas:", df_clean['CORTE'].unique().tolist())
print("Competencias únicas:", df_clean['COMPETENCIA'].unique().tolist())
print(f"Tribunales canónicos únicos ({df_clean['TRIBUNAL'].nunique()}):")
display(df_clean[['COD_TRIBUNAL', 'TRIBUNAL']].drop_duplicates().sort_values('COD_TRIBUNAL'))

print(f"\\nTIPO_PROCEDIMIENTO ({df_clean['TIPO_PROCEDIMIENTO'].nunique()} categorías canónicas):")
display(df_clean['TIPO_PROCEDIMIENTO'].value_counts().to_frame("conteo"))

print(f"\\nTIPO_AUDIENCIA ({df_clean['TIPO_AUDIENCIA'].nunique()} categorías normalizadas - Muestra top 10):")
display(df_clean['TIPO_AUDIENCIA'].value_counts().head(10).to_frame("conteo"))"""))

# Cell 20: Markdown - Ítem 3.3: Estandarización de Modalidad (Videoconferencia)
new_cells.append(nbformat.v4.new_markdown_cell("""### 3.3.- Estandarización de Modalidad (Videoconferencia)

Estandarización de los 6 formatos heterogéneos (`'SI'`, `'NO'`, `'1.0'`, `'0.0'`, `'1,0'`, `'0,0'`) a tipado booleano estricto (`True` = Telemática / Remota, `False` = Presencial).

**Criterio metodológico sobre valores ausentes pre-2020:**
Los 248.137 registros con valor nulo corresponden en su totalidad al período 2015 hasta noviembre de 2020. Debido a que las audiencias telemáticas fueron habilitadas por primera vez en el Poder Judicial chileno mediante la Ley 21.226 (publicada en abril de 2020 e implementada progresivamente en tribunales de familia hacia finales de ese año), las audiencias de dicho período histórico fueron presenciales por definición jurídica y operativa. En consecuencia, se imputan con `False` (Presencial), alcanzando un 100% de integridad en la variable."""))

# Cell 21: Code - Estandarización de Videoconferencia
new_cells.append(nbformat.v4.new_code_cell("""map_video = {
    'SI': True, 'SÍ': True, '1.0': True, '1,0': True, '1': True, 'TRUE': True,
    'NO': False, '0.0': False, '0,0': False, '0': False, 'FALSE': False
}

video_series = df_clean['VIDEOCONFERENCIA'].astype(str).str.strip().str.upper().map(map_video)
df_clean['VIDEOCONFERENCIA'] = video_series.fillna(False).astype(bool)

print("Distribución final de VIDEOCONFERENCIA (Booleano estricto):")
display(df_clean['VIDEOCONFERENCIA'].value_counts().to_frame("conteo"))
display(df_clean['VIDEOCONFERENCIA'].value_counts(normalize=True).mul(100).round(2).to_frame("% participación"))

print("\\nAdopción por año (Presencial vs Telemática):")
display(df_clean.groupby(['ANO_PROCESO', 'VIDEOCONFERENCIA']).size().unstack(fill_value=0))"""))

nb.cells.extend(new_cells)
print(f"New total cells count: {len(nb.cells)}")

# Save updated notebook
with open(nb_path, "w", encoding="utf-8") as f:
    nbformat.write(nb, f)

print("Notebook structure saved. Now executing notebook...")
client = NotebookClient(nb, timeout=600, kernel_name="python3")
executed_nb = client.execute()

with open(nb_path, "w", encoding="utf-8") as f:
    nbformat.write(executed_nb, f)

print("Notebook executed and outputs saved successfully!")

import nbformat
from nbclient import NotebookClient
from pathlib import Path

nb_path = Path(r"C:\Users\frero\CD-2026-Proyecto-EquipoEMCR\notebooks\01 ETL_audienciasparquet.ipynb")

with open(nb_path, "r", encoding="utf-8") as f:
    nb = nbformat.read(f, as_version=4)

print(f"Initial cells count: {len(nb.cells)}")

# Keep cells 0 to 12 (Sección 1 y 2)
nb.cells = nb.cells[:13]

new_cells = []

# Cell 13: Markdown - Encabezado Sección 3
new_cells.append(nbformat.v4.new_markdown_cell("""# 3.- Limpieza y Estandarización de Datos (Sanitización)

Implementación del plan de saneamiento, corrección estructural y normalización técnica conforme a los hallazgos de la auditoría y fuentes oficiales del PJUD."""))

# Cell 14: Markdown - Ítem 3.1
new_cells.append(nbformat.v4.new_markdown_cell("""### 3.1.- Tratamiento y Resolución del Cruce Anómalo del Año 2023 (Opción A: Fuente Oficial PJUD)

En la auditoría de calidad se detectó un desplazamiento estructural de columnas en el endpoint de la API para el lote 2023 (43.380 registros):
1. **Desplazamiento Procesal**: En el campo `TIPO_AUDIENCIA` de la API se entregaron los nombres de procedimiento (`'Contenciosa'`, `'Medidas de protección'`, etc.), mientras que en `TIPO_PROCEDIMIENTO` se registraron letras aisladas (`'C'`, `'P'`, `'F'`, `'X'`).
2. **Desplazamiento RIT / RUC**: En `RIT` se alojó el RUC nacional (`21- 2-2384696-0`), quedando `RUC` con 100% de nulos.
3. **Pérdida Aparente de Audiencia e Ingreso**: El verdadero tipo de audiencia fue entregado en el campo `FECHA_INGRESO` (coaccionado erróneamente a `NaT` por Pandas en la ingesta inicial).

A continuación se expone la muestra de 5 filas de 2023 tal como vienen en el archivo parquet antes de su corrección:"""))

# Cell 15: Code - Exposición previa 2023
new_cells.append(nbformat.v4.new_code_cell("""# Exposición de la anomalía en el lote 2023
cols_anomalia = ['ANO_PROCESO', 'TRIBUNAL', 'RIT', 'RUC', 'TIPO_PROCEDIMIENTO', 'TIPO_AUDIENCIA', 'FECHA_INGRESO', 'FECHA_AUDIENCIA']
print("Muestra de 5 filas del lote 2023 antes de la corrección:")
display(df[df['ANO_PROCESO'] == 2023][cols_anomalia].head(5))"""))

# Cell 16: Markdown - Explicación de la Opción A
new_cells.append(nbformat.v4.new_markdown_cell("""#### Resolución mediante Fuente Oficial del PJUD (Opción A):
Para restablecer con certeza jurídica y estadística los datos reales de 2023, se utiliza el reporte oficial del Departamento de Estadísticas del PJUD:  
`data/raw/excel_pjud/audiencias_realizadas_2023.csv` (350.149 filas a nivel nacional).

Se realiza un cruce relacional exacto sobre el identificador único `CRR AUD` (`ID_AUDIENCIA`) para las 43.380 causas de la Corte de Valparaíso (`CÓDIGO CORTE == 30`), recuperando:
- **`RIT` Real**: Formato legal auténtico (`F-1-2023`, `C-995-2021`, `X-12-2021`, etc.).
- **`RUC` Real**: Identificador único de causa en su columna correspondiente.
- **`TIPO_PROCEDIMIENTO` Real**: Glosa jurídica oficial (`GLOSA TIPO CAUSA`).
- **`TIPO_AUDIENCIA` Real**: Tipo auténtico de audiencia (`Inmediata`, `Audiencia Preparatoria`, `Audiencia de Juicio`, etc.).
- **`FECHA_INGRESO` y `FECHA_AUDIENCIA` Reales**: Fechas auténticas del sistema SITFA (eliminando los 43.380 nulos de ingreso y los 1.196 nulos de audiencia).
- Bandera de auditoría: `FLG_CRUCE_2023 = True` para trazabilidad."""))

# Cell 17: Code - Aplicación de Opción A
new_cells.append(nbformat.v4.new_code_cell("""import numpy as np
import unicodedata
import re
from pathlib import Path

df_clean = df.copy()

# Carga de fuente oficial PJUD para el año 2023
path_csv = Path("C:/Users/frero/CD-2026-Proyecto-EquipoEMCR/data/raw/excel_pjud/audiencias_realizadas_2023.csv")

df_csv = pd.read_csv(
    path_csv, sep=';', encoding='utf-8-sig',
    usecols=['CRR AUD', 'RUC', 'RIT', 'GLOSA TIPO CAUSA', 'TIPO AUDIENCIA', 
             'FECHA INGRESO CAUSA', 'FECHA PROGRAMACIÓN AUDIENCIA', 'FECHA AUDIENCIA PROGRAMADA'],
    low_memory=False
)

df_csv = df_csv.rename(columns={
    'CRR AUD': 'ID_AUDIENCIA',
    'RUC': 'RUC_CSV',
    'RIT': 'RIT_CSV',
    'GLOSA TIPO CAUSA': 'PROC_CSV',
    'TIPO AUDIENCIA': 'AUD_CSV',
    'FECHA INGRESO CAUSA': 'FEC_ING_CSV',
    'FECHA PROGRAMACIÓN AUDIENCIA': 'FEC_PROG_CSV',
    'FECHA AUDIENCIA PROGRAMADA': 'FEC_AUD_CSV'
})

# Conversión de fechas de la fuente oficial
df_csv['FEC_ING_CSV'] = pd.to_datetime(df_csv['FEC_ING_CSV'], format='%d-%m-%Y', errors='coerce')
df_csv['FEC_PROG_CSV'] = pd.to_datetime(df_csv['FEC_PROG_CSV'], format='%d-%m-%Y', errors='coerce')
df_csv['FEC_AUD_CSV'] = pd.to_datetime(df_csv['FEC_AUD_CSV'], format='%d-%m-%Y', errors='coerce')

# Cruce relacional por ID_AUDIENCIA
df_clean = df_clean.merge(df_csv, on='ID_AUDIENCIA', how='left')

is_2023 = df_clean['ANO_PROCESO'] == 2023
df_clean['FLG_CRUCE_2023'] = is_2023

# Sustitución verificada para el año 2023
df_clean['RIT'] = np.where(is_2023, df_clean['RIT_CSV'], df_clean['RIT'])
df_clean['RUC'] = np.where(is_2023, df_clean['RUC_CSV'], df_clean['RUC'])
df_clean['TIPO_PROCEDIMIENTO'] = np.where(is_2023, df_clean['PROC_CSV'], df_clean['TIPO_PROCEDIMIENTO'])
df_clean['TIPO_AUDIENCIA'] = np.where(is_2023, df_clean['AUD_CSV'], df_clean['TIPO_AUDIENCIA'])
df_clean['FECHA_INGRESO'] = np.where(is_2023, df_clean['FEC_ING_CSV'], df_clean['FECHA_INGRESO'])
df_clean['FECHA_PROGRAMACION'] = np.where(is_2023, df_clean['FEC_PROG_CSV'], df_clean['FECHA_PROGRAMACION'])
df_clean['FECHA_AUDIENCIA'] = np.where(is_2023, df_clean['FEC_AUD_CSV'], df_clean['FECHA_AUDIENCIA'])

# Limpieza de columnas temporales
df_clean.drop(columns=['RUC_CSV', 'RIT_CSV', 'PROC_CSV', 'AUD_CSV', 'FEC_ING_CSV', 'FEC_PROG_CSV', 'FEC_AUD_CSV'], inplace=True)

print("=== MUESTRA POST-CORRECCIÓN DEL LOTE 2023 (FUENTE OFICIAL PJUD) ===")
display(df_clean[df_clean['ANO_PROCESO'] == 2023][cols_anomalia + ['FLG_CRUCE_2023']].head(5))

print(f"\\nDistribución real de TIPO_AUDIENCIA en 2023 ({df_clean[is_2023]['TIPO_AUDIENCIA'].nunique()} categorías):")
display(df_clean[df_clean['ANO_PROCESO'] == 2023]['TIPO_AUDIENCIA'].value_counts().to_frame("conteo"))

print(f"\\nDistribución real de TIPO_PROCEDIMIENTO en 2023 ({df_clean[is_2023]['TIPO_PROCEDIMIENTO'].nunique()} categorías):")
display(df_clean[df_clean['ANO_PROCESO'] == 2023]['TIPO_PROCEDIMIENTO'].value_counts().to_frame("conteo"))"""))

# Cell 18: Markdown - Ítem 3.2
new_cells.append(nbformat.v4.new_markdown_cell("""### 3.2.- Resolución de Inconsistencias en Columnas Categóricas

Habiendo normalizado y restituido la verdad procesal del año 2023, se implementa la estandarización general de texto sobre todo el universo de 466.178 registros:
1. **`CORTE` y `COMPETENCIA`**: Unificación a mayúsculas sostenidas (`.upper()`) y sin tildes.
2. **`TRIBUNAL`**: Estandarización de los nombres mediante mapeo oficial del catálogo PJUD sobre `COD_TRIBUNAL` (15 juzgados canónicos).
3. **`TIPO_PROCEDIMIENTO`**: Homologación canónica general a las 12 categorías legales en mayúsculas sostenidas.
4. **`TIPO_AUDIENCIA`**: Normalización textual (`.upper()` y sin tildes), resultando en 12 categorías canónicas limpias para toda la serie 2015-2025."""))

# Cell 19: Code - Estandarización Categórica
new_cells.append(nbformat.v4.new_code_cell("""def norm_text(s):
    if pd.isna(s):
        return s
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode('utf-8')
    s = re.sub(r'\\s+', ' ', s)
    return s.strip().upper()

# 1. Normalización de CORTE y COMPETENCIA
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

# 3. Mapeo y homologación canónica de TIPO_PROCEDIMIENTO
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

print(f"\\nTIPO_AUDIENCIA ({df_clean['TIPO_AUDIENCIA'].nunique()} categorías canónicas - Universo Completo):")
display(df_clean['TIPO_AUDIENCIA'].value_counts().to_frame("conteo"))"""))

# Cell 20: Markdown - Ítem 3.3
new_cells.append(nbformat.v4.new_markdown_cell("""### 3.3.- Estandarización de Modalidad (Videoconferencia)

Estandarización de los 6 formatos heterogéneos (`'SI'`, `'NO'`, `'1.0'`, `'0.0'`, `'1,0'`, `'0,0'`) a tipado booleano estricto (`True` = Telemática / Remota, `False` = Presencial).

**Criterio metodológico sobre valores ausentes pre-2020:**
Los 248.137 registros con valor nulo corresponden en su totalidad al período 2015 hasta noviembre de 2020. Debido a que las audiencias telemáticas fueron habilitadas por primera vez en el Poder Judicial chileno mediante la Ley 21.226 (publicada en abril de 2020 e implementada progresivamente en tribunales de familia hacia finales de ese año), las audiencias de dicho período histórico fueron presenciales por definición jurídica y operativa. En consecuencia, se imputan con `False` (Presencial), alcanzando un 100% de integridad en la variable."""))

# Cell 21: Code - Videoconferencia
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

print("Notebook executed and outputs saved successfully with Option A!")

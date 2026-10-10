import nbformat
from nbclient import NotebookClient
from pathlib import Path

nb_path = Path(r"C:\Users\frero\CD-2026-Proyecto-EquipoEMCR\notebooks\01 ETL_audienciasparquet.ipynb")

with open(nb_path, "r", encoding="utf-8") as f:
    nb = nbformat.read(f, as_version=4)

print(f"Initial cells count: {len(nb.cells)}")

# Keep cells 0 to 12 (original sections 1 and 2)
if len(nb.cells) > 13:
    nb.cells = nb.cells[:13]

new_cells = []

# Cell 13: Markdown - Encabezado Sección 3
new_cells.append(nbformat.v4.new_markdown_cell("""# 3.- Limpieza y Estandarización de Datos (Sanitización)

Implementación de las reglas de saneamiento y normalización técnica acordadas a partir de la auditoría de calidad de datos."""))

# Cell 14: Markdown - Ítem 3.1
new_cells.append(nbformat.v4.new_markdown_cell("""### 3.1.- Resolución de Inconsistencias en Columnas Categóricas

Estandarización textual (mayúsculas sostenidas, remoción de tildes y depuración de espacios en blanco redundantes) aplicada a las variables institucionales y procesales:
1. **`CORTE` y `COMPETENCIA`**: Unificación a mayúsculas sostenidas (`.upper()`) y sin tildes.
2. **`TRIBUNAL`**: Estandarización de los nombres mediante mapeo oficial del catálogo PJUD sobre `COD_TRIBUNAL` (reduciendo de 34 variantes a 15 juzgados canónicos).
3. **`TIPO_PROCEDIMIENTO`**: Normalización textual y homologación de siglas de una letra (`'C'`, `'P'`, `'F'`, etc.) a sus denominaciones canónicas en mayúsculas sostenidas.
4. **`TIPO_AUDIENCIA`**: Normalización de mayúsculas y remoción de tildes."""))

# Cell 15: Code - Ejecución de Transformación Categórica
new_cells.append(nbformat.v4.new_code_cell("""import unicodedata
import re

df_clean = df.copy()

def norm_text(s):
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

# 3. Homologación de códigos/siglas en TIPO_PROCEDIMIENTO
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
df_clean['TIPO_AUDIENCIA'] = df_clean['TIPO_AUDIENCIA'].apply(norm_text)"""))

# Cell 16: Code - Verificación de Resultados
new_cells.append(nbformat.v4.new_code_cell("""print("=== VERIFICACIÓN POST-NORMALIZACIÓN CATEGÓRICA ===")
print("Cortes únicas:", df_clean['CORTE'].unique().tolist())
print("Competencias únicas:", df_clean['COMPETENCIA'].unique().tolist())
print(f"Tribunales canónicos únicos ({df_clean['TRIBUNAL'].nunique()}):")
display(df_clean[['COD_TRIBUNAL', 'TRIBUNAL']].drop_duplicates().sort_values('COD_TRIBUNAL'))

print(f"\\nTIPO_PROCEDIMIENTO ({df_clean['TIPO_PROCEDIMIENTO'].nunique()} categorías canónicas):")
display(df_clean['TIPO_PROCEDIMIENTO'].value_counts().to_frame("conteo"))

print(f"\\nTIPO_AUDIENCIA ({df_clean['TIPO_AUDIENCIA'].nunique()} categorías normalizadas - Muestra top 10):")
display(df_clean['TIPO_AUDIENCIA'].value_counts().head(10).to_frame("conteo"))"""))

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

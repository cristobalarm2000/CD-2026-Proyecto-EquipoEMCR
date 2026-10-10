import nbformat
from nbclient import NotebookClient
from pathlib import Path

nb_path = Path(r"C:\Users\frero\CD-2026-Proyecto-EquipoEMCR\notebooks\01 ETL_audienciasparquet.ipynb")
with open(nb_path, "r", encoding="utf-8") as f:
    nb = nbformat.read(f, as_version=4)

print(f"Initial cells count: {len(nb.cells)}")

new_cells = []

# Cell 28: Markdown 3.7
new_cells.append(nbformat.v4.new_markdown_cell("""### 3.7.- Normalización de RIT y Creación de Clave Compuesta de Causa (`ID_CAUSA_RIT`)

Resolución de la inconsistencia de formato en la columna `RIT` y construcción del identificador único de causa:
1. **Normalización Textual**: Corrección del patrón de doble guión (`--` $\\rightarrow$ `-`) en 41.439 registros (8,89% del universo).
2. **Validación Canónica**: Verificación mediante expresión regular del estándar judicial `Letra-Correlativo-Año` (`^[A-Z]{1,2}-\\d+-\\d{4}$`), alcanzando un **100,0% de conformidad (466.178 de 466.178 registros)**.
3. **Clave Compuesta Jurisdiccional (`ID_CAUSA_RIT`)**: Dado que el RIT es un correlativo propio de cada juzgado y no un identificador global, se genera la clave compuesta `COD_TRIBUNAL + '-' + RIT` (ej. `1261-A-5-2015`), permitiendo aislar con certeza jurídica las causas únicas y analizar la recurrencia de audiencias por causa."""))

# Cell 29: Code 3.7
new_cells.append(nbformat.v4.new_code_cell("""# 1. Corrección de inconsistencia de formato en RIT (reemplazo de doble guión por guión simple)
df_clean['RIT'] = df_clean['RIT'].astype(str).str.strip().str.upper().str.replace('--', '-', regex=False)

# 2. Validación de formato canónico Letra-Correlativo-Año
patron_rit = r'^[A-Z]{1,2}-\\d+-\\d{4}$'
rit_valido = df_clean['RIT'].str.match(patron_rit)
print("=== VALIDACIÓN DE FORMATO RIT ===")
print(f"Total registros: {len(df_clean):,}")
print(f"Registros conformes con Letra-Correlativo-Año: {rit_valido.sum():,} ({rit_valido.mean()*100:.2f}%)")
print(f"Registros no conformes: {(~rit_valido).sum()}")

# 3. Creación de la clave compuesta de causa única
df_clean['ID_CAUSA_RIT'] = df_clean['COD_TRIBUNAL'].astype(str) + '-' + df_clean['RIT']

print("\\n=== IDENTIFICACIÓN DE CAUSAS ÚNICAS ===")
print(f"Total de audiencias en el dataset: {len(df_clean):,}")
print(f"Total de causas judiciales únicas (ID_CAUSA_RIT): {df_clean['ID_CAUSA_RIT'].nunique():,}")
print(f"Promedio de audiencias por causa: {len(df_clean) / df_clean['ID_CAUSA_RIT'].nunique():.2f}")

print("\\nMuestra de causas y audiencias asociadas:")
display(df_clean[['COD_TRIBUNAL', 'TRIBUNAL', 'RIT', 'ID_CAUSA_RIT', 'TIPO_AUDIENCIA']].head(6))"""))

nb.cells.extend(new_cells)
print(f"New total cells count: {len(nb.cells)}")

with open(nb_path, "w", encoding="utf-8") as f:
    nbformat.write(nb, f)

print("Executing notebook with nbclient...")
client = NotebookClient(nb, timeout=600, kernel_name="python3")
executed_nb = client.execute()

with open(nb_path, "w", encoding="utf-8") as f:
    nbformat.write(executed_nb, f)

print("Notebook successfully executed and saved with Section 3.7!")

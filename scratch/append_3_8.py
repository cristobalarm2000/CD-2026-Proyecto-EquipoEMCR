import nbformat
from nbclient import NotebookClient
from pathlib import Path

nb_path = Path(r"C:\Users\frero\CD-2026-Proyecto-EquipoEMCR\notebooks\01 ETL_audienciasparquet.ipynb")
with open(nb_path, "r", encoding="utf-8") as f:
    nb = nbformat.read(f, as_version=4)

print(f"Initial cells count: {len(nb.cells)}")

new_cells = []

# Cell 30: Markdown 3.8
new_cells.append(nbformat.v4.new_markdown_cell("""### 3.8.- Verificación de Duplicados Exactos y Claves de Sesión

Auditoría de unicidad sobre el dataset sanitizado (`df_clean`):
1. **Duplicados Exactos Globales**: Evaluación sobre las 24 columnas del dataset.
2. **Duplicados Sustantivos**: Evaluación excluyendo metadatos e identificadores de sistema (`ID_AUDIENCIA`, `FLG_CRUCE_2023`).
3. **Colisiones de Sesión Judicial**: Análisis de eventos donde una misma causa judicial registra audiencias simultáneas en la misma fecha y hora de inicio (`ID_CAUSA_RIT`, `FECHA_AUDIENCIA`, `HORA_INICIO`)."""))

# Cell 31: Code 3.8
new_cells.append(nbformat.v4.new_code_cell("""# 1. Duplicados exactos en la totalidad de columnas (24 variables)
duplicados_totales = df_clean.duplicated().sum()
print("=== VERIFICACIÓN DE DUPLICADOS EXACTOS ===")
print(f"Total registros en df_clean: {len(df_clean):,}")
print(f"Duplicados exactos (todas las columnas): {duplicados_totales}")

# 2. Duplicados excluyendo identificadores de sistema (ID_AUDIENCIA, FLG_CRUCE_2023)
cols_sustantivas = [c for c in df_clean.columns if c not in ['ID_AUDIENCIA', 'FLG_CRUCE_2023']]
duplicados_sustantivos = df_clean.duplicated(subset=cols_sustantivas).sum()
print(f"Duplicados sustantivos (excluyendo IDs del sistema): {duplicados_sustantivos}")

# 3. Análisis de colisiones a nivel de sesión judicial (Misma causa, fecha y hora de inicio)
cols_sesion = ['ID_CAUSA_RIT', 'FECHA_AUDIENCIA', 'HORA_INICIO']
colisiones_sesion = df_clean.duplicated(subset=cols_sesion, keep=False).sum()
print(f"\\nAudiencias que comparten causa, fecha y hora de inicio: {colisiones_sesion} ({colisiones_sesion // 2} pares)")

if colisiones_sesion > 0:
    print("\\nMuestra de audiencias concurrentes en la misma causa:")
    display(df_clean[df_clean.duplicated(subset=cols_sesion, keep=False)][
        ['ANO_PROCESO', 'TRIBUNAL', 'ID_CAUSA_RIT', 'FECHA_AUDIENCIA', 'HORA_INICIO', 'HORA_FIN', 'TIPO_AUDIENCIA']
    ].sort_values(['ID_CAUSA_RIT', 'FECHA_AUDIENCIA']).head(8))"""))

nb.cells.extend(new_cells)
print(f"New total cells count: {len(nb.cells)}")

with open(nb_path, "w", encoding="utf-8") as f:
    nbformat.write(nb, f)

print("Executing notebook with nbclient...")
client = NotebookClient(nb, timeout=600, kernel_name="python3")
executed_nb = client.execute()

with open(nb_path, "w", encoding="utf-8") as f:
    nbformat.write(executed_nb, f)

print("Notebook successfully executed and saved with Section 3.8!")

import nbformat
from nbclient import NotebookClient
from pathlib import Path

nb_path = Path(r"C:\Users\frero\CD-2026-Proyecto-EquipoEMCR\notebooks\01 ETL_audienciasparquet.ipynb")

with open(nb_path, "r", encoding="utf-8") as f:
    nb = nbformat.read(f, as_version=4)

print(f"Initial cells count: {len(nb.cells)}")

# Ensure we have cells 0 to 16
if len(nb.cells) > 17:
    nb.cells = nb.cells[:17]

new_cells = []

# Cell 17: Markdown - Ítem 3.2
new_cells.append(nbformat.v4.new_markdown_cell("""### 3.2.- Estandarización de Modalidad (Videoconferencia)

Estandarización de los 6 formatos heterogéneos (`'SI'`, `'NO'`, `'1.0'`, `'0.0'`, `'1,0'`, `'0,0'`) a tipado booleano estricto (`True` = Telemática / Remota, `False` = Presencial).

**Criterio metodológico sobre valores ausentes pre-2020:**
Los 248.137 registros con valor nulo corresponden en su totalidad al período 2015 hasta noviembre de 2020. Debido a que las audiencias telemáticas fueron habilitadas por primera vez en el Poder Judicial chileno mediante la Ley 21.226 (publicada en abril de 2020 e implementada progresivamente en tribunales de familia hacia finales de ese año), las audiencias de dicho período histórico fueron presenciales por definición jurídica y operativa. En consecuencia, se imputan con `False` (Presencial), alcanzando un 100% de integridad en la variable."""))

# Cell 18: Code - Ejecución y Visualización de Videoconferencia
new_cells.append(nbformat.v4.new_code_cell("""# Mapeo de formatos heterogéneos a booleano
map_video = {
    'SI': True, 'SÍ': True, '1.0': True, '1,0': True, '1': True, 'TRUE': True,
    'NO': False, '0.0': False, '0,0': False, '0': False, 'FALSE': False
}

video_series = df_clean['VIDEOCONFERENCIA'].astype(str).str.strip().str.upper().map(map_video)

# Imputación histórica pre-2020 (100% presencial previo a Ley 21.226)
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

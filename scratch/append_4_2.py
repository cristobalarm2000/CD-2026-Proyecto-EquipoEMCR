import nbformat
from nbclient import NotebookClient
from pathlib import Path

nb_path = Path(r"C:\Users\frero\CD-2026-Proyecto-EquipoEMCR\notebooks\01 ETL_audienciasparquet.ipynb")
with open(nb_path, "r", encoding="utf-8") as f:
    nb = nbformat.read(f, as_version=4)

print(f"Initial cells count: {len(nb.cells)}")

new_cells = []

# Cell 35: Markdown 4.2
new_cells.append(nbformat.v4.new_markdown_cell("""### 4.2.- Depuración de Columnas y Anonimización del Modelo (Eliminación de RUC, ID_CAUSA, ID_AUDIENCIA y FECHA_FIRMA)

Conforme a las definiciones de modelamiento para inteligencia de negocio (BI) en un estudio jurídico y las directrices de privacidad de datos, se procede a la eliminación formal de 4 variables:

1. **`RUC` (81,24% de nulos)**: Identificador nacional de causa. Se elimina para anonimizar los expedientes judiciales de familia y porque la causa queda unívocamente identificada mediante la clave compuesta canónica `ID_CAUSA_RIT`.
2. **`ID_CAUSA` (71,64% de nulos)**: Clave interna de backend del SITFA ausente en la serie histórica (2015-2020). Reemplazado plenamente por `ID_CAUSA_RIT`.
3. **`ID_AUDIENCIA` (62,34% de nulos)**: Identificador técnico de sistema no disponible en años antiguos y redundante con la granularidad temporal de la audiencia (`ID_CAUSA_RIT` + `FECHA_AUDIENCIA` + `HORA_INICIO`).
4. **`FECHA_FIRMA` (62,68% de nulos)**:
   - **Fundamento procesal:** En los juicios de familia (Ley 19.968), las resoluciones se notifican oralmente a las partes en la misma audiencia; el soporte auténtico es el audio y los plazos fatales corren desde la audiencia, no desde la suscripción electrónica posterior del acta.
   - **Fundamento analítico y de BI:** No incide en la planificación, agenda ni tarificación de la firma legal. Además, presenta 100% de nulos en 2015-2020 y 2025, no existe en el catálogo oficial del PJUD de 2023, y en 2024 es idéntica en el 100% de los casos a `FECHA_AUDIENCIA`."""))

# Cell 36: Code 4.2
new_cells.append(nbformat.v4.new_code_cell("""# Eliminación de columnas según definición de negocio y anonimización
cols_drop = ['RUC', 'ID_CAUSA', 'ID_AUDIENCIA', 'FECHA_FIRMA']
df_clean.drop(columns=cols_drop, inplace=True)

print("=== DIMENSIONES POST-DEPURACIÓN ===")
print(f"Dimensiones de df_clean: {df_clean.shape[0]:,} filas x {df_clean.shape[1]} columnas")
print("\\nColumnas conservadas en el modelo:")
print(df_clean.columns.tolist())

# Evaluación de nulos remanentes
nulos_remanentes = pd.DataFrame({
    "nulos": df_clean.isna().sum(),
    "% nulos": (df_clean.isna().mean() * 100).round(4),
    "dtype": df_clean.dtypes.astype(str)
}).sort_values("% nulos", ascending=False)

print("\\nResumen de variables con valores ausentes restantes:")
display(nulos_remanentes[nulos_remanentes['nulos'] > 0])"""))

nb.cells.extend(new_cells)
print(f"New total cells count: {len(nb.cells)}")

with open(nb_path, "w", encoding="utf-8") as f:
    nbformat.write(nb, f)

print("Executing notebook with nbclient...")
client = NotebookClient(nb, timeout=600, kernel_name="python3")
executed_nb = client.execute()

with open(nb_path, "w", encoding="utf-8") as f:
    nbformat.write(executed_nb, f)

print("Notebook successfully executed and saved with Section 4.2!")

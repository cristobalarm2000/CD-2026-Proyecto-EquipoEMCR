import nbformat
from nbclient import NotebookClient
from pathlib import Path

nb_path = Path(r"C:\Users\frero\CD-2026-Proyecto-EquipoEMCR\notebooks\01 ETL_audienciasparquet.ipynb")
with open(nb_path, "r", encoding="utf-8") as f:
    nb = nbformat.read(f, as_version=4)

print(f"Initial cells count: {len(nb.cells)}")

new_cells = []

# Cell 32: Markdown - Encabezado Sección 4
new_cells.append(nbformat.v4.new_markdown_cell("""# 4.- Datos Faltantes

Diagnóstico, perfil de calidad y estrategia para el tratamiento de valores nulos o ausentes en el dataset sanitizado."""))

# Cell 33: Markdown - Ítem 4.1
new_cells.append(nbformat.v4.new_markdown_cell("""### 4.1.- Perfil de Calidad y Visualización de % Nulos por Columna

Evaluación detallada de completitud sobre las 24 variables consolidadas de `df_clean`:
- Identificación de variables íntegras (100% completitud) vs variables con valores ausentes.
- Cuantificación de valores nulos absolutos y porcentuales para orientar las reglas de imputación o preservación."""))

# Cell 34: Code - Perfil y Gráfico
new_cells.append(nbformat.v4.new_code_cell("""# Perfil de calidad para la Sección 4: Datos Faltantes
perfil_faltantes = pd.DataFrame({
    "dtype": df_clean.dtypes.astype(str),
    "nulos": df_clean.isna().sum(),
    "% nulos": (df_clean.isna().mean() * 100).round(2),
    "unicos": df_clean.nunique(dropna=True),
    "ejemplo": df_clean.iloc[0]
}).sort_values("% nulos", ascending=False)

print("=== PERFIL DE CALIDAD: DATOS FALTANTES (df_clean) ===")
display(perfil_faltantes)

# Visualización de % Nulos por Columna
missing_s4 = df_clean.isna().mean().sort_values(ascending=False) * 100
missing_s4 = missing_s4[missing_s4 > 0]

plt.figure(figsize=(9, 4.5))
bars = plt.bar(missing_s4.index, missing_s4.values, color="#e377c2", edgecolor="#7f7f7f", linewidth=0.8)
plt.ylabel("% de valores faltantes", fontsize=11)
plt.title("Porcentaje de Valores Nulos por Variable (Sección 4: Datos Faltantes)", fontsize=12, fontweight="bold")
plt.xticks(rotation=35, ha="right", fontsize=10)
plt.grid(axis='y', linestyle='--', alpha=0.5)

# Etiquetas de porcentaje sobre cada barra
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2.0, yval + 1, f"{yval:.2f}%", ha='center', va='bottom', fontsize=9)

plt.ylim(0, max(missing_s4.values) * 1.15)
plt.tight_layout()
plt.show()"""))

nb.cells.extend(new_cells)
print(f"New total cells count: {len(nb.cells)}")

with open(nb_path, "w", encoding="utf-8") as f:
    nbformat.write(nb, f)

print("Executing notebook with nbclient...")
client = NotebookClient(nb, timeout=600, kernel_name="python3")
executed_nb = client.execute()

with open(nb_path, "w", encoding="utf-8") as f:
    nbformat.write(executed_nb, f)

print("Notebook successfully executed and saved with Section 4!")

import nbformat
from nbclient import NotebookClient
from pathlib import Path

nb_path = Path(r"C:\Users\frero\CD-2026-Proyecto-EquipoEMCR\notebooks\01 ETL_audienciasparquet.ipynb")
with open(nb_path, "r", encoding="utf-8") as f:
    nb = nbformat.read(f, as_version=4)

print(f"Initial cells count: {len(nb.cells)}")

# Keep cells 0 to 21
nb.cells = nb.cells[:22]

new_cells = []

# Cell 22: Markdown 3.4
new_cells.append(nbformat.v4.new_markdown_cell("""### 3.4.- Homogeneización de Formatos Horarios (HORA_INICIO y HORA_FIN)

Estandarización de las marcas temporales de inicio y término de las audiencias a formato uniforme `HH:MM:SS`:
- Se corrigen los 3 registros con longitud 4 (`H:MM`, ej. `8:38` -> `08:38:00`).
- Se homogeneizan los 292.378 registros en formato `HH:MM` agregando precisión de segundos (`:00`).
- Se preservan intactos los únicos 2 valores nulos registrados en `HORA_FIN`.
- **Criterio metodológico:** Se mantiene el dataset limpio en sus variables originales sin introducir cálculo de features derivadas (ej. duración) ni alterar valores atípicos hasta su posterior análisis consensuado."""))

# Cell 23: Code 3.4
new_cells.append(nbformat.v4.new_code_cell("""def norm_hora(s):
    if pd.isna(s):
        return np.nan
    s_str = str(s).strip()
    if not s_str or s_str == 'nan':
        return np.nan
    if len(s_str) == 4 and s_str[1] == ':':
        s_str = '0' + s_str
    if len(s_str) == 5 and s_str[2] == ':':
        s_str = s_str + ':00'
    return s_str

df_clean['HORA_INICIO'] = df_clean['HORA_INICIO'].apply(norm_hora)
df_clean['HORA_FIN'] = df_clean['HORA_FIN'].apply(norm_hora)

print("=== VERIFICACIÓN DE HOMOGENEIZACIÓN HORARIA ===")
print("Longitud de cadena HORA_INICIO:", df_clean['HORA_INICIO'].str.len().value_counts().to_dict())
print("Longitud de cadena HORA_FIN:", df_clean['HORA_FIN'].str.len().value_counts().to_dict())
print("\\nMuestra de 5 filas de horarios estandarizados:")
display(df_clean[['HORA_INICIO', 'HORA_FIN']].head(5))"""))

# Cell 24: Markdown 3.5
new_cells.append(nbformat.v4.new_markdown_cell("""### 3.5.- Estandarización y Casteo de Tipos Numéricos

Ajuste de tipado en variables enteras discretas:
1. **`ANO_AUDIENCIA`**: Casteo de `float64` a `Int64` (entero de 64 bits con soporte de valores nulos).
2. **`PLAZO_AGENDAMIENTO`**: Casteo de `float64` a `Int64`.
   - Se preservan intactos los 16 casos con plazos negativos (-6 a -2 días) y los 97 valores ausentes, sin forzar imputaciones ni alteraciones numéricas, para su posterior análisis de negocio."""))

# Cell 25: Code 3.5
new_cells.append(nbformat.v4.new_code_cell("""df_clean['ANO_AUDIENCIA'] = df_clean['ANO_AUDIENCIA'].astype('Int64')
df_clean['PLAZO_AGENDAMIENTO'] = df_clean['PLAZO_AGENDAMIENTO'].astype('Int64')

print("=== VERIFICACIÓN DE CASTEO NUMÉRICO ===")
print("Dtype ANO_AUDIENCIA:", df_clean['ANO_AUDIENCIA'].dtype)
print("Dtype PLAZO_AGENDAMIENTO:", df_clean['PLAZO_AGENDAMIENTO'].dtype)
print("\\nResumen estadístico de PLAZO_AGENDAMIENTO:")
display(df_clean['PLAZO_AGENDAMIENTO'].describe().to_frame())"""))

# Cell 26: Markdown 3.6
new_cells.append(nbformat.v4.new_markdown_cell("""### 3.6.- Perfil de Calidad y Visualización de % Nulos por Columna (Dataset Sanitizado)

Evaluación integral del estado de completitud y tipos de datos del dataset sanitizado (`df_clean`), permitiendo dimensionar el impacto de la limpieza y la reducción de valores ausentes."""))

# Cell 27: Code 3.6
new_cells.append(nbformat.v4.new_code_cell("""# Perfil de calidad post-sanitización
perfil_sanitizado = pd.DataFrame({
    "dtype": df_clean.dtypes.astype(str),
    "nulos": df_clean.isna().sum(),
    "% nulos": (df_clean.isna().mean() * 100).round(2),
    "unicos": df_clean.nunique(dropna=True),
    "ejemplo": df_clean.iloc[0]
}).sort_values("% nulos", ascending=False)

print("=== PERFIL DE CALIDAD POST-SANITIZACIÓN ===")
display(perfil_sanitizado)

# Visualización de % Nulos por Columna
missing_clean = df_clean.isna().mean().sort_values(ascending=False) * 100
missing_clean = missing_clean[missing_clean > 0]

plt.figure(figsize=(9, 4))
plt.bar(missing_clean.index, missing_clean.values, color="#2ca02c")
plt.ylabel("% de valores faltantes")
plt.title("Missingness por variable post-sanitización (df_clean)")
plt.xticks(rotation=35, ha="right")
plt.grid(axis='y', linestyle='--', alpha=0.5)
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

print("Notebook successfully executed and saved!")

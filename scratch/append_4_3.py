import nbformat
from nbclient import NotebookClient
from pathlib import Path

nb_path = Path(r"C:\Users\frero\CD-2026-Proyecto-EquipoEMCR\notebooks\01 ETL_audienciasparquet.ipynb")
with open(nb_path, "r", encoding="utf-8") as f:
    nb = nbformat.read(f, as_version=4)

print(f"Initial cells count: {len(nb.cells)}")

new_cells = []

# Cell 37: Markdown 4.3
new_cells.append(nbformat.v4.new_markdown_cell("""### 4.3.- Tratamiento e Imputación de Faltantes Remanentes (HORA_FIN, FECHA_PROGRAMACION y PLAZO_AGENDAMIENTO)

Implementación del plan consensuado para alcanzar el 100% de completitud en las variables procesales y temporales:

1. **`HORA_FIN` (2 registros nulos)**:
   - Imputación mediante la **mediana de duración de Audiencia Preparatoria (18 minutos)** sumada a `HORA_INICIO`.
   - Limache (2020): `08:48:00` + 18 min $\\rightarrow$ `09:06:00`.
   - Quintero (2022): `11:00:00` + 18 min $\\rightarrow$ `11:18:00`.
2. **`FECHA_PROGRAMACION` (9.228 registros nulos)**:
   - El 100% corresponde a **Audiencias Inmediatas** (trámites cautelares de urgencia en VIF y medidas de protección según Ley 19.968).
   - Se imputa con **`FECHA_AUDIENCIA`**, reflejando la realidad procesal: citación y celebración ocurren el **mismo día** en el acto.
3. **`PLAZO_AGENDAMIENTO` (97 nulos y 16 negativos)**:
   - Se imputan a **`0` días** los 97 valores ausentes (adoptando el estándar oficial del PJUD para audiencias inmediatas de espera nula).
   - Se corrigen los 16 plazos negativos a **`0` días** (trámites inmediatos ingresados con desfase administrativo)."""))

# Cell 38: Code 4.3
new_cells.append(nbformat.v4.new_code_cell("""# 1. Imputación de HORA_FIN mediante mediana de duración (18 min)
def imputar_hora_fin(row):
    if pd.isna(row['HORA_FIN']):
        h_ini = str(row['HORA_INICIO'])
        parts = h_ini.split(':')
        hh = int(parts[0])
        mm = int(parts[1]) + 18
        if mm >= 60:
            hh += mm // 60
            mm = mm % 60
        return f"{hh:02d}:{mm:02d}:00"
    return row['HORA_FIN']

df_clean['HORA_FIN'] = df_clean.apply(imputar_hora_fin, axis=1)

# 2. Imputación de FECHA_PROGRAMACION (Audiencias inmediatas del mismo día)
df_clean['FECHA_PROGRAMACION'] = df_clean['FECHA_PROGRAMACION'].fillna(df_clean['FECHA_AUDIENCIA'])

# 3. Imputación y corrección de PLAZO_AGENDAMIENTO (Espera nula = 0 días)
df_clean['PLAZO_AGENDAMIENTO'] = df_clean['PLAZO_AGENDAMIENTO'].fillna(0)
df_clean['PLAZO_AGENDAMIENTO'] = np.where(df_clean['PLAZO_AGENDAMIENTO'] < 0, 0, df_clean['PLAZO_AGENDAMIENTO'])
df_clean['PLAZO_AGENDAMIENTO'] = df_clean['PLAZO_AGENDAMIENTO'].astype('Int64')

print("=== VERIFICACIÓN DE COMPLETITUD TOTAL POST-IMPUTACIÓN ===")
print(f"Dimensiones finales: {df_clean.shape[0]:,} filas x {df_clean.shape[1]} columnas")
print(f"Total valores nulos en el dataset completo: {df_clean.isna().sum().sum()}")

# Perfil final
perfil_final = pd.DataFrame({
    "dtype": df_clean.dtypes.astype(str),
    "nulos": df_clean.isna().sum(),
    "% completitud": ((1 - df_clean.isna().mean()) * 100).round(2),
    "unicos": df_clean.nunique(),
    "ejemplo": df_clean.iloc[0]
})
display(perfil_final)"""))

nb.cells.extend(new_cells)
print(f"New total cells count: {len(nb.cells)}")

with open(nb_path, "w", encoding="utf-8") as f:
    nbformat.write(nb, f)

print("Executing notebook with nbclient...")
client = NotebookClient(nb, timeout=600, kernel_name="python3")
executed_nb = client.execute()

with open(nb_path, "w", encoding="utf-8") as f:
    nbformat.write(executed_nb, f)

print("Notebook successfully executed and saved with Section 4.3!")

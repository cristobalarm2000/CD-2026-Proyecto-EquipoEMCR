import pandas as pd
import numpy as np
import unicodedata, re, time

t0 = time.time()
raw_path = r"C:\Users\frero\CD-2026-Proyecto-EquipoEMCR\data\raw\parquet\audiencias_realizadas_competencia_detalle.parquet"
df = pd.read_parquet(raw_path)
print(f"Cargado raw: {df.shape} en {time.time() - t0:.2f}s")

# Copia de trabajo
df_clean = df.copy()

# Función auxiliar de limpieza de texto
def norm_text(s):
    if pd.isna(s): return s
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode('utf-8')
    s = re.sub(r'\s+', ' ', s)
    return s.strip().upper()

# 1. Normalización de CORTE
df_clean['CORTE'] = df_clean['CORTE'].apply(norm_text)

# 2. Catálogo canónico de TRIBUNAL por COD_TRIBUNAL
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

# 3. Corrección del cruce 2023 y normalización de procedimientos y audiencias
# Detectar anomalía de cruce en 2023
is_2023 = df_clean['ANO_PROCESO'] == 2023
df_clean['FLG_CRUCE_2023'] = is_2023

# Mapeo de códigos de procedimiento
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

# Limpiar texto base
proc_norm = df_clean['TIPO_PROCEDIMIENTO'].apply(norm_text).replace(map_proc_codes)
aud_norm = df_clean['TIPO_AUDIENCIA'].apply(norm_text)

# En 2023, TIPO_AUDIENCIA traía el procedimiento:
# Usar el procedimiento de aud_norm si proc_norm es una sigla o menor detalle
proc_2023_mapped = aud_norm.replace(map_proc_codes)
proc_final = np.where(is_2023, proc_2023_mapped, proc_norm)
df_clean['TIPO_PROCEDIMIENTO'] = proc_final

# Para TIPO_AUDIENCIA en 2023, marcarlo como NO ESPECIFICADA
aud_final = np.where(is_2023, 'NO ESPECIFICADA', aud_norm)
df_clean['TIPO_AUDIENCIA'] = aud_final

# 4. Estandarización de VIDEOCONFERENCIA a booleano
map_video = {
    'SI': True, 'SÍ': True, '1.0': True, '1,0': True, '1': True, 'TRUE': True,
    'NO': False, '0.0': False, '0,0': False, '0': False, 'FALSE': False
}
video_series = df_clean['VIDEOCONFERENCIA'].astype(str).str.strip().str.upper().map(map_video)
# Para registros pre-2020 (antes de pandemia / Ley 21.226), eran 100% presenciales -> False
df_clean['VIDEOCONFERENCIA'] = video_series.fillna(False).astype(bool)

# 5. Normalización de horas y cálculo de DURACION_MINUTOS
h_ini = pd.to_datetime(df_clean['HORA_INICIO'], format='%H:%M', errors='coerce').fillna(
    pd.to_datetime(df_clean['HORA_INICIO'], format='%H:%M:%S', errors='coerce')
)
h_fin = pd.to_datetime(df_clean['HORA_FIN'], format='%H:%M', errors='coerce').fillna(
    pd.to_datetime(df_clean['HORA_FIN'], format='%H:%M:%S', errors='coerce')
)

dur = (h_fin - h_ini).dt.total_seconds() / 60.0
dur = dur.apply(lambda x: x + 1440 if pd.notna(x) and x < 0 else x)
# Acotar valores válidos entre 0 y 480 min
df_clean['DURACION_MINUTOS'] = dur.apply(lambda x: x if pd.notna(x) and 0 <= x <= 480 else np.nan)
df_clean['HORA_INICIO'] = h_ini.dt.strftime('%H:%M:%S')
df_clean['HORA_FIN'] = h_fin.dt.strftime('%H:%M:%S')

# 6. Reclasificación numérica y corrección de PLAZO_AGENDAMIENTO
df_clean['ANO_AUDIENCIA'] = df_clean['ANO_AUDIENCIA'].astype('Int64')

# Plazos negativos: flag y reemplazo con pd.NA para análisis robusto
df_clean['ANOMALIA_PLAZO_NEGATIVO'] = df_clean['PLAZO_AGENDAMIENTO'] < 0
plazo_corregido = df_clean['PLAZO_AGENDAMIENTO'].apply(lambda x: np.nan if pd.notna(x) and x < 0 else x)
df_clean['PLAZO_AGENDAMIENTO'] = plazo_corregido.astype('Int64')

# 7. Construcción de KEY_CAUSA y TIPO_CAUSA
df_clean['KEY_CAUSA'] = (
    df_clean['COD_CORTE'].astype(str) + '-' +
    df_clean['COD_TRIBUNAL'].astype(str) + '-' +
    df_clean['RIT'].astype(str)
)
df_clean['TIPO_CAUSA'] = df_clean['RIT'].astype(str).str.extract(r'^([A-Za-z]+)-')[0]
df_clean['RUC'] = df_clean['RUC'].fillna('SIN_RUC').astype(str)

print("\n--- RESUMEN TRAS LIMPIEZA ---")
print(f"Dimensiones: {df_clean.shape}")
print(f"Columnas: {df_clean.columns.tolist()}")
print(f"KEY_CAUSA únicas: {df_clean['KEY_CAUSA'].nunique()} (nulos: {df_clean['KEY_CAUSA'].isna().sum()})")
print(f"TIPO_PROCEDIMIENTO únicos ({df_clean['TIPO_PROCEDIMIENTO'].nunique()}):\n{df_clean['TIPO_PROCEDIMIENTO'].value_counts()}")
print(f"\nTIPO_AUDIENCIA únicos ({df_clean['TIPO_AUDIENCIA'].nunique()}):\n{df_clean['TIPO_AUDIENCIA'].value_counts()}")
print(f"\nVIDEOCONFERENCIA counts:\n{df_clean['VIDEOCONFERENCIA'].value_counts()}")
print(f"\nDURACION_MINUTOS stats:\n{df_clean['DURACION_MINUTOS'].describe()}")
print(f"\nPLAZO_AGENDAMIENTO stats:\n{df_clean['PLAZO_AGENDAMIENTO'].describe()}")
print(f"Tiempo total: {time.time() - t0:.2f}s")

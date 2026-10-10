import pandas as pd
import numpy as np
from pathlib import Path

# Cargar y preparar df_clean tal como está en el pipeline actual
parquet_path = Path("data/raw/parquet/audiencias_realizadas_competencia_detalle.parquet")
df = pd.read_parquet(parquet_path)

# 3.1 Tratamiento 2023
path_csv = Path("data/raw/excel_pjud/audiencias_realizadas_2023.csv")
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
df_csv['FEC_ING_CSV'] = pd.to_datetime(df_csv['FEC_ING_CSV'], format='%d-%m-%Y', errors='coerce')
df_csv['FEC_PROG_CSV'] = pd.to_datetime(df_csv['FEC_PROG_CSV'], format='%d-%m-%Y', errors='coerce')
df_csv['FEC_AUD_CSV'] = pd.to_datetime(df_csv['FEC_AUD_CSV'], format='%d-%m-%Y', errors='coerce')

df = df.merge(df_csv, on='ID_AUDIENCIA', how='left')
is_23 = df['ANO_PROCESO'] == 2023
df['FLG_CRUCE_2023'] = is_23
df['RIT'] = np.where(is_23, df['RIT_CSV'], df['RIT'])
df['TIPO_PROCEDIMIENTO'] = np.where(is_23, df['PROC_CSV'], df['TIPO_PROCEDIMIENTO'])
df['TIPO_AUDIENCIA'] = np.where(is_23, df['AUD_CSV'], df['TIPO_AUDIENCIA'])
df['FECHA_INGRESO'] = np.where(is_23, df['FEC_ING_CSV'], df['FECHA_INGRESO'])
df['FECHA_PROGRAMACION'] = np.where(is_23, df['FEC_PROG_CSV'], df['FECHA_PROGRAMACION'])
df['FECHA_AUDIENCIA'] = np.where(is_23, df['FEC_AUD_CSV'], df['FECHA_AUDIENCIA'])
df.drop(columns=['RUC_CSV', 'RIT_CSV', 'PROC_CSV', 'AUD_CSV', 'FEC_ING_CSV', 'FEC_PROG_CSV', 'FEC_AUD_CSV'], inplace=True)

# Normalizaciones
import unicodedata
def norm_text(text):
    if pd.isna(text): return np.nan
    s = str(text).strip().upper()
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

df['CORTE'] = df['CORTE'].apply(norm_text)
df['COMPETENCIA'] = df['COMPETENCIA'].apply(norm_text)

cat_trib = {
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
df['TRIBUNAL'] = df['COD_TRIBUNAL'].map(cat_trib).fillna(df['TRIBUNAL'].apply(norm_text))

map_proc = {
    'C': 'CONTENCIOSA', 'P': 'MEDIDAS DE PROTECCION', 'F': 'VIOLENCIA INTRAFAMILIAR',
    'X': 'CUMPLIMIENTO', 'A': 'ADOPCION', 'V': 'VOLUNTARIA', 'I': 'IDENTIDAD DE GENERO',
    'Z': 'MENORES', 'R': 'TRANSACCION', 'T': 'TRANSACCION', 'S': 'PROTECCION SALUD MENTAL',
    'W': 'EXHORTOS', 'EXHORTO': 'EXHORTOS'
}
df['TIPO_PROCEDIMIENTO'] = df['TIPO_PROCEDIMIENTO'].apply(norm_text).replace(map_proc)
df['TIPO_AUDIENCIA'] = df['TIPO_AUDIENCIA'].apply(norm_text)

map_vid = {
    'SI': True, 'SÍ': True, '1.0': True, '1,0': True, '1': True, 'TRUE': True,
    'NO': False, '0.0': False, '0,0': False, '0': False, 'FALSE': False
}
df['VIDEOCONFERENCIA'] = df['VIDEOCONFERENCIA'].astype(str).str.strip().str.upper().map(map_vid).fillna(False).astype(bool)

def norm_hora(s):
    if pd.isna(s): return np.nan
    s_str = str(s).strip()
    if not s_str or s_str == 'nan': return np.nan
    if len(s_str) == 4 and s_str[1] == ':': s_str = '0' + s_str
    if len(s_str) == 5 and s_str[2] == ':': s_str = s_str + ':00'
    return s_str

df['HORA_INICIO'] = df['HORA_INICIO'].apply(norm_hora)
df['HORA_FIN'] = df['HORA_FIN'].apply(norm_hora)
df['ANO_AUDIENCIA'] = df['ANO_AUDIENCIA'].astype('Int64')
df['PLAZO_AGENDAMIENTO'] = df['PLAZO_AGENDAMIENTO'].astype('Int64')

df['RIT'] = df['RIT'].astype(str).str.strip().str.upper().str.replace('--', '-', regex=False)
df['ID_CAUSA_RIT'] = df['COD_TRIBUNAL'].astype(str) + '-' + df['RIT']
df.drop(columns=[c for c in ['RUC', 'ID_CAUSA', 'ID_AUDIENCIA', 'FECHA_FIRMA'] if c in df.columns], inplace=True)

# Imputaciones de 4.3
mask_hf = df['HORA_FIN'].isna()
if mask_hf.any():
    for idx in df[mask_hf].index:
        h_ini = str(df.loc[idx, 'HORA_INICIO'])
        parts = h_ini.split(':')
        hh = int(parts[0])
        mm = int(parts[1]) + 18
        if mm >= 60:
            hh += mm // 60
            mm = mm % 60
        df.loc[idx, 'HORA_FIN'] = f"{hh:02d}:{mm:02d}:00"

df['FECHA_PROGRAMACION'] = df['FECHA_PROGRAMACION'].fillna(df['FECHA_AUDIENCIA'])
df['PLAZO_AGENDAMIENTO'] = df['PLAZO_AGENDAMIENTO'].fillna(0)
df['PLAZO_AGENDAMIENTO'] = np.where(df['PLAZO_AGENDAMIENTO'] < 0, 0, df['PLAZO_AGENDAMIENTO'])
df['PLAZO_AGENDAMIENTO'] = df['PLAZO_AGENDAMIENTO'].astype('Int64')

# Aplicar Acción 1 acordada para fechas
mask_22 = df['FECHA_AUDIENCIA'] < df['FECHA_PROGRAMACION']
df.loc[mask_22, 'FECHA_PROGRAMACION'] = df.loc[mask_22, 'FECHA_AUDIENCIA']

df_clean = df

print("=== DIAGNÓSTICO DE HORAS Y DURACIÓN DE AUDIENCIAS ===")

# Convertir horas a minutos desde medianoche para cálculo exacto
def hora_a_minutos(h_str):
    if pd.isna(h_str): return np.nan
    try:
        parts = str(h_str).split(':')
        return int(parts[0]) * 60 + int(parts[1]) + (int(parts[2]) / 60 if len(parts) > 2 else 0)
    except:
        return np.nan

min_inicio = df_clean['HORA_INICIO'].apply(hora_a_minutos)
min_fin = df_clean['HORA_FIN'].apply(hora_a_minutos)
duracion_min = min_fin - min_inicio

print("\n--- 1. RANGOS Y ANOMALÍAS DE HORAS ---")
print(f"HORA_INICIO mín: {df_clean['HORA_INICIO'].min()} | máx: {df_clean['HORA_INICIO'].max()}")
print(f"HORA_FIN    mín: {df_clean['HORA_FIN'].min()} | máx: {df_clean['HORA_FIN'].max()}")

mask_negativa = duracion_min < 0
mask_cero = duracion_min == 0
mask_menor_5m = (duracion_min > 0) & (duracion_min < 5)
mask_mayor_8h = duracion_min > 480 # más de 8 horas
mask_mayor_12h = duracion_min > 720 # más de 12 horas

print(f"\nDuración < 0 minutos (HORA_FIN < HORA_INICIO): {mask_negativa.sum():,} casos")
print(f"Duración == 0 minutos (HORA_FIN == HORA_INICIO): {mask_cero.sum():,} casos ({mask_cero.mean()*100:.3f}%)")
print(f"Duración entre 1 y 4 minutos: {mask_menor_5m.sum():,} casos ({mask_menor_5m.mean()*100:.3f}%)")
print(f"Duración > 8 horas (480 min): {mask_mayor_8h.sum():,} casos ({mask_mayor_8h.mean()*100:.3f}%)")
print(f"Duración > 12 horas (720 min): {mask_mayor_12h.sum():,} casos")

print("\n--- 2. DETALLE DE CASOS NEGATIVOS (HORA_FIN < HORA_INICIO) ---")
if mask_negativa.sum() > 0:
    print(df_clean[mask_negativa][['ID_CAUSA_RIT', 'TRIBUNAL', 'TIPO_AUDIENCIA', 'HORA_INICIO', 'HORA_FIN']])
else:
    print("No hay casos con duración estrictamente negativa.")

print("\n--- 3. DETALLE DE CASOS CON DURACIÓN CERO (1.008 casos) ---")
sample_cero = df_clean[mask_cero][['ID_CAUSA_RIT', 'TRIBUNAL', 'TIPO_PROCEDIMIENTO', 'TIPO_AUDIENCIA', 'HORA_INICIO', 'HORA_FIN', 'ANO_AUDIENCIA']]
print("Distribución por tipo de audiencia en duración 0:")
print(sample_cero['TIPO_AUDIENCIA'].value_counts().head(5))
print("\nDistribución por año en duración 0:")
print(sample_cero['ANO_AUDIENCIA'].value_counts().sort_index())
print("\nMuestra de 5 casos duración 0:")
print(sample_cero.head(5))

print("\n--- 4. DETALLE DE CASOS CON DURACIÓN EXTREMA (> 8 HORAS) ---")
print(f"Total casos > 8 horas: {mask_mayor_8h.sum()}")
cols_ext = ['ID_CAUSA_RIT', 'TRIBUNAL', 'TIPO_PROCEDIMIENTO', 'TIPO_AUDIENCIA', 'HORA_INICIO', 'HORA_FIN', 'ANO_AUDIENCIA']
sample_ext = df_clean[mask_mayor_8h][cols_ext].copy()
sample_ext['DURACION_HORAS'] = (duracion_min[mask_mayor_8h] / 60).round(2)
print(sample_ext.sort_values('DURACION_HORAS', ascending=False).head(15))

print("\n--- 5. ESTADÍSTICAS DESCRIPTIVAS DE DURACIÓN (PARA DURACIÓN > 0) ---")
dur_valid = duracion_min[duracion_min > 0]
print(dur_valid.describe(percentiles=[0.01, 0.05, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99, 0.999]))

print("\nDuración mediana por Tipo de Audiencia (en minutos):")
df_temp = df_clean.copy()
df_temp['DURACION_MIN'] = duracion_min
print(df_temp[df_temp['DURACION_MIN'] > 0].groupby('TIPO_AUDIENCIA')['DURACION_MIN'].agg(['count', 'median', 'mean', lambda x: x.quantile(0.75), lambda x: x.quantile(0.95)]).rename(columns={'<lambda_0>': 'p75', '<lambda_1>': 'p95'}).sort_values('count', ascending=False))

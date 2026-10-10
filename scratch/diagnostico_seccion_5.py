import pandas as pd
import numpy as np
from pathlib import Path

# 1. Cargar y preparar df_clean tal como está en el pipeline actual
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

# Drop cols
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

df_clean = df

print("=== DATASET PREPARADO EXITOSAMENTE ===")
print(f"Dimensiones: {df_clean.shape}")
print(f"Nulos totales: {df_clean.isna().sum().sum()}")

# Asegurar datetimes
df_clean['FECHA_INGRESO'] = pd.to_datetime(df_clean['FECHA_INGRESO'])
df_clean['FECHA_PROGRAMACION'] = pd.to_datetime(df_clean['FECHA_PROGRAMACION'])
df_clean['FECHA_AUDIENCIA'] = pd.to_datetime(df_clean['FECHA_AUDIENCIA'])

print("\n--- 1. RANGOS TEMPORALES GENERALES ---")
print(f"FECHA_INGRESO:      min={df_clean['FECHA_INGRESO'].min()} | max={df_clean['FECHA_INGRESO'].max()}")
print(f"FECHA_PROGRAMACION: min={df_clean['FECHA_PROGRAMACION'].min()} | max={df_clean['FECHA_PROGRAMACION'].max()}")
print(f"FECHA_AUDIENCIA:    min={df_clean['FECHA_AUDIENCIA'].min()} | max={df_clean['FECHA_AUDIENCIA'].max()}")

print("\n--- 2. INCONSISTENCIAS CRONOLÓGICAS (VALORES IMPOSIBLES) ---")
# A. Audiencia anterior a Fecha Ingreso
mask_aud_ant_ing = df_clean['FECHA_AUDIENCIA'] < df_clean['FECHA_INGRESO']
print(f"FECHA_AUDIENCIA < FECHA_INGRESO: {mask_aud_ant_ing.sum():,} casos ({mask_aud_ant_ing.mean()*100:.4f}%)")

# B. Programación anterior a Fecha Ingreso
mask_prog_ant_ing = df_clean['FECHA_PROGRAMACION'] < df_clean['FECHA_INGRESO']
print(f"FECHA_PROGRAMACION < FECHA_INGRESO: {mask_prog_ant_ing.sum():,} casos ({mask_prog_ant_ing.mean()*100:.4f}%)")

# C. Audiencia anterior a Fecha Programacion
mask_aud_ant_prog = df_clean['FECHA_AUDIENCIA'] < df_clean['FECHA_PROGRAMACION']
print(f"FECHA_AUDIENCIA < FECHA_PROGRAMACION: {mask_aud_ant_prog.sum():,} casos ({mask_aud_ant_prog.mean()*100:.4f}%)")

# D. Concordancia de Año
mask_ano_diff = df_clean['FECHA_AUDIENCIA'].dt.year != df_clean['ANO_AUDIENCIA']
print(f"FECHA_AUDIENCIA.dt.year != ANO_AUDIENCIA: {mask_ano_diff.sum():,} casos")

mask_proc_diff = df_clean['FECHA_AUDIENCIA'].dt.year != df_clean['ANO_PROCESO']
print(f"FECHA_AUDIENCIA.dt.year != ANO_PROCESO: {mask_proc_diff.sum():,} casos")

# Analicemos en detalle los casos con FECHA_AUDIENCIA < FECHA_INGRESO
if mask_aud_ant_ing.sum() > 0:
    print("\nDetalle de casos FECHA_AUDIENCIA < FECHA_INGRESO:")
    sample_ai = df_clean[mask_aud_ant_ing][['RIT', 'ID_CAUSA_RIT', 'TRIBUNAL', 'TIPO_PROCEDIMIENTO', 'FECHA_INGRESO', 'FECHA_PROGRAMACION', 'FECHA_AUDIENCIA', 'PLAZO_AGENDAMIENTO']]
    print(sample_ai.head(10))
    diff_dias = (df_clean.loc[mask_aud_ant_ing, 'FECHA_AUDIENCIA'] - df_clean.loc[mask_aud_ant_ing, 'FECHA_INGRESO']).dt.days
    print(f"Diferencia en días (negativos): min={diff_dias.min()}, max={diff_dias.max()}, mediana={diff_dias.median()}")

# Analicemos en detalle los casos con FECHA_PROGRAMACION < FECHA_INGRESO
if mask_prog_ant_ing.sum() > 0:
    print("\nDetalle de casos FECHA_PROGRAMACION < FECHA_INGRESO:")
    diff_pi = (df_clean.loc[mask_prog_ant_ing, 'FECHA_PROGRAMACION'] - df_clean.loc[mask_prog_ant_ing, 'FECHA_INGRESO']).dt.days
    print(f"Conteo total: {mask_prog_ant_ing.sum()}")
    print(f"Diferencia en días: min={diff_pi.min()}, max={diff_pi.max()}, mediana={diff_pi.median()}")
    print(df_clean[mask_prog_ant_ing][['RIT', 'ID_CAUSA_RIT', 'TRIBUNAL', 'TIPO_PROCEDIMIENTO', 'FECHA_INGRESO', 'FECHA_PROGRAMACION', 'FECHA_AUDIENCIA', 'PLAZO_AGENDAMIENTO']].head(5))

print("\n--- 3. DISTRIBUCIÓN Y OUTLIERS DE PLAZO_AGENDAMIENTO ---")
plazo = df_clean['PLAZO_AGENDAMIENTO'].astype(float)
desc = plazo.describe(percentiles=[0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99, 0.999])
print(desc)

q1 = plazo.quantile(0.25)
q3 = plazo.quantile(0.75)
iqr = q3 - q1
upper_mild = q3 + 1.5 * iqr
upper_extreme = q3 + 3.0 * iqr
print(f"\nIQR: {iqr}")
print(f"Umbral Outlier Leve (Q3 + 1.5*IQR): {upper_mild:.1f} días")
print(f"Umbral Outlier Extremo (Q3 + 3*IQR): {upper_extreme:.1f} días")
print(f"Casos > {upper_mild:.1f} días: {(plazo > upper_mild).sum():,} ({(plazo > upper_mild).mean()*100:.2f}%)")
print(f"Casos > {upper_extreme:.1f} días: {(plazo > upper_extreme).sum():,} ({(plazo > upper_extreme).mean()*100:.2f}%)")
print(f"Casos > 100 días: {(plazo > 100).sum():,} ({(plazo > 100).mean()*100:.2f}%)")
print(f"Casos > 180 días (aprox 6 meses hábiles): {(plazo > 180).sum():,} ({(plazo > 180).mean()*100:.2f}%)")
print(f"Casos > 250 días: {(plazo > 250).sum():,} ({(plazo > 250).mean()*100:.4f}%)")

print("\nTop 10 plazos más altos:")
print(df_clean.sort_values('PLAZO_AGENDAMIENTO', ascending=False)[['ID_CAUSA_RIT', 'TRIBUNAL', 'TIPO_PROCEDIMIENTO', 'TIPO_AUDIENCIA', 'FECHA_PROGRAMACION', 'FECHA_AUDIENCIA', 'PLAZO_AGENDAMIENTO']].head(10))

print("\n--- 4. DURACIÓN DE TRAMITACIÓN PREVIA (FECHA_AUDIENCIA - FECHA_INGRESO) ---")
dias_tramitacion = (df_clean['FECHA_AUDIENCIA'] - df_clean['FECHA_INGRESO']).dt.days
print(dias_tramitacion.describe(percentiles=[0.01, 0.05, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99, 0.999]))
print(f"Casos tramitación < 0 días: {(dias_tramitacion < 0).sum()}")
print(f"Casos tramitación > 365 días (1 año): {(dias_tramitacion > 365).sum():,} ({(dias_tramitacion > 365).mean()*100:.2f}%)")
print(f"Casos tramitación > 1825 días (5 años): {(dias_tramitacion > 1825).sum():,} ({(dias_tramitacion > 1825).mean()*100:.2f}%)")
print(f"Casos tramitación > 3650 días (10 años): {(dias_tramitacion > 3650).sum():,} ({(dias_tramitacion > 3650).mean()*100:.2f}%)")

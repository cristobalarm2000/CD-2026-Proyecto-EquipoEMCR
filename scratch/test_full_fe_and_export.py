import pandas as pd
import numpy as np
from pathlib import Path
import time

start_t = time.time()
print("=== EJECUTANDO TEST DE INGENIERÍA DE CARACTERÍSTICAS Y EXPORTACIÓN ===")

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

# Imputaciones 4.3
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

# Seccion 5: Correccion de fechas imposibles
mask_22 = df['FECHA_AUDIENCIA'] < df['FECHA_PROGRAMACION']
df.loc[mask_22, 'FECHA_PROGRAMACION'] = df.loc[mask_22, 'FECHA_AUDIENCIA']

df_clean = df

# Datetime casts
df_clean['FECHA_INGRESO'] = pd.to_datetime(df_clean['FECHA_INGRESO'])
df_clean['FECHA_PROGRAMACION'] = pd.to_datetime(df_clean['FECHA_PROGRAMACION'])
df_clean['FECHA_AUDIENCIA'] = pd.to_datetime(df_clean['FECHA_AUDIENCIA'])

print(f"Base limpia lista en {time.time() - start_t:.2f} s. Filas: {len(df_clean):,}, Columnas: {df_clean.shape[1]}")

# =============================================================================
# SECCIÓN 6: INGENIERÍA DE CARACTERÍSTICAS (16 VARIABLES)
# =============================================================================
print("\n--- Calculando 16 Características Derivadas ---")

# 1. Calendario y Tiempo
dias_map = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
meses_map = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
             7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}

df_clean['DIA_SEMANA_AUDIENCIA'] = df_clean['FECHA_AUDIENCIA'].dt.dayofweek.map(dias_map)
df_clean['MES_AUDIENCIA'] = df_clean['FECHA_AUDIENCIA'].dt.month.map(meses_map)
df_clean['TRIMESTRE_AUDIENCIA'] = 'Q' + df_clean['FECHA_AUDIENCIA'].dt.quarter.astype(str)

def hora_to_min(h_str):
    p = str(h_str).split(':')
    return int(p[0]) * 60 + int(p[1]) + (int(p[2])/60 if len(p) > 2 else 0)

min_inicio = df_clean['HORA_INICIO'].apply(hora_to_min)
min_fin = df_clean['HORA_FIN'].apply(hora_to_min)
df_clean['DURACION_MINUTOS'] = (min_fin - min_inicio).round(1)

def categorizar_bloque(min_val):
    hh = min_val / 60
    if hh < 10: return 'Mañana Temprano (08:00-09:59)'
    elif hh < 12: return 'Mañana Central (10:00-11:59)'
    elif hh < 14: return 'Mediodía (12:00-13:59)'
    elif hh < 17: return 'Tarde (14:00-16:59)'
    else: return 'Vespertino / Turno (>= 17:00)'

df_clean['BLOQUE_HORARIO'] = min_inicio.apply(categorizar_bloque)

def categorizar_duracion(dur):
    if dur == 0: return '0. Frustrada / En el acto (0 min)'
    elif dur <= 15: return '1. Breve (1-15 min)'
    elif dur <= 30: return '2. Estándar (16-30 min)'
    elif dur <= 60: return '3. Extendida (31-60 min)'
    else: return '4. Compleja (> 60 min)'

df_clean['TRAMO_DURACION'] = df_clean['DURACION_MINUTOS'].apply(categorizar_duracion)
df_clean['FLG_AUDIENCIA_FRUSTRADA'] = df_clean['DURACION_MINUTOS'] == 0

# 2. Tiempos de Tramitación
df_clean['DIAS_TRAMITACION_PREVIA'] = (df_clean['FECHA_AUDIENCIA'] - df_clean['FECHA_INGRESO']).dt.days
df_clean['DIAS_DESPACHO_AGENDAMIENTO'] = (df_clean['FECHA_PROGRAMACION'] - df_clean['FECHA_INGRESO']).dt.days

def categorizar_plazo(dias):
    if dias == 0: return '1. Inmediato (0 días)'
    elif dias <= 15: return '2. Rápido (1-15 días)'
    elif dias <= 30: return '3. Estándar Legal (16-30 días)'
    elif dias <= 60: return '4. Demora Moderada (31-60 días)'
    elif dias <= 120: return '5. Congestión Severa (61-120 días)'
    else: return '6. Cuello de Botella Crítico (> 120 días)'

df_clean['TRAMO_AGENDAMIENTO'] = df_clean['PLAZO_AGENDAMIENTO'].apply(categorizar_plazo)

# 3. Secuencia y Litigiosidad
# Ordenar cronológicamente para secuencia exacta
df_clean = df_clean.sort_values(['ID_CAUSA_RIT', 'FECHA_AUDIENCIA', 'HORA_INICIO']).reset_index(drop=True)
df_clean['ORDEN_AUDIENCIA_CAUSA'] = (df_clean.groupby('ID_CAUSA_RIT').cumcount() + 1).astype('int16')
df_clean['TOTAL_AUDIENCIAS_CAUSA'] = df_clean.groupby('ID_CAUSA_RIT')['FECHA_AUDIENCIA'].transform('count').astype('int16')
df_clean['ES_AUDIENCIA_INICIAL'] = df_clean['ORDEN_AUDIENCIA_CAUSA'] == 1
df_clean['ES_CONTINUACION'] = df_clean['TIPO_AUDIENCIA'].str.contains('CONTINUACION', na=False)

# 4. Macro Materia y Época
def clasificar_macro_materia(proc):
    if proc == 'CONTENCIOSA': return 'Litigación Contenciosa'
    elif proc in ['VIOLENCIA INTRAFAMILIAR', 'MEDIDAS DE PROTECCION']: return 'Medidas Cautelares y Vulnerabilidad'
    elif proc == 'CUMPLIMIENTO': return 'Ejecución y Alimentos (Cumplimiento)'
    elif proc in ['VOLUNTARIA', 'ADOPCION', 'IDENTIDAD DE GENERO', 'TRANSACCION']: return 'Actos No Contenciosos y Voluntarios'
    else: return 'Otros Procedimientos'

df_clean['MACRO_MATERIA'] = df_clean['TIPO_PROCEDIMIENTO'].apply(clasificar_macro_materia)

def clasificar_epoca(fec):
    if fec < pd.Timestamp('2020-03-18'): return 'Pre-Pandemia (Presencial)'
    elif fec < pd.Timestamp('2022-10-01'): return 'Emergencia Sanitaria (Ley 21.226)'
    else: return 'Régimen Permanente Híbrido (Ley 21.394)'

df_clean['EPOCA_NORMATIVA'] = df_clean['FECHA_AUDIENCIA'].apply(clasificar_epoca)

print(f"Ingeniería completada en {time.time() - start_t:.2f} s.")
print(f"Dimensiones finales: {df_clean.shape[0]:,} filas x {df_clean.shape[1]} columnas")
print(f"Nulos totales: {df_clean.isna().sum().sum()}")

# =============================================================================
# SECCIÓN 7: EXPORTACIÓN Y PERSISTENCIA
# =============================================================================
out_dir = Path("data/processed")
out_dir.mkdir(parents=True, exist_ok=True)
out_file = out_dir / "audiencias_preparadas_modelo.parquet"

df_clean.to_parquet(out_file, index=False, compression='snappy')
file_size_mb = out_file.stat().st_size / (1024 * 1024)
print(f"\nArchivo guardado con éxito en: {out_file}")
print(f"Tamaño en disco: {file_size_mb:.2f} MB")
print("Lista de 36 columnas:")
for i, col in enumerate(df_clean.columns, 1):
    print(f"{i:2d}. {col:30s} ({df_clean[col].dtype})")

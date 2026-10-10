import pandas as pd
import numpy as np
from pathlib import Path

# Cargar y preparar df_clean tal como está en el pipeline actual hasta Seccion 5
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

print("=== PROBANDO CARACTERÍSTICAS PROPUESTAS ===")

# 1. Temporales / Calendario
dias_map = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
meses_map = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
             7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}

dia_semana = df_clean['FECHA_AUDIENCIA'].dt.dayofweek.map(dias_map)
mes = df_clean['FECHA_AUDIENCIA'].dt.month.map(meses_map)
trimestre = 'Q' + df_clean['FECHA_AUDIENCIA'].dt.quarter.astype(str)

print("Distribución Día Semana:")
print(dia_semana.value_counts())

# Franja Horaria
def hora_to_min(h_str):
    p = str(h_str).split(':')
    return int(p[0]) * 60 + int(p[1]) + (int(p[2])/60 if len(p) > 2 else 0)

min_inicio = df_clean['HORA_INICIO'].apply(hora_to_min)
min_fin = df_clean['HORA_FIN'].apply(hora_to_min)
duracion_min = (min_fin - min_inicio).round(1)

def categorizar_bloque(min_val):
    hh = min_val / 60
    if hh < 10: return 'Mañana Temprano (08:00-09:59)'
    elif hh < 12: return 'Mañana Central (10:00-11:59)'
    elif hh < 14: return 'Mediodía (12:00-13:59)'
    elif hh < 17: return 'Tarde (14:00-16:59)'
    else: return 'Vespertino / Turno (>= 17:00)'

bloque_horario = min_inicio.apply(categorizar_bloque)
print("\nDistribución Bloque Horario:")
print(bloque_horario.value_counts())

# 2. Tiempos de Tramitacion y Agendamiento
dias_tramitacion = (df_clean['FECHA_AUDIENCIA'] - df_clean['FECHA_INGRESO']).dt.days

def categorizar_plazo(dias):
    if dias == 0: return '1. Inmediato (0 días)'
    elif dias <= 15: return '2. Rápido (1-15 días)'
    elif dias <= 30: return '3. Estándar Legal (16-30 días)'
    elif dias <= 60: return '4. Demora Moderada (31-60 días)'
    elif dias <= 120: return '5. Congestión Severa (61-120 días)'
    else: return '6. Cuello de Botella Crítico (> 120 días)'

tramo_plazo = df_clean['PLAZO_AGENDAMIENTO'].apply(categorizar_plazo)
print("\nDistribución Tramo Agendamiento:")
print(tramo_plazo.value_counts().sort_index())

# 3. Secuencia a nivel de causa
df_sorted = df_clean.sort_values(['ID_CAUSA_RIT', 'FECHA_AUDIENCIA', 'HORA_INICIO'])
orden_aud = df_sorted.groupby('ID_CAUSA_RIT').cumcount() + 1
total_aud_causa = df_sorted.groupby('ID_CAUSA_RIT')['FECHA_AUDIENCIA'].transform('count')

print("\nDistribución Orden de Audiencia en la Causa:")
print(orden_aud.value_counts().head(6))

# 4. Macro Materia
def clasificar_macro_materia(proc):
    if proc == 'CONTENCIOSA': return 'Litigación Contenciosa'
    elif proc in ['VIOLENCIA INTRAFAMILIAR', 'MEDIDAS DE PROTECCION']: return 'Medidas Cautelares y Vulnerabilidad'
    elif proc == 'CUMPLIMIENTO': return 'Ejecución y Alimentos (Cumplimiento)'
    elif proc in ['VOLUNTARIA', 'ADOPCION', 'IDENTIDAD DE GENERO', 'TRANSACCION']: return 'Actos No Contenciosos y Voluntarios'
    else: return 'Otros Procedimientos'

macro_materia = df_clean['TIPO_PROCEDIMIENTO'].apply(clasificar_macro_materia)
print("\nDistribución Macro Materia:")
print(macro_materia.value_counts())

# 5. Época Normativa
def clasificar_epoca(fec):
    if fec < pd.Timestamp('2020-03-18'): return 'Pre-Pandemia (Presencial)'
    elif fec < pd.Timestamp('2022-10-01'): return 'Emergencia Sanitaria (Ley 21.226)'
    else: return 'Régimen Permanente Híbrido (Ley 21.394)'

epoca_normativa = df_clean['FECHA_AUDIENCIA'].apply(clasificar_epoca)
print("\nDistribución Época Normativa:")
print(epoca_normativa.value_counts())

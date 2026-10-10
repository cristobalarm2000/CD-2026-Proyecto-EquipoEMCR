import time
import unicodedata
import re
from pathlib import Path
import numpy as np
import pandas as pd

start_t = time.time()
print("=== EJECUTANDO PIPELINE ETL NACIONAL (FAMILIA - 17 CORTES) ===")

base_dir = Path("C:/Users/frero/CD-2026-Proyecto-EquipoEMCR")
parquet_raw = base_dir / "data/raw/parquet/audiencias_realizadas_competencia_detalle.parquet"

print("1. Cargando datos crudos Parquet...")
t0 = time.time()
df = pd.read_parquet(parquet_raw)
print(f"   Cargado en {time.time() - t0:.2f} s. Filas: {len(df):,}, Columnas: {df.shape[1]}")

print("2. Tratamiento y cruce lote 2023 (Fuente Oficial PJUD)...")
t0 = time.time()
path_csv = base_dir / "data/raw/excel_pjud/audiencias_realizadas_2023.csv"
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
del df_csv
print(f"   Cruce 2023 finalizado en {time.time() - t0:.2f} s. Filas 2023 cruzadas: {is_23.sum():,}")

print("3. Sanitización categórica y catálogos canónicos nacionales...")
t0 = time.time()
def norm_text(text):
    if pd.isna(text): return np.nan
    s = str(text).strip().upper()
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

# Catálogos oficiales PJUD
cortes_csv = base_dir / "src/Api_Caller/cortes.csv"
df_c = pd.read_csv(cortes_csv)
cat_cortes = dict(zip(df_c['corte'], df_c['glosa_corte'].apply(norm_text)))

trib_csv = base_dir / "src/Api_Caller/tribunales.csv"
df_t = pd.read_csv(trib_csv)
df_t_uniq = df_t[['tribunal', 'glosa_tribunal']].drop_duplicates(subset=['tribunal'])
cat_tribunales = dict(zip(df_t_uniq['tribunal'], df_t_uniq['glosa_tribunal'].apply(norm_text)))

df['CORTE'] = df['COD_CORTE'].map(cat_cortes).fillna(df['CORTE'].apply(norm_text))
df['TRIBUNAL'] = df['COD_TRIBUNAL'].map(cat_tribunales).fillna(df['TRIBUNAL'].apply(norm_text))
df['COMPETENCIA'] = 'FAMILIA'

map_proc = {
    'C': 'CONTENCIOSA', 'P': 'MEDIDAS DE PROTECCION', 'F': 'VIOLENCIA INTRAFAMILIAR',
    'X': 'CUMPLIMIENTO', 'A': 'ADOPCION', 'V': 'VOLUNTARIA', 'I': 'IDENTIDAD DE GENERO',
    'Z': 'MENORES', 'R': 'TRANSACCION', 'T': 'TRANSACCION', 'S': 'PROTECCION SALUD MENTAL',
    'W': 'EXHORTOS', 'EXHORTO': 'EXHORTOS'
}
df['TIPO_PROCEDIMIENTO'] = df['TIPO_PROCEDIMIENTO'].apply(norm_text).replace(map_proc)
df['TIPO_AUDIENCIA'] = df['TIPO_AUDIENCIA'].apply(norm_text)

# Modalidad Videoconferencia
map_vid = {
    'SI': True, 'SÍ': True, '1.0': True, '1,0': True, '1': True, 'TRUE': True,
    'NO': False, '0.0': False, '0,0': False, '0': False, 'FALSE': False
}
df['VIDEOCONFERENCIA'] = df['VIDEOCONFERENCIA'].astype(str).str.strip().str.upper().map(map_vid).fillna(False).astype(bool)

# Horarios
def norm_hora(s):
    if pd.isna(s): return np.nan
    s_str = str(s).strip()
    if not s_str or s_str.upper() in ['NAN', 'NONE', 'NULL', '[NULL]', 'NO REGISTRA', 'NO APLICA', 'S/I']: return np.nan
    s_str = s_str.replace('.', ':')
    if len(s_str) == 4 and s_str[1] == ':': s_str = '0' + s_str
    if len(s_str) == 5 and s_str[2] == ':': s_str = s_str + ':00'
    parts = s_str.split(':')
    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
        hh = int(parts[0])
        mm = int(parts[1])
        ss = int(parts[2]) if (len(parts) > 2 and parts[2].isdigit()) else 0
        return f"{hh:02d}:{mm:02d}:{ss:02d}"
    return np.nan

df['HORA_INICIO'] = df['HORA_INICIO'].apply(norm_hora)
df['HORA_FIN'] = df['HORA_FIN'].apply(norm_hora)

df['ANO_AUDIENCIA'] = df['ANO_AUDIENCIA'].astype('Int64')
df['PLAZO_AGENDAMIENTO'] = df['PLAZO_AGENDAMIENTO'].astype('Int64')
df['RIT'] = df['RIT'].astype(str).str.strip().str.upper().str.replace('--', '-', regex=False)
df['ID_CAUSA_RIT'] = df['COD_TRIBUNAL'].astype(str) + '-' + df['RIT']

# Depuración y anonimización
cols_drop = [c for c in ['RUC', 'ID_CAUSA', 'ID_AUDIENCIA', 'FECHA_FIRMA'] if c in df.columns]
df.drop(columns=cols_drop, inplace=True)
print(f"   Sanitización completada en {time.time() - t0:.2f} s.")

print("4. Imputación de faltantes y corrección de incoherencias...")
t0 = time.time()
# Imputación HORA_FIN
mask_hf = df['HORA_FIN'].isna()
if mask_hf.any():
    print(f"   Imputando {mask_hf.sum()} registros con HORA_FIN ausente...")
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

# Coherencia de fechas
mask_fechas = df['FECHA_AUDIENCIA'] < df['FECHA_PROGRAMACION']
print(f"   Casos donde FECHA_AUDIENCIA < FECHA_PROGRAMACION ajustados: {mask_fechas.sum():,}")
df.loc[mask_fechas, 'FECHA_PROGRAMACION'] = df.loc[mask_fechas, 'FECHA_AUDIENCIA']

df['FECHA_INGRESO'] = pd.to_datetime(df['FECHA_INGRESO'])
df['FECHA_PROGRAMACION'] = pd.to_datetime(df['FECHA_PROGRAMACION'])
df['FECHA_AUDIENCIA'] = pd.to_datetime(df['FECHA_AUDIENCIA'])
print(f"   Imputaciones completadas en {time.time() - t0:.2f} s.")

print("5. Ingeniería de características (16 variables analíticas)...")
t0 = time.time()
dias_map = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
meses_map = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
             7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}

df['DIA_SEMANA_AUDIENCIA'] = df['FECHA_AUDIENCIA'].dt.dayofweek.map(dias_map)
df['MES_AUDIENCIA'] = df['FECHA_AUDIENCIA'].dt.month.map(meses_map)
df['TRIMESTRE_AUDIENCIA'] = 'Q' + df['FECHA_AUDIENCIA'].dt.quarter.astype(str)

def hora_to_min(h_str):
    if pd.isna(h_str): return np.nan
    p = str(h_str).split(':')
    try:
        hh = int(p[0])
        mm = int(p[1]) if len(p) > 1 else 0
        ss = float(p[2]) if len(p) > 2 else 0.0
        return hh * 60 + mm + ss / 60.0
    except Exception:
        return np.nan

min_inicio = df['HORA_INICIO'].apply(hora_to_min)
min_fin = df['HORA_FIN'].apply(hora_to_min)
df['DURACION_MINUTOS'] = (min_fin - min_inicio).round(1)

def categorizar_bloque(min_val):
    hh = min_val / 60
    if hh < 10: return 'Mañana Temprano (08:00-09:59)'
    elif hh < 12: return 'Mañana Central (10:00-11:59)'
    elif hh < 14: return 'Mediodía (12:00-13:59)'
    elif hh < 17: return 'Tarde (14:00-16:59)'
    else: return 'Vespertino / Turno (>= 17:00)'

df['BLOQUE_HORARIO'] = min_inicio.apply(categorizar_bloque)

def categorizar_duracion(dur):
    if dur == 0: return '0. Frustrada / En el acto (0 min)'
    elif dur <= 15: return '1. Breve (1-15 min)'
    elif dur <= 30: return '2. Estándar (16-30 min)'
    elif dur <= 60: return '3. Extendida (31-60 min)'
    else: return '4. Compleja (> 60 min)'

df['TRAMO_DURACION'] = df['DURACION_MINUTOS'].apply(categorizar_duracion)
df['FLG_AUDIENCIA_FRUSTRADA'] = df['DURACION_MINUTOS'] == 0

# Tiempos de tramitación
df['DIAS_TRAMITACION_PREVIA'] = (df['FECHA_AUDIENCIA'] - df['FECHA_INGRESO']).dt.days
df['DIAS_DESPACHO_AGENDAMIENTO'] = (df['FECHA_PROGRAMACION'] - df['FECHA_INGRESO']).dt.days

def categorizar_plazo(dias):
    if dias == 0: return '1. Inmediato (0 días)'
    elif dias <= 15: return '2. Rápido (1-15 días)'
    elif dias <= 30: return '3. Estándar Legal (16-30 días)'
    elif dias <= 60: return '4. Demora Moderada (31-60 días)'
    elif dias <= 120: return '5. Congestión Severa (61-120 días)'
    else: return '6. Cuello de Botella Crítico (> 120 días)'

df['TRAMO_AGENDAMIENTO'] = df['PLAZO_AGENDAMIENTO'].apply(categorizar_plazo)

# Secuencia y litigiosidad
print("   Ordenando y calculando secuencias procesales...")
df = df.sort_values(['ID_CAUSA_RIT', 'FECHA_AUDIENCIA', 'HORA_INICIO']).reset_index(drop=True)
df['ORDEN_AUDIENCIA_CAUSA'] = (df.groupby('ID_CAUSA_RIT').cumcount() + 1).astype('int16')
df['TOTAL_AUDIENCIAS_CAUSA'] = df.groupby('ID_CAUSA_RIT')['FECHA_AUDIENCIA'].transform('count').astype('int16')
df['ES_AUDIENCIA_INICIAL'] = df['ORDEN_AUDIENCIA_CAUSA'] == 1
df['ES_CONTINUACION'] = df['TIPO_AUDIENCIA'].str.contains('CONTINUACION', na=False)

# Macro Materia y Época
def clasificar_macro_materia(proc):
    if proc == 'CONTENCIOSA': return 'Litigación Contenciosa'
    elif proc in ['VIOLENCIA INTRAFAMILIAR', 'MEDIDAS DE PROTECCION']: return 'Medidas Cautelares y Vulnerabilidad'
    elif proc == 'CUMPLIMIENTO': return 'Ejecución y Alimentos (Cumplimiento)'
    elif proc in ['VOLUNTARIA', 'ADOPCION', 'IDENTIDAD DE GENERO', 'TRANSACCION']: return 'Actos No Contenciosos y Voluntarios'
    else: return 'Otros Procedimientos'

df['MACRO_MATERIA'] = df['TIPO_PROCEDIMIENTO'].apply(clasificar_macro_materia)

def clasificar_epoca(fec):
    if fec < pd.Timestamp('2020-03-18'): return 'Pre-Pandemia (Presencial)'
    elif fec < pd.Timestamp('2022-10-01'): return 'Emergencia Sanitaria (Ley 21.226)'
    else: return 'Régimen Permanente Híbrido (Ley 21.394)'

df['EPOCA_NORMATIVA'] = df['FECHA_AUDIENCIA'].apply(clasificar_epoca)
print(f"   Ingeniería de características completada en {time.time() - t0:.2f} s.")

print("6. Exportando a Apache Parquet...")
t0 = time.time()
out_dir = base_dir / "data/processed"
out_dir.mkdir(parents=True, exist_ok=True)
out_file = out_dir / "audiencias_preparadas_modelo.parquet"
df.to_parquet(out_file, index=False, compression='snappy')
file_size_mb = out_file.stat().st_size / (1024 * 1024)
print(f"   Guardado exitoso en {time.time() - t0:.2f} s. Tamaño: {file_size_mb:.2f} MB")

print("\n=== RESUMEN EJECUTIVO DEL DATASET PREPARADO NACIONAL ===")
print(f"Filas totales: {len(df):,}")
print(f"Columnas totales: {df.shape[1]}")
print(f"Nulos totales: {df.isna().sum().sum()}")
print(f"Cortes únicas ({df['CORTE'].nunique()}): {sorted(df['CORTE'].unique())}")
print(f"Tribunales únicos: {df['TRIBUNAL'].nunique()}")
print(f"Tiempo total de ejecución: {time.time() - start_t:.2f} segundos.")

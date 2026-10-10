import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import time

start_t = time.time()
path = Path("data/processed/audiencias_preparadas_modelo.parquet")
df = pd.read_parquet(path)
print(f"Loaded parquet in {time.time() - start_t:.2f} s: {df.shape}")

# Test Tab 1 aggregations: SLAs by Tribunal
benchmark_trib = df.groupby('TRIBUNAL')['PLAZO_AGENDAMIENTO'].agg(['median', 'count', lambda x: x.quantile(0.9)]).rename(columns={'<lambda_0>': 'p90'}).reset_index()
benchmark_trib = benchmark_trib.sort_values('median', ascending=False)
print("Benchmark Tribunales:")
print(benchmark_trib.head(5))

# Test Tab 2 aggregations: Litigiosidad
df_causes = df.groupby('ID_CAUSA_RIT')['TOTAL_AUDIENCIAS_CAUSA'].first().value_counts().sort_index()
print("Distribución causas por total audiencias:")
print(df_causes.head(5))

# Test Tab 3: Heatmap Dia x Bloque
matriz_sala = pd.crosstab(df['DIA_SEMANA_AUDIENCIA'], df['BLOQUE_HORARIO'])
print("Matriz Dia x Bloque:")
print(matriz_sala)

# Test Tab 4: Telematica por Anio y Epoca
telematica_epoca = df.groupby(['ANO_AUDIENCIA', 'VIDEOCONFERENCIA']).size().unstack(fill_value=0)
telematica_epoca['pct_telematica'] = (telematica_epoca[True] / (telematica_epoca[True] + telematica_epoca[False]) * 100).round(1)
print("Telemática por año:")
print(telematica_epoca['pct_telematica'])

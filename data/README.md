# data/

Los datos **no se versionan** (ver `.gitignore`). Se regeneran con:

```bash
python src/descargar_pjud.py   --competencia familia --anios 2022 2023 2024
python src/descomprimir_zips.py --entrada data/raw/familia
```

- `raw/familia/` — ZIP `-CSV` de PJUD + carpeta `csv/` con los CSV extraídos
  (`Ingresos-2024-Rol.csv`, `Ingresos-2024-Materia.csv`, `Terminos-…`,
  `Duracion-…`, `Inventario-…`, `Audiencias-…-Realizadas.csv`).
- `processed/` — panel `tribunal × mes` y tablas filtradas a `COD. CORTE = 30`,
  en Parquet.

Fuente: datos abiertos del Poder Judicial de Chile (`numeros.pjud.cl`).
Detalle de esquemas y endpoints en `../docs/API_PJUD.md`.

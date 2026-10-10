import time
import nbformat
from nbclient import NotebookClient
from pathlib import Path

start = time.time()
nb_path = Path("C:/Users/frero/CD-2026-Proyecto-EquipoEMCR/notebooks/01 ETL_audienciasparquet.ipynb")
print(f"Iniciando ejecución completa de: {nb_path.name}")

nb = nbformat.read(nb_path, as_version=4)
client = NotebookClient(nb, timeout=600, kernel_name="python3")

try:
    client.execute(cwd="C:/Users/frero/CD-2026-Proyecto-EquipoEMCR/notebooks")
    nbformat.write(nb, nb_path)
    print(f"Ejecución del cuaderno finalizada exitosamente en {time.time() - start:.2f} s.")
except Exception as e:
    print(f"Error durante la ejecución del cuaderno: {e}")
    raise

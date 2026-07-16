"""
Carga config.json (UN SOLO archivo, idéntico en Norte y Sur) y extrae
automáticamente la configuración del nodo cuyo nombre coincide con el
hostname real de esta máquina.

Estructura esperada:
{
  "nodos": {
    "XANDER27HALF": { "sede_id": 1, "sede_nombre": "Sede Norte", ... },
    "DXCAM":        { "sede_id": 2, "sede_nombre": "Sede Sur", ... }
  }
}
"""

import json
import os
import socket
import sys


class ConfigError(Exception):
    """Error de configuración: archivo faltante, incompleto o nodo no encontrado."""
    pass


CAMPOS_REQUERIDOS_NODO = [
    "sede_id",
    "sede_nombre",
    "base_local",
    "usuario_local",
    "clave_local",
    "instancia_remota",
    "base_remota",
]


def _ruta_config():
    # Busca config.json junto al ejecutable / script principal,
    # no en el directorio de trabajo actual (importante si se abre con doble clic).
    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.join(base_dir, "config.json")


def cargar_config():
    ruta = _ruta_config()

    if not os.path.exists(ruta):
        raise ConfigError(f"No se encontró config.json en:\n{ruta}")

    with open(ruta, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "nodos" not in data or not isinstance(data["nodos"], dict):
        raise ConfigError("config.json debe tener una clave raíz 'nodos' con un objeto de nodos.")

    # Normalizamos a mayúsculas para que no falle por diferencias de capitalización
    nodos = {k.strip().upper(): v for k, v in data["nodos"].items()}
    hostname_actual = socket.gethostname().strip().upper()

    if hostname_actual not in nodos:
        raise ConfigError(
            f"Esta máquina se llama '{hostname_actual}', pero config.json no tiene "
            f"ninguna entrada dentro de 'nodos' para ese hostname.\n\n"
            f"Nodos configurados: {', '.join(nodos.keys())}\n\n"
            f"Revisa que el nombre de esta PC coincida exactamente con la clave del JSON."
        )

    nodo = nodos[hostname_actual]

    faltantes = [c for c in CAMPOS_REQUERIDOS_NODO if c not in nodo]
    if faltantes:
        raise ConfigError(
            f"La configuración del nodo '{hostname_actual}' está incompleta. "
            f"Faltan campos: {', '.join(faltantes)}"
        )

    config = dict(nodo)
    config["instancia_local"] = hostname_actual
    config["hostname_actual"] = hostname_actual
    return config

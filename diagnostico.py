"""
Diagnóstico de conexión — corre esto por consola, SIN la GUI, para
aislar si el problema es de red/SQL Server o de la aplicación.

Uso:
    python diagnostico.py
"""

import json
import socket
import sys
import time


def cargar_config_cruda():
    with open("config.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    hostname = socket.gethostname().strip().upper()
    nodos = {k.strip().upper(): v for k, v in data["nodos"].items()}
    if hostname not in nodos:
        print(f"❌ Esta máquina ({hostname}) no aparece en config.json -> nodos")
        sys.exit(1)
    config = dict(nodos[hostname])
    config["instancia_local"] = hostname
    return config


def main():
    print("=" * 60)
    print("DIAGNÓSTICO DE CONEXIÓN — MoodCoffee POS")
    print("=" * 60)

    config = cargar_config_cruda()
    print(f"Hostname detectado : {socket.gethostname()}")
    print(f"instancia_local     : {config['instancia_local']}")
    print(f"base_local          : {config['base_local']}")
    print(f"usuario_local       : {config['usuario_local']}")
    print()

    # --- Paso 1: resolución DNS/hostname básica ---
    print("[1/4] Probando resolver el nombre del servidor...")
    try:
        ip = socket.gethostbyname(config["instancia_local"])
        print(f"      OK -> {config['instancia_local']} resuelve a {ip}")
    except socket.gaierror as e:
        print(f"      ❌ No se pudo resolver el hostname: {e}")
        print("      Esto normalmente es un problema de red local, no de SQL Server.")

    # --- Paso 2: pyodbc disponible ---
    print("[2/4] Verificando que pyodbc esté instalado...")
    try:
        import pyodbc
        print(f"      OK -> pyodbc {pyodbc.version}")
        print(f"      Drivers ODBC instalados: {pyodbc.drivers()}")
    except ImportError:
        print("      ❌ pyodbc no está instalado. Corre: pip install pyodbc")
        sys.exit(1)

    # --- Paso 3: intento de conexión SIN forzar protocolo (como hoy) ---
    print("[3/4] Probando conexión tal como la usa la app hoy (sin forzar protocolo)...")
    conn_str_normal = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={config['instancia_local']};"
        f"DATABASE={config['base_local']};"
        f"UID={config['usuario_local']};"
        f"PWD={config['clave_local']};"
    )
    _probar(conn_str_normal, "Conexión normal (Named Pipes o lo que el driver elija)")

    # --- Paso 4: intento forzando TCP explícito con puerto 1433 ---
    print("[4/4] Probando conexión forzando TCP explícito en el puerto 1433...")
    conn_str_tcp = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER=tcp:{config['instancia_local']},1433;"
        f"DATABASE={config['base_local']};"
        f"UID={config['usuario_local']};"
        f"PWD={config['clave_local']};"
    )
    _probar(conn_str_tcp, "Conexión forzando TCP:1433")

    print()
    print("=" * 60)
    print("Si el paso [4/4] (TCP forzado) funcionó pero el [3/4] falló,")
    print("el arreglo es cambiar la app para usar 'tcp:' + puerto en el")
    print("connection string (ver instrucciones que te doy en el chat).")
    print("=" * 60)


def _probar(conn_str, etiqueta):
    import pyodbc
    inicio = time.time()
    try:
        conn = pyodbc.connect(conn_str, timeout=5)
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        conn.close()
        duracion = time.time() - inicio
        print(f"      ✅ {etiqueta}: EXITOSA ({duracion:.2f}s)")
        print(f"         {version.splitlines()[0]}")
    except pyodbc.Error as e:
        duracion = time.time() - inicio
        print(f"      ❌ {etiqueta}: FALLÓ ({duracion:.2f}s)")
        print(f"         {e}")


if __name__ == "__main__":
    main()
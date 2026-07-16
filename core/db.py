"""
Capa de acceso a datos. IMPORTANTE:
Python SOLO se conecta a la instancia LOCAL del nodo (instancia_local /
base_local del config.json), usando autenticación SQL (usuario_local /
clave_local) — la misma identidad que ya confirmaste que funciona en
SSMS con 'sa'. El acceso a la sede contraria queda resuelto a nivel de
SQL Server mediante el Linked Server + las vistas particionadas
(v_Consumo_Operativo, v_Detalle_Consumo). Python nunca abre una
conexión pyodbc directa hacia el servidor remoto.
"""

import pyodbc

DRIVER = "{ODBC Driver 17 for SQL Server}"


def get_local_connection(config, timeout=5):
    conn_str = (
        f"DRIVER={DRIVER};"
        f"SERVER={config['instancia_local']};"
        f"DATABASE={config['base_local']};"
        f"UID={config['usuario_local']};"
        f"PWD={config['clave_local']};"
    )
    return pyodbc.connect(conn_str, timeout=timeout)


def probar_conexion(config):
    """Usado al arrancar la app para avisar temprano si SQL Server no responde."""
    try:
        conn = get_local_connection(config)
        conn.close()
        return True, None
    except pyodbc.Error as e:
        return False, str(e)


def ejecutar_query(config, query, params=None):
    """Ejecuta un SELECT y devuelve (columnas, filas) listas para pintar en UI."""
    conn = get_local_connection(config)
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or [])
        columnas = [col[0] for col in cursor.description]
        filas = [list(f) for f in cursor.fetchall()]
        return columnas, filas
    finally:
        conn.close()


def obtener_stats_inicio(config):
    """
    Estadísticas de la pantalla de Inicio, calculadas SIEMPRE sobre la sede
    local (id_sede = config['sede_id']):

    - consumos_registrados / total_vendido: se leen de las vistas
      particionadas v_Consumo_Operativo y v_Detalle_Consumo, filtradas por
      id_sede. Se usa SUM(subtotal) de v_Detalle_Consumo en vez de tocar
      Consumo_Financiero, porque esa tabla solo vive físicamente en Norte
      y no queremos forzar un cruce remoto extra solo para un contador.
    - clientes_registrados: tabla física Cliente_Operativo (replicación
      bidireccional, existe local en ambos nodos).
    - productos_menu: tabla física Producto (replicación unidireccional
      desde Norte, ya está local en ambos nodos).
    """
    sede_id = config["sede_id"]
    conn = get_local_connection(config)
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM v_Consumo_Operativo WHERE id_sede = ?", sede_id)
        consumos = cursor.fetchone()[0]

        cursor.execute("SELECT ISNULL(SUM(subtotal), 0) FROM v_Detalle_Consumo WHERE id_sede = ?", sede_id)
        total = float(cursor.fetchone()[0])

        cursor.execute("SELECT COUNT(*) FROM Cliente_Operativo")
        clientes = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Producto")
        productos = cursor.fetchone()[0]

        return {
            "consumos_registrados": consumos,
            "total_vendido": total,
            "clientes_registrados": clientes,
            "productos_menu": productos,
        }
    finally:
        conn.close()

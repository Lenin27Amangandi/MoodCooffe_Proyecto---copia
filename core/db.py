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


def listar_clientes(config):
    """
    Norte: join local Cliente_Operativo + Cliente_Datos (ambas existen ahí).
    Sur: solo Cliente_Operativo local — Cliente_Datos no existe físicamente
    en Sur, por diseño de la fragmentación vertical.
    """
    conn = get_local_connection(config)
    try:
        cursor = conn.cursor()
        if config["sede_id"] == 1:
            query = """
                SELECT co.id_cliente AS ID, co.nombre AS Nombre, co.apellido AS Apellido,
                       cd.cedula AS Cedula, cd.telefono AS Telefono, cd.correo AS Correo
                FROM Cliente_Operativo co
                LEFT JOIN Cliente_Datos cd ON cd.id_cliente = co.id_cliente
                ORDER BY co.id_cliente
            """
        else:
            query = """
                SELECT id_cliente AS ID, nombre AS Nombre, apellido AS Apellido
                FROM Cliente_Operativo
                ORDER BY id_cliente
            """
        cursor.execute(query)
        columnas = [c[0] for c in cursor.description]
        filas = [list(f) for f in cursor.fetchall()]
        return columnas, filas
    finally:
        conn.close()


def insertar_cliente(config, nombre, apellido, cedula, telefono, correo):
    """
    Inserta respetando la fragmentación vertical del Cliente:
      - Cliente_Operativo (nombre, apellido) -> SIEMPRE local (bidireccional).
      - Cliente_Datos (cedula, telefono, correo) -> físicamente solo en
        Norte. Si el nodo actual ES Norte, se inserta local. Si es Sur,
        se inserta remoto vía Linked Server con nomenclatura de 4 partes.

    NOTA (limitación conocida para la documentación del proyecto): el
    próximo id_cliente se calcula como MAX(id_cliente)+1 sobre la copia
    LOCAL de Cliente_Operativo. Si Norte y Sur insertan un cliente nuevo
    de forma simultánea antes de que la replicación bidireccional
    sincronice, podrían generar el mismo id_cliente y chocar al fusionarse.
    Para un entorno productivo real se recomendaría particionar rangos de
    ID por sede (ej. Norte=impares, Sur=pares) o usar IDENTITY con manejo
    automático de rangos de Merge Replication.
    """
    conn = get_local_connection(config)
    try:
        cursor = conn.cursor()
        cursor.execute("SET XACT_ABORT ON;")

        cursor.execute("SELECT ISNULL(MAX(id_cliente), 0) FROM Cliente_Operativo")
        siguiente_id = cursor.fetchone()[0] + 1

        cursor.execute(
            "INSERT INTO Cliente_Operativo (id_cliente, nombre, apellido) VALUES (?, ?, ?)",
            siguiente_id, nombre, apellido
        )

        if config["sede_id"] == 1:
            cursor.execute(
                "INSERT INTO Cliente_Datos (id_cliente, cedula, telefono, correo) VALUES (?, ?, ?, ?)",
                siguiente_id, cedula, telefono, correo
            )
        else:
            instancia_remota = config["instancia_remota"]
            base_remota = config["base_remota"]
            query_remota = (
                f"INSERT INTO [{instancia_remota}].[{base_remota}].dbo.Cliente_Datos "
                f"(id_cliente, cedula, telefono, correo) VALUES (?, ?, ?, ?)"
            )
            cursor.execute(query_remota, siguiente_id, cedula, telefono, correo)

        conn.commit()
        return siguiente_id
    except Exception:
        conn.rollback()
        raise
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

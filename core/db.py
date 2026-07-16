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


def insertar_fila(config, tabla, columnas, valores):
    """
    Inserta una fila genérica. 'tabla' y 'columnas' SIEMPRE vienen de
    constantes internas (core/catalogos_meta.py), nunca de texto libre
    del usuario -- por eso el f-string de nombres es seguro. Los VALORES
    sí van parametrizados con '?' para evitar inyección SQL.
    """
    conn = get_local_connection(config)
    try:
        cursor = conn.cursor()
        cols_sql = ", ".join(columnas)
        placeholders = ", ".join(["?"] * len(valores))
        cursor.execute(f"INSERT INTO {tabla} ({cols_sql}) VALUES ({placeholders})", *valores)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def actualizar_fila(config, tabla, pk_columna, pk_valor, columnas, valores):
    conn = get_local_connection(config)
    try:
        cursor = conn.cursor()
        set_sql = ", ".join([f"{c} = ?" for c in columnas])
        cursor.execute(f"UPDATE {tabla} SET {set_sql} WHERE {pk_columna} = ?", *valores, pk_valor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def eliminar_fila(config, tabla, pk_columna, pk_valor):
    conn = get_local_connection(config)
    try:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {tabla} WHERE {pk_columna} = ?", pk_valor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def existe_id(config, tabla, pk_columna, pk_valor):
    conn = get_local_connection(config)
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {tabla} WHERE {pk_columna} = ?", pk_valor)
        return cursor.fetchone()[0] > 0
    finally:
        conn.close()


def listar_consumos(config):
    """
    Historial de consumos (ambas sedes, porque v_Consumo_Operativo ya es
    la vista particionada Norte UNION ALL Sur). Se une con Cliente_Operativo
    y Sede -- ambas tablas físicas locales en cualquier nodo -- solo para
    mostrar nombres en vez de IDs; no agrega ningún cruce de red adicional
    más allá del que la propia vista ya hace.

    El total se calcula sumando subtotal de v_Detalle_Consumo (no se toca
    Consumo_Financiero, que solo vive en Norte).
    """
    query = """
        SELECT
            c.id_consumo AS ID,
            cl.nombre + ' ' + cl.apellido AS Cliente,
            s.nombre AS Sede,
            c.fecha AS Fecha,
            (SELECT ISNULL(SUM(d.subtotal), 0)
             FROM v_Detalle_Consumo d
             WHERE d.id_consumo = c.id_consumo) AS Total
        FROM v_Consumo_Operativo c
        JOIN Cliente_Operativo cl ON cl.id_cliente = c.id_cliente
        JOIN Sede s ON s.id_sede = c.id_sede
        ORDER BY c.id_consumo
    """
    return ejecutar_query(config, query)


def listar_detalle_consumo(config, id_consumo):
    """Líneas de un consumo específico, con el nombre del producto."""
    query = """
        SELECT
            d.id_linea AS Linea,
            p.nombre AS Producto,
            d.cantidad AS Cantidad,
            d.subtotal AS Subtotal
        FROM v_Detalle_Consumo d
        JOIN Producto p ON p.id_producto = d.id_producto
        WHERE d.id_consumo = ?
        ORDER BY d.id_linea
    """
    return ejecutar_query(config, query, params=[id_consumo])


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

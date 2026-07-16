"""
Metadatos de los catálogos con replicación UNIDIRECCIONAL (Sede,
Estado_Animo, Producto). Norte es el nodo gestor: solo ahí se permite
crear/editar/eliminar. Sur es suscriptor: solo lectura.

Los IDs son SIEMPRE ingresados manualmente por el usuario en el
formulario (no hay autoincremento ni MAX+1), tal como se pidió.
"""

NODO_GESTOR_SEDE_ID = 1  # Sede Norte

CATALOGOS_META = {
    "producto": {
        "titulo": "Producto",
        "icono": "☕",
        "tabla": "Producto",
        "pk_columna": "id_producto",
        "orden": "id_producto",
        "campos": [
            {"columna": "id_producto", "etiqueta": "ID Producto *", "tipo": "numero", "pk": True},
            {"columna": "nombre", "etiqueta": "Nombre *", "tipo": "texto", "requerido": True},
            {"columna": "descripcion", "etiqueta": "Descripción", "tipo": "texto_largo"},
            {"columna": "tipo", "etiqueta": "Tipo", "tipo": "texto"},
            {"columna": "precio", "etiqueta": "Precio *", "tipo": "decimal", "requerido": True},
            {
                "columna": "id_estado", "etiqueta": "Estado de Ánimo *", "tipo": "combobox",
                "requerido": True,
                "opciones_query": "SELECT id_estado, nombre FROM Estado_Animo ORDER BY id_estado",
            },
        ],
    },
    "sede": {
        "titulo": "Sede",
        "icono": "🏛️",
        "tabla": "Sede",
        "pk_columna": "id_sede",
        "orden": "id_sede",
        "campos": [
            {"columna": "id_sede", "etiqueta": "ID Sede *", "tipo": "numero", "pk": True},
            {"columna": "nombre", "etiqueta": "Nombre *", "tipo": "texto", "requerido": True},
            {"columna": "ciudad", "etiqueta": "Ciudad *", "tipo": "texto", "requerido": True},
            {"columna": "direccion", "etiqueta": "Dirección", "tipo": "texto_largo"},
        ],
    },
    "estado": {
        "titulo": "Estado de Ánimo",
        "icono": "😊",
        "tabla": "Estado_Animo",
        "pk_columna": "id_estado",
        "orden": "id_estado",
        "campos": [
            {"columna": "id_estado", "etiqueta": "ID Estado *", "tipo": "numero", "pk": True},
            {"columna": "nombre", "etiqueta": "Nombre *", "tipo": "texto", "requerido": True},
            {"columna": "descripcion", "etiqueta": "Descripción", "tipo": "texto_largo"},
        ],
    },
}

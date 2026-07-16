# MoodCoffee POS — Paso 1: Login bloqueado por sede + panel de vistas

## Qué hace este paso (y qué NO hace todavía)

✅ Detecta el hostname real de la máquina y lo valida contra `config.json`.
✅ Login con dos tarjetas (Norte / Sur) — solo se puede entrar por la sede
   que coincide con el hostname de esta computadora.
✅ Tras el login, un panel con dos pestañas que leen en vivo:
   - `v_Consumo_Operativo`
   - `v_Detalle_Consumo`

❌ Todavía NO hay CRUD (nueva venta, clientes, productos, etc.) — eso es
   el siguiente paso una vez confirmemos que esto funciona en tus dos nodos.
❌ Ya NO existe "Cambiar de Sede" — cada instalación queda fija a su nodo.

## Estructura de carpetas

```
moodcoffee_pos/
├── main.py                  <- punto de entrada, igual en ambos nodos
├── config.norte.json        <- plantilla para la máquina del Norte
├── config.sur.json          <- plantilla para la máquina del Sur
├── requirements.txt
├── core/
│   ├── config_loader.py     <- lee y valida config.json contra el hostname
│   └── db.py                <- conexión pyodbc SOLO a la instancia local
└── ui/
    ├── login_screen.py      <- pantalla de login con bloqueo por sede
    └── dashboard.py         <- panel con las dos vistas particionadas
```

## Instalación (en CADA máquina, Norte y Sur)

1. Instala el **ODBC Driver 17 for SQL Server** si no lo tienes
   (Microsoft lo distribuye gratis para Windows).
2. Copia toda la carpeta `moodcoffee_pos/` a la máquina.
3. Instala dependencias:
   ```
   pip install -r requirements.txt
   ```
4. **En la máquina del Norte**: renombra `config.norte.json` a `config.json`.
   **En la máquina del Sur**: renombra `config.sur.json` a `config.json`.
   (Solo debe quedar UN `config.json` por máquina — borra o ignora el otro).
5. Ejecuta:
   ```
   python main.py
   ```

## Cómo probar que el bloqueo funciona

- En la máquina del Norte, intenta iniciar sesión eligiendo la tarjeta
  "Sede Sur" → debe rechazar el login con un mensaje de error.
- Elige "Sede Norte" (usuario `admin`, clave `1234`) → debe entrar sin problema.
- Repite el mismo par de pruebas en la máquina del Sur, con las tarjetas invertidas.

## Si el panel de vistas no carga datos

Revisa el mensaje de error emergente — normalmente indica:
- El nombre de instancia en `config.json` no coincide con el real de SQL Server.
- Falta el ODBC Driver 17.
- Las vistas `v_Consumo_Operativo` / `v_Detalle_Consumo` no existen en la
  base local de esa máquina (revisa que se hayan creado como en tus scripts).

## Siguientes pasos (una vez esto funcione en tus dos PCs)

1. CRUD de Cliente (Cliente_Operativo + Cliente_Datos si estás en Norte).
2. CRUD de Consumo respetando el orden top-down / bottom-up que ya definiste,
   con `SET XACT_ABORT ON`.
3. Manejo de errores cuando el linked server de la sede contraria está apagado.

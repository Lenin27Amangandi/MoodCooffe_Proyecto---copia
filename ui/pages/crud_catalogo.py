"""
Página CRUD genérica, reutilizada para Producto, Sede y Estado_Animo
(ver core/catalogos_meta.py). Solo el nodo gestor (Norte) ve los botones
de Nuevo/Editar/Eliminar; el nodo suscriptor (Sur) solo lee.
"""

import customtkinter as ctk
from tkinter import ttk, messagebox

from core.db import ejecutar_query, insertar_fila, actualizar_fila, eliminar_fila, existe_id
from core.catalogos_meta import NODO_GESTOR_SEDE_ID
from core.theme import PALETTE


class CrudCatalogoPage(ctk.CTkFrame):
    def __init__(self, master, config, meta):
        super().__init__(master, fg_color="transparent")
        self.config_data = config
        self.meta = meta
        self.es_gestor = config["sede_id"] == NODO_GESTOR_SEDE_ID
        self._build_ui()
        self.cargar_datos()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(26, 10))

        ctk.CTkLabel(
            header, text=self.meta["icono"], fg_color=PALETTE["pink_strip"], corner_radius=14,
            width=54, height=54, font=ctk.CTkFont(size=22)
        ).pack(side="left", padx=(0, 14))

        titulos = ctk.CTkFrame(header, fg_color="transparent")
        titulos.pack(side="left")
        ctk.CTkLabel(
            titulos, text=self.meta["titulo"], font=ctk.CTkFont(size=22, weight="bold"),
            text_color=PALETTE["espresso"]
        ).pack(anchor="w")

        subtitulo = (
            "Replicación unidireccional — esta sede es el nodo gestor (lectura y escritura)"
            if self.es_gestor
            else "Replicación unidireccional — esta sede es suscriptora (solo lectura)"
        )
        ctk.CTkLabel(
            titulos, text=subtitulo, font=ctk.CTkFont(size=12), text_color=PALETTE["mocha"]
        ).pack(anchor="w")

        botones = ctk.CTkFrame(header, fg_color="transparent")
        botones.pack(side="right")

        ctk.CTkButton(
            botones, text="🔄 Refrescar", width=110, command=self.cargar_datos
        ).pack(side="left", padx=(0, 8))

        if self.es_gestor:
            ctk.CTkButton(
                botones, text="➕ Nuevo", width=100,
                fg_color=PALETTE["terracotta"], hover_color="#A9683A", command=self._nuevo
            ).pack(side="left", padx=(0, 8))
            ctk.CTkButton(
                botones, text="✏️ Editar", width=100, command=self._editar
            ).pack(side="left", padx=(0, 8))
            ctk.CTkButton(
                botones, text="🗑️ Eliminar", width=100,
                fg_color="#B23A3A", hover_color="#8C2C2C", command=self._eliminar
            ).pack(side="left")
        else:
            ctk.CTkLabel(
                botones, text="🔒 Solo lectura — el nodo gestor es Sede Norte",
                font=ctk.CTkFont(size=11, weight="bold"), text_color=PALETTE["mocha"]
            ).pack(side="left")

        cont = ctk.CTkFrame(self, fg_color=PALETTE["card_bg"], corner_radius=16)
        cont.pack(fill="both", expand=True, padx=30, pady=(10, 26))

        tabla_frame = ctk.CTkFrame(cont, fg_color="transparent")
        tabla_frame.pack(fill="both", expand=True, padx=14, pady=14)

        self.tree = ttk.Treeview(tabla_frame, show="headings")
        vsb = ttk.Scrollbar(tabla_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    def cargar_datos(self):
        tabla = self.meta["tabla"]
        orden = self.meta["orden"]
        try:
            columnas, filas = ejecutar_query(self.config_data, f"SELECT * FROM {tabla} ORDER BY {orden}")
            self.tree.delete(*self.tree.get_children())
            self.tree["columns"] = columnas
            for col in columnas:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=130, anchor="center")
            for fila in filas:
                self.tree.insert("", "end", values=fila)
        except Exception as e:
            messagebox.showerror(
                f"Error al cargar {self.meta['titulo']}",
                f"No se pudieron cargar los datos.\n\nDetalle técnico:\n{e}"
            )

    def _fila_seleccionada_dict(self):
        seleccion = self.tree.selection()
        if not seleccion:
            return None
        columnas = self.tree["columns"]
        valores = self.tree.item(seleccion[0], "values")
        return dict(zip(columnas, valores))

    def _nuevo(self):
        FormularioCrud(self, self.config_data, self.meta, on_guardado=self.cargar_datos, fila_editar=None)

    def _editar(self):
        fila = self._fila_seleccionada_dict()
        if not fila:
            messagebox.showwarning("Selecciona una fila", "Elige primero un registro de la tabla para editar.")
            return
        FormularioCrud(self, self.config_data, self.meta, on_guardado=self.cargar_datos, fila_editar=fila)

    def _eliminar(self):
        fila = self._fila_seleccionada_dict()
        if not fila:
            messagebox.showwarning("Selecciona una fila", "Elige primero un registro de la tabla para eliminar.")
            return

        pk_columna = self.meta["pk_columna"]
        pk_valor = fila.get(pk_columna)

        if not messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Seguro que quieres eliminar el registro con {pk_columna} = {pk_valor}?\n\n"
            f"Si otras tablas dependen de este registro (llaves foráneas), "
            f"la base de datos rechazará la eliminación."
        ):
            return

        try:
            eliminar_fila(self.config_data, self.meta["tabla"], pk_columna, pk_valor)
            self.cargar_datos()
        except Exception as e:
            messagebox.showerror("Error al eliminar", f"No se pudo eliminar el registro.\n\nDetalle técnico:\n{e}")


class FormularioCrud(ctk.CTkToplevel):
    def __init__(self, master, config, meta, on_guardado, fila_editar=None):
        super().__init__(master)
        self.config_data = config
        self.meta = meta
        self.on_guardado = on_guardado
        self.fila_editar = fila_editar
        self.es_edicion = fila_editar is not None
        self.widgets = {}
        self.opciones_combobox = {}

        accion = "Editar" if self.es_edicion else "Nuevo"
        self.title(f"{accion} {meta['titulo']}")
        self.geometry("400x560")
        self.resizable(False, False)
        self.grab_set()

        ctk.CTkLabel(
            self, text=f"{'✏️' if self.es_edicion else '➕'} {accion} {meta['titulo']}",
            font=ctk.CTkFont(size=18, weight="bold"), text_color=PALETTE["espresso"]
        ).pack(pady=(20, 12))

        scroll = ctk.CTkScrollableFrame(self, width=340, height=380)
        scroll.pack(padx=20, pady=(0, 8), fill="both", expand=True)

        for campo in meta["campos"]:
            self._crear_campo(scroll, campo)

        self.lbl_error = ctk.CTkLabel(
            self, text="", text_color="#B23A3A", font=ctk.CTkFont(size=11, weight="bold"),
            wraplength=340, justify="center"
        )
        self.lbl_error.pack(pady=(4, 8), padx=20)

        ctk.CTkButton(
            self, text="Guardar", fg_color=PALETTE["terracotta"], hover_color="#A9683A",
            command=self._guardar
        ).pack(pady=(0, 20))

    def _crear_campo(self, master, campo):
        columna = campo["columna"]
        tipo = campo["tipo"]
        valor_actual = self.fila_editar.get(columna) if self.fila_editar else None

        ctk.CTkLabel(
            master, text=campo["etiqueta"], font=ctk.CTkFont(size=12, weight="bold"),
            text_color=PALETTE["espresso"]
        ).pack(anchor="w", pady=(6, 0))

        if tipo == "combobox":
            _, filas_opciones = ejecutar_query(self.config_data, campo["opciones_query"])
            mapa = {f"{f[0]} - {f[1]}": f[0] for f in filas_opciones}
            self.opciones_combobox[columna] = mapa
            widget = ctk.CTkComboBox(master, values=list(mapa.keys()) or ["(sin opciones)"], width=300)
            if valor_actual is not None:
                for label, id_val in mapa.items():
                    if str(id_val) == str(valor_actual):
                        widget.set(label)
                        break
            widget.pack(pady=(2, 4), fill="x")

        elif tipo == "texto_largo":
            widget = ctk.CTkTextbox(master, width=300, height=60)
            if valor_actual is not None:
                widget.insert("1.0", str(valor_actual))
            widget.pack(pady=(2, 4), fill="x")

        else:  # texto, numero, decimal
            widget = ctk.CTkEntry(master, width=300)
            if valor_actual is not None:
                widget.insert(0, str(valor_actual))
            if campo.get("pk") and self.es_edicion:
                # No se permite cambiar la PK al editar (evita romper FKs de otras tablas)
                widget.configure(state="disabled")
            widget.pack(pady=(2, 4), fill="x")

        self.widgets[columna] = widget

    def _leer_valor(self, campo):
        columna = campo["columna"]
        tipo = campo["tipo"]
        widget = self.widgets[columna]

        if tipo == "combobox":
            return self.opciones_combobox[columna].get(widget.get())

        if tipo == "texto_largo":
            return widget.get("1.0", "end").strip() or None

        valor = widget.get().strip()
        if tipo == "numero":
            return int(valor) if valor != "" else None
        if tipo == "decimal":
            return float(valor) if valor != "" else None
        return valor or None

    def _guardar(self):
        try:
            valores = {c["columna"]: self._leer_valor(c) for c in self.meta["campos"]}

            faltantes = [
                c["etiqueta"] for c in self.meta["campos"]
                if c.get("requerido") and valores[c["columna"]] in (None, "")
            ]
            if faltantes:
                self.lbl_error.configure(text=f"⚠️ Campos obligatorios: {', '.join(faltantes)}")
                return

            pk_columna = self.meta["pk_columna"]
            pk_valor = valores[pk_columna]

            if pk_valor is None:
                self.lbl_error.configure(text="⚠️ Debes ingresar un ID válido")
                return

            if not self.es_edicion:
                if existe_id(self.config_data, self.meta["tabla"], pk_columna, pk_valor):
                    self.lbl_error.configure(text=f"⚠️ Ya existe un registro con {pk_columna} = {pk_valor}")
                    return
                columnas = [c["columna"] for c in self.meta["campos"]]
                datos = [valores[c] for c in columnas]
                insertar_fila(self.config_data, self.meta["tabla"], columnas, datos)
            else:
                columnas = [c["columna"] for c in self.meta["campos"] if not c.get("pk")]
                datos = [valores[c] for c in columnas]
                actualizar_fila(self.config_data, self.meta["tabla"], pk_columna, pk_valor, columnas, datos)

            messagebox.showinfo("Guardado", f"{self.meta['titulo']} guardado correctamente.")
            self.on_guardado()
            self.destroy()
        except ValueError:
            self.lbl_error.configure(text="⚠️ Revisa los campos numéricos (deben ser números válidos)")
        except Exception as e:
            self.lbl_error.configure(text=f"⚠️ Error al guardar:\n{e}")

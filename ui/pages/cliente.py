"""
Página de Cliente. La tabla que se muestra y la forma de guardar un
cliente nuevo dependen del nodo (ver core/db.py -> listar_clientes /
insertar_cliente para el detalle de la fragmentación vertical).
"""

import customtkinter as ctk
from tkinter import ttk, messagebox

from core.db import listar_clientes, insertar_cliente
from core.theme import PALETTE


class ClientePage(ctk.CTkFrame):
    def __init__(self, master, config):
        super().__init__(master, fg_color="transparent")
        self.config_data = config
        self._build_ui()
        self.cargar_datos()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(26, 10))

        ctk.CTkLabel(
            header, text="👥", fg_color=PALETTE["pink_strip"], corner_radius=14,
            width=54, height=54, font=ctk.CTkFont(size=22)
        ).pack(side="left", padx=(0, 14))

        titulos = ctk.CTkFrame(header, fg_color="transparent")
        titulos.pack(side="left")
        ctk.CTkLabel(
            titulos, text="Cliente", font=ctk.CTkFont(size=22, weight="bold"),
            text_color=PALETTE["espresso"]
        ).pack(anchor="w")

        subtitulo = (
            "Cliente_Operativo (ambas sedes) unido con Cliente_Datos (Norte)"
            if self.config_data["sede_id"] == 1
            else "Cliente_Operativo local — los datos sensibles se guardan en Norte"
        )
        ctk.CTkLabel(
            titulos, text=subtitulo, font=ctk.CTkFont(size=12), text_color=PALETTE["mocha"]
        ).pack(anchor="w")

        botones = ctk.CTkFrame(header, fg_color="transparent")
        botones.pack(side="right")
        ctk.CTkButton(
            botones, text="🔄 Refrescar", width=110, command=self.cargar_datos
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            botones, text="➕ Nuevo cliente", width=150,
            fg_color=PALETTE["terracotta"], hover_color="#A9683A",
            command=self._abrir_formulario
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
        try:
            columnas, filas = listar_clientes(self.config_data)
            self.tree.delete(*self.tree.get_children())
            self.tree["columns"] = columnas
            for col in columnas:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=140, anchor="center")
            for fila in filas:
                self.tree.insert("", "end", values=fila)
        except Exception as e:
            messagebox.showerror(
                "Error al cargar Cliente",
                f"No se pudieron cargar los datos.\n\nDetalle técnico:\n{e}"
            )

    def _abrir_formulario(self):
        FormularioCliente(self, self.config_data, on_guardado=self.cargar_datos)


class FormularioCliente(ctk.CTkToplevel):
    def __init__(self, master, config, on_guardado):
        super().__init__(master)
        self.config_data = config
        self.on_guardado = on_guardado

        self.title("Nuevo cliente")
        self.geometry("380x500")
        self.resizable(False, False)
        self.grab_set()  # modal

        ctk.CTkLabel(
            self, text="➕ Nuevo cliente", font=ctk.CTkFont(size=18, weight="bold"),
            text_color=PALETTE["espresso"]
        ).pack(pady=(20, 4))

        nota = (
            "Se registrará en Cliente_Operativo y en Cliente_Datos, ambas locales en Norte."
            if config["sede_id"] == 1
            else "Nombre/Apellido → Cliente_Operativo local.\n"
                 "Cédula/Teléfono/Correo → se envían a Cliente_Datos en Norte vía Linked Server."
        )
        ctk.CTkLabel(
            self, text=nota, font=ctk.CTkFont(size=11), text_color=PALETTE["mocha"],
            wraplength=320, justify="center"
        ).pack(pady=(0, 16), padx=20)

        self.entry_nombre = self._campo("Nombre *")
        self.entry_apellido = self._campo("Apellido *")
        self.entry_cedula = self._campo("Cédula *")
        self.entry_telefono = self._campo("Teléfono")
        self.entry_correo = self._campo("Correo")

        self.lbl_error = ctk.CTkLabel(
            self, text="", text_color="#B23A3A", font=ctk.CTkFont(size=11, weight="bold"),
            wraplength=320, justify="center"
        )
        self.lbl_error.pack(pady=(4, 8), padx=20)

        ctk.CTkButton(
            self, text="Guardar cliente", fg_color=PALETTE["terracotta"], hover_color="#A9683A",
            command=self._guardar
        ).pack(pady=(4, 20))

    def _campo(self, etiqueta):
        ctk.CTkLabel(
            self, text=etiqueta, font=ctk.CTkFont(size=12, weight="bold"), text_color=PALETTE["espresso"]
        ).pack(anchor="w", padx=30)
        entry = ctk.CTkEntry(self, width=320)
        entry.pack(pady=(2, 10), padx=30)
        return entry

    def _guardar(self):
        nombre = self.entry_nombre.get().strip()
        apellido = self.entry_apellido.get().strip()
        cedula = self.entry_cedula.get().strip()
        telefono = self.entry_telefono.get().strip() or None
        correo = self.entry_correo.get().strip() or None

        if not nombre or not apellido or not cedula:
            self.lbl_error.configure(text="⚠️ Nombre, apellido y cédula son obligatorios")
            return

        try:
            nuevo_id = insertar_cliente(self.config_data, nombre, apellido, cedula, telefono, correo)
            messagebox.showinfo("Cliente registrado", f"Cliente #{nuevo_id} registrado correctamente.")
            self.on_guardado()
            self.destroy()
        except Exception as e:
            self.lbl_error.configure(text=f"⚠️ Error al guardar:\n{e}")

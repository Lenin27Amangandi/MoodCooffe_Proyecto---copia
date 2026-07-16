"""
Página genérica de solo lectura para catálogos replicados de forma
UNIDIRECCIONAL (Sede, Estado_Animo, Producto). Las tres ya viven
físicamente en el nodo local (llegan por replicación desde Norte), así
que la consulta siempre es local, nunca cruza el Linked Server.
"""

import customtkinter as ctk
from tkinter import ttk, messagebox

from core.db import ejecutar_query
from core.theme import PALETTE


class CatalogoPage(ctk.CTkFrame):
    def __init__(self, master, config, titulo, icono, query, anchos=None):
        super().__init__(master, fg_color="transparent")
        self.config_data = config
        self.titulo = titulo
        self.icono = icono
        self.query = query
        self.anchos = anchos or {}
        self._build_ui()
        self.cargar_datos()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(26, 10))

        ctk.CTkLabel(
            header, text=self.icono, fg_color=PALETTE["pink_strip"], corner_radius=14,
            width=54, height=54, font=ctk.CTkFont(size=22)
        ).pack(side="left", padx=(0, 14))

        titulos = ctk.CTkFrame(header, fg_color="transparent")
        titulos.pack(side="left")
        ctk.CTkLabel(
            titulos, text=self.titulo, font=ctk.CTkFont(size=22, weight="bold"),
            text_color=PALETTE["espresso"]
        ).pack(anchor="w")
        ctk.CTkLabel(
            titulos, text="Catálogo replicado — disponible localmente en esta sede",
            font=ctk.CTkFont(size=12), text_color=PALETTE["mocha"]
        ).pack(anchor="w")

        ctk.CTkButton(
            header, text="🔄 Refrescar", width=110, command=self.cargar_datos
        ).pack(side="right")

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
            columnas, filas = ejecutar_query(self.config_data, self.query)
            self.tree.delete(*self.tree.get_children())
            self.tree["columns"] = columnas
            for col in columnas:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=self.anchos.get(col, 120), anchor="center")
            for fila in filas:
                self.tree.insert("", "end", values=fila)
        except Exception as e:
            messagebox.showerror(
                f"Error al cargar {self.titulo}",
                f"No se pudieron cargar los datos.\n\nDetalle técnico:\n{e}"
            )

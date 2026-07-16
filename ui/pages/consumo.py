"""
Página de Consumo: historial completo (ambas sedes, vía las vistas
particionadas) con patrón maestro-detalle. Al seleccionar un consumo en
la tabla superior, se cargan sus líneas en la tabla inferior.
"""

import customtkinter as ctk
from tkinter import ttk, messagebox

from core.db import listar_consumos, listar_detalle_consumo
from core.theme import PALETTE


class ConsumoPage(ctk.CTkFrame):
    def __init__(self, master, config):
        super().__init__(master, fg_color="transparent")
        self.config_data = config
        self._build_ui()
        self.cargar_consumos()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(26, 10))

        ctk.CTkLabel(
            header, text="🧾", fg_color=PALETTE["pink_strip"], corner_radius=14,
            width=54, height=54, font=ctk.CTkFont(size=22)
        ).pack(side="left", padx=(0, 14))

        titulos = ctk.CTkFrame(header, fg_color="transparent")
        titulos.pack(side="left")
        ctk.CTkLabel(
            titulos, text="Consumo", font=ctk.CTkFont(size=22, weight="bold"),
            text_color=PALETTE["espresso"]
        ).pack(anchor="w")
        ctk.CTkLabel(
            titulos, text="v_Consumo_Operativo ⋈ v_Detalle_Consumo — historial de ambas sedes",
            font=ctk.CTkFont(size=12), text_color=PALETTE["mocha"]
        ).pack(anchor="w")

        ctk.CTkButton(
            header, text="🔄 Refrescar", width=110, command=self.cargar_consumos
        ).pack(side="right")

        # --- Tabla maestro: consumos ---
        cont_maestro = ctk.CTkFrame(self, fg_color=PALETTE["card_bg"], corner_radius=16)
        cont_maestro.pack(fill="both", expand=True, padx=30, pady=(10, 8))

        ctk.CTkLabel(
            cont_maestro, text="Consumos", font=ctk.CTkFont(size=13, weight="bold"),
            text_color=PALETTE["espresso"]
        ).pack(anchor="w", padx=16, pady=(12, 0))

        frame_maestro = ctk.CTkFrame(cont_maestro, fg_color="transparent")
        frame_maestro.pack(fill="both", expand=True, padx=14, pady=(6, 14))

        self.tree_consumos = ttk.Treeview(frame_maestro, show="headings", height=8)
        vsb1 = ttk.Scrollbar(frame_maestro, orient="vertical", command=self.tree_consumos.yview)
        self.tree_consumos.configure(yscrollcommand=vsb1.set)
        self.tree_consumos.pack(side="left", fill="both", expand=True)
        vsb1.pack(side="right", fill="y")
        self.tree_consumos.bind("<<TreeviewSelect>>", self._on_seleccionar_consumo)

        # --- Tabla detalle: líneas del consumo seleccionado ---
        cont_detalle = ctk.CTkFrame(self, fg_color=PALETTE["card_bg"], corner_radius=16)
        cont_detalle.pack(fill="both", expand=True, padx=30, pady=(8, 26))

        self.lbl_detalle_titulo = ctk.CTkLabel(
            cont_detalle, text="Detalle — selecciona un consumo arriba",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=PALETTE["espresso"]
        )
        self.lbl_detalle_titulo.pack(anchor="w", padx=16, pady=(12, 0))

        frame_detalle = ctk.CTkFrame(cont_detalle, fg_color="transparent")
        frame_detalle.pack(fill="both", expand=True, padx=14, pady=(6, 14))

        self.tree_detalle = ttk.Treeview(frame_detalle, show="headings", height=6)
        vsb2 = ttk.Scrollbar(frame_detalle, orient="vertical", command=self.tree_detalle.yview)
        self.tree_detalle.configure(yscrollcommand=vsb2.set)
        self.tree_detalle.pack(side="left", fill="both", expand=True)
        vsb2.pack(side="right", fill="y")

    def cargar_consumos(self):
        try:
            columnas, filas = listar_consumos(self.config_data)
            self.tree_consumos.delete(*self.tree_consumos.get_children())
            self.tree_consumos["columns"] = columnas
            for col in columnas:
                self.tree_consumos.heading(col, text=col)
                self.tree_consumos.column(col, width=130, anchor="center")
            for fila in filas:
                self.tree_consumos.insert("", "end", values=fila)

            self.tree_detalle.delete(*self.tree_detalle.get_children())
            self.tree_detalle["columns"] = []
            self.lbl_detalle_titulo.configure(text="Detalle — selecciona un consumo arriba")
        except Exception as e:
            messagebox.showerror(
                "Error al cargar Consumo",
                f"No se pudieron cargar los consumos.\n\nDetalle técnico:\n{e}"
            )

    def _on_seleccionar_consumo(self, event=None):
        seleccion = self.tree_consumos.selection()
        if not seleccion:
            return
        valores = self.tree_consumos.item(seleccion[0], "values")
        id_consumo = valores[0]  # la primera columna siempre es ID

        try:
            columnas, filas = listar_detalle_consumo(self.config_data, id_consumo)
            self.tree_detalle.delete(*self.tree_detalle.get_children())
            self.tree_detalle["columns"] = columnas
            for col in columnas:
                self.tree_detalle.heading(col, text=col)
                self.tree_detalle.column(col, width=130, anchor="center")
            for fila in filas:
                self.tree_detalle.insert("", "end", values=fila)
            self.lbl_detalle_titulo.configure(text=f"Detalle del consumo #{id_consumo}")
        except Exception as e:
            messagebox.showerror(
                "Error al cargar Detalle_Consumo",
                f"No se pudo cargar el detalle del consumo #{id_consumo}.\n\nDetalle técnico:\n{e}"
            )

"""
Contenedor principal tras el login: Sidebar + área de contenido.
Solo "Inicio" está completamente implementado con datos reales por
ahora; el resto de páginas del menú muestran un placeholder hasta que
construyamos su CRUD (ver roadmap del proyecto).
"""

import customtkinter as ctk

from core.theme import PALETTE
from ui.sidebar import Sidebar
from ui.pages.inicio import InicioPage

NOMBRES_PAGINA = {
    "venta": "Nueva Venta",
    "clientes": "Cliente",
    "consumo": "Consumo",
    "producto": "Producto",
    "sede": "Sede",
    "estado": "Estado de Ánimo",
}


class Dashboard(ctk.CTkFrame):
    def __init__(self, master, config):
        super().__init__(master, fg_color=PALETTE["bg_main"])
        self.config_data = config

        self.sidebar = Sidebar(self, config, on_nav=self.mostrar_pagina)
        self.sidebar.pack(side="left", fill="y")

        self.contenido = ctk.CTkFrame(self, fg_color=PALETTE["bg_main"])
        self.contenido.pack(side="left", fill="both", expand=True)

        self.pagina_actual = None
        self.mostrar_pagina("inicio")

    def _limpiar_contenido(self):
        for widget in self.contenido.winfo_children():
            widget.destroy()

    def mostrar_pagina(self, key):
        self.sidebar.set_activo(key)
        self._limpiar_contenido()

        if key == "inicio":
            pagina = InicioPage(self.contenido, self.config_data, on_navegar=self.mostrar_pagina)
        else:
            pagina = self._crear_placeholder(key)

        pagina.pack(fill="both", expand=True)
        self.pagina_actual = pagina

    def _crear_placeholder(self, key):
        frame = ctk.CTkFrame(self.contenido, fg_color="transparent")
        ctk.CTkLabel(
            frame, text=f"🚧 {NOMBRES_PAGINA.get(key, key)}",
            font=ctk.CTkFont(size=20, weight="bold"), text_color=PALETTE["espresso"]
        ).pack(pady=(60, 6))
        ctk.CTkLabel(
            frame, text="Esta sección todavía no está implementada.",
            font=ctk.CTkFont(size=13), text_color=PALETTE["mocha"]
        ).pack()
        return frame

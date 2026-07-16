"""
Página de Inicio. Réplica del mockup HTML: encabezado con saludo,
4 tarjetas de estadísticas (calculadas en vivo desde la base local) y
4 accesos rápidos que navegan a otras páginas del sidebar.
"""

import datetime as _dt

import customtkinter as ctk
from tkinter import messagebox

from core.db import obtener_stats_inicio
from core.theme import PALETTE

DIAS_LARGOS = ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"]


class InicioPage(ctk.CTkFrame):
    def __init__(self, master, config, on_navegar):
        super().__init__(master, fg_color="transparent")
        self.config_data = config
        self.on_navegar = on_navegar
        self._build_ui()
        self.cargar_datos()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(26, 16))

        ctk.CTkLabel(
            header, text="🏠", fg_color=PALETTE["pink_strip"], corner_radius=14,
            width=54, height=54, font=ctk.CTkFont(size=22)
        ).pack(side="left", padx=(0, 14))

        titulos = ctk.CTkFrame(header, fg_color="transparent")
        titulos.pack(side="left")

        ctk.CTkLabel(
            titulos, text="¡Buen turno!", font=ctk.CTkFont(size=22, weight="bold"),
            text_color=PALETTE["espresso"]
        ).pack(anchor="w")

        hoy = _dt.datetime.now()
        dia_txt = DIAS_LARGOS[(hoy.weekday() + 1) % 7]
        ctk.CTkLabel(
            titulos, text=f"Hoy es {dia_txt} · {self.config_data['sede_nombre']}",
            font=ctk.CTkFont(size=13), text_color=PALETTE["mocha"]
        ).pack(anchor="w")

        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", padx=30, pady=10)
        for i in range(4):
            stats_frame.grid_columnconfigure(i, weight=1, uniform="stat")

        self.card_consumos = self._crear_stat_card(stats_frame, 0, "🧾", "0", "Consumos registrados")
        self.card_total = self._crear_stat_card(stats_frame, 1, "💰", "$0.00", "Total vendido")
        self.card_clientes = self._crear_stat_card(stats_frame, 2, "👥", "0", "Clientes registrados")
        self.card_productos = self._crear_stat_card(stats_frame, 3, "☕", "0", "Productos en el menú")

        acciones_frame = ctk.CTkFrame(self, fg_color="transparent")
        acciones_frame.pack(fill="x", padx=30, pady=(20, 10))
        for i in range(4):
            acciones_frame.grid_columnconfigure(i, weight=1, uniform="accion")

        self._crear_accion(acciones_frame, 0, "🛒", "Registrar consumo", "Cobrar a un cliente", "venta")
        self._crear_accion(acciones_frame, 1, "👥", "Ver clientes", "Buscar o agregar uno nuevo", "clientes")
        self._crear_accion(acciones_frame, 2, "🧾", "Ver consumos", "Revisar consumos anteriores", "consumo")
        self._crear_accion(acciones_frame, 3, "📋", "Revisar productos", "Productos disponibles", "producto")

    def _crear_stat_card(self, master, col, icono, valor, etiqueta):
        card = ctk.CTkFrame(master, fg_color=PALETTE["card_bg"], corner_radius=16)
        card.grid(row=0, column=col, padx=8, sticky="nsew")

        ctk.CTkLabel(card, text=icono, font=ctk.CTkFont(size=20)).pack(anchor="w", padx=18, pady=(16, 4))
        lbl_valor = ctk.CTkLabel(
            card, text=valor, font=ctk.CTkFont(size=24, weight="bold"), text_color=PALETTE["espresso"]
        )
        lbl_valor.pack(anchor="w", padx=18)
        ctk.CTkLabel(
            card, text=etiqueta, font=ctk.CTkFont(size=11), text_color=PALETTE["mocha"]
        ).pack(anchor="w", padx=18, pady=(2, 16))
        return lbl_valor

    def _crear_accion(self, master, col, icono, titulo, subtitulo, destino):
        card = ctk.CTkFrame(master, fg_color=PALETTE["card_bg"], corner_radius=16, height=140)
        card.grid(row=0, column=col, padx=8, sticky="nsew")
        card.grid_propagate(False)

        ctk.CTkLabel(card, text=icono, font=ctk.CTkFont(size=26)).pack(pady=(20, 6))
        ctk.CTkLabel(
            card, text=titulo, font=ctk.CTkFont(size=13, weight="bold"), text_color=PALETTE["espresso"]
        ).pack()
        ctk.CTkLabel(
            card, text=subtitulo, font=ctk.CTkFont(size=10), text_color=PALETTE["mocha"]
        ).pack(pady=(2, 0))

        widgets = [card] + list(card.winfo_children())
        for w in widgets:
            w.bind("<Button-1>", lambda e, d=destino: self.on_navegar(d))

    def cargar_datos(self):
        try:
            stats = obtener_stats_inicio(self.config_data)
            self.card_consumos.configure(text=str(stats["consumos_registrados"]))
            self.card_total.configure(text=f"${stats['total_vendido']:.2f}")
            self.card_clientes.configure(text=str(stats["clientes_registrados"]))
            self.card_productos.configure(text=str(stats["productos_menu"]))
        except Exception as e:
            messagebox.showerror(
                "Error al cargar Inicio",
                f"No se pudieron calcular las estadísticas.\n\nDetalle técnico:\n{e}"
            )

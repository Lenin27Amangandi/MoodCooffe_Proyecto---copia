"""
Menú lateral, fiel al mockup HTML: logo, tag de sede, reloj/uptime,
navegación y chip del empleado. NO tiene botón "Cambiar de sede" —
esa función se eliminó del diseño (cada nodo es fijo por hostname).
"""

import customtkinter as ctk
from datetime import datetime

from core.theme import PALETTE

NAV_ITEMS = [
    ("inicio", "🏠", "Inicio"),
    ("venta", "🛒", "Nueva Venta"),
    ("clientes", "👥", "Cliente"),
    ("consumo", "🧾", "Consumo"),
    ("producto", "📋", "Producto"),
    ("sede", "🏛️", "Sede"),
    ("estado", "😊", "Estado de Ánimo"),
]

DIAS = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"]
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, config, on_nav):
        super().__init__(master, width=260, fg_color=PALETTE["bg_sidebar"], corner_radius=0)
        self.config_data = config
        self.on_nav = on_nav
        self.pack_propagate(False)
        self._nav_buttons = {}
        self._sesion_inicio = datetime.now()
        self._build_ui()
        self._tick_reloj()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(20, 10))

        ctk.CTkLabel(
            header, text="☕ MoodCoffee", font=ctk.CTkFont(size=19, weight="bold"),
            text_color=PALETTE["espresso"]
        ).pack(anchor="w")

        sede_nombre = self.config_data["sede_nombre"]
        self.lbl_tag = ctk.CTkLabel(
            header, text=f"🏛️ Turno en {sede_nombre}", fg_color=PALETTE["milk"],
            text_color=PALETTE["espresso"], corner_radius=12,
            font=ctk.CTkFont(size=11, weight="bold"), padx=10, pady=4
        )
        self.lbl_tag.pack(anchor="w", pady=(10, 8))

        self.lbl_fecha = ctk.CTkLabel(
            header, text="", font=ctk.CTkFont(size=10, weight="bold"),
            text_color=PALETTE["mocha"], justify="left"
        )
        self.lbl_fecha.pack(anchor="w")

        self.lbl_uptime = ctk.CTkLabel(
            header, text="", font=ctk.CTkFont(size=10, weight="bold"),
            text_color=PALETTE["mocha"], justify="left"
        )
        self.lbl_uptime.pack(anchor="w", pady=(2, 0))

        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="x", padx=12, pady=10)

        for key, icon, label in NAV_ITEMS:
            btn = ctk.CTkButton(
                nav_frame, text=f"{icon}  {label}", anchor="w",
                fg_color="transparent", text_color=PALETTE["espresso"],
                hover_color=PALETTE["milk"], font=ctk.CTkFont(size=13, weight="bold"),
                height=40, corner_radius=10,
                command=lambda k=key: self._click_nav(k)
            )
            btn.pack(fill="x", pady=3)
            self._nav_buttons[key] = btn

        self.set_activo("inicio")

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=14, pady=16)

        chip = ctk.CTkFrame(footer, fg_color=PALETTE["card_bg"], corner_radius=12)
        chip.pack(fill="x")
        ctk.CTkLabel(chip, text="🏛️", font=ctk.CTkFont(size=18)).pack(side="left", padx=(10, 6), pady=10)
        info = ctk.CTkFrame(chip, fg_color="transparent")
        info.pack(side="left", pady=8)
        ctk.CTkLabel(
            info, text="Empleado", font=ctk.CTkFont(size=12, weight="bold"),
            text_color=PALETTE["espresso"]
        ).pack(anchor="w")
        ctk.CTkLabel(
            info, text=f"{sede_nombre} · Quito", font=ctk.CTkFont(size=10),
            text_color=PALETTE["mocha"]
        ).pack(anchor="w")

    def _click_nav(self, key):
        self.set_activo(key)
        self.on_nav(key)

    def set_activo(self, key):
        for k, btn in self._nav_buttons.items():
            if k == key:
                btn.configure(fg_color=PALETTE["active_nav"], text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color=PALETTE["espresso"])

    def _tick_reloj(self):
        ahora = datetime.now()
        self.lbl_fecha.configure(text=self._formato_fecha(ahora))

        elapsed = int((datetime.now() - self._sesion_inicio).total_seconds())
        hh, resto = divmod(elapsed, 3600)
        mm, ss = divmod(resto, 60)
        self.lbl_uptime.configure(text=f"⏱ Conectado: {hh:02d}:{mm:02d}:{ss:02d}")

        self.after(1000, self._tick_reloj)

    def _formato_fecha(self, dt):
        dia = DIAS[(dt.weekday() + 1) % 7]  # datetime: Lun=0..Dom=6 -> Dom=0..Sab=6
        mes = MESES[dt.month - 1]
        return f"📅 {dia} {dt.day} {mes} {dt.year} · {dt.strftime('%H:%M:%S')}"

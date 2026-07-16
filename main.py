"""
Punto de entrada. Mismo archivo para Norte y Sur; lo único que cambia
entre nodos es config.json (ver config.norte.json / config.sur.json).
"""

import sys
import customtkinter as ctk
from tkinter import messagebox

from core.config_loader import cargar_config, ConfigError
from core.db import probar_conexion
from ui.login_screen import LoginScreen
from ui.dashboard import Dashboard

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class MoodCoffeeApp(ctk.CTk):
    def __init__(self, config):
        super().__init__()
        self.config_data = config
        self.title(f"MoodCoffee POS — {config['sede_nombre']} ({config['hostname_actual']})")
        self.geometry("1100x700")
        self.minsize(900, 600)

        self.frame_actual = None
        self.mostrar_login()

    def _limpiar_frame_actual(self):
        if self.frame_actual is not None:
            self.frame_actual.destroy()

    def mostrar_login(self):
        self._limpiar_frame_actual()
        self.frame_actual = LoginScreen(self, self.config_data, on_login_success=self.mostrar_dashboard)
        self.frame_actual.pack(fill="both", expand=True)

    def mostrar_dashboard(self):
        self._limpiar_frame_actual()
        self.frame_actual = Dashboard(self, self.config_data)
        self.frame_actual.pack(fill="both", expand=True)


def main():
    try:
        config = cargar_config()
    except ConfigError as e:
        root = ctk.CTk()
        root.withdraw()
        messagebox.showerror("Error de configuración", str(e))
        sys.exit(1)

    ok, error = probar_conexion(config)
    if not ok:
        root = ctk.CTk()
        root.withdraw()
        messagebox.showwarning(
            "Sin conexión a SQL Server",
            f"No se pudo conectar a la instancia local '{config['instancia_local']}'.\n\n"
            f"Detalle técnico:\n{error}\n\n"
            f"La aplicación se abrirá igual, pero el panel de vistas fallará al cargar."
        )

    app = MoodCoffeeApp(config)
    app.mainloop()


if __name__ == "__main__":
    main()

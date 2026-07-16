"""
Pantalla de Login. Muestra ambas tarjetas (Norte / Sur) igual que el
mockup original, pero el login SOLO tiene éxito si la sede elegida
coincide con la sede que ya viene fijada en config.json (que a su vez
ya fue validada contra el hostname real de esta máquina).
"""

import customtkinter as ctk

USUARIO_DEMO = "admin"
CLAVE_DEMO = "1234"


class LoginScreen(ctk.CTkFrame):
    def __init__(self, master, config, on_login_success):
        super().__init__(master, fg_color="transparent")
        self.config_data = config
        self.on_login_success = on_login_success
        self.sede_elegida = None
        self._build_ui()

    def _build_ui(self):
        contenedor = ctk.CTkFrame(self, corner_radius=20, fg_color=("#FFF8F0", "#2b2320"))
        contenedor.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            contenedor, text="☕ MoodCoffee",
            font=ctk.CTkFont(size=28, weight="bold"), text_color="#4B2E1E"
        ).pack(pady=(30, 0), padx=60)

        ctk.CTkLabel(
            contenedor, text="PUNTO DE VENTA",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#A9825D"
        ).pack(pady=(0, 20))

        ctk.CTkLabel(
            contenedor, text="Tu sede de hoy",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#4B2E1E"
        ).pack(anchor="w", padx=30)

        tarjetas_frame = ctk.CTkFrame(contenedor, fg_color="transparent")
        tarjetas_frame.pack(pady=10, padx=30)

        self.btn_norte = self._crear_tarjeta_sede(tarjetas_frame, "🏛️ Sede Norte", 1)
        self.btn_norte.grid(row=0, column=0, padx=8)

        self.btn_sur = self._crear_tarjeta_sede(tarjetas_frame, "🏛️ Sede Sur", 2)
        self.btn_sur.grid(row=0, column=1, padx=8)

        # Preseleccionar visualmente la sede real de esta máquina (no es obligatorio,
        # pero ayuda a que el usuario vea de inmediato cuál es la opción correcta).
        self._seleccionar_sede(self.config_data["sede_id"])

        self.entry_user = ctk.CTkEntry(contenedor, placeholder_text="Usuario", width=260)
        self.entry_user.insert(0, USUARIO_DEMO)
        self.entry_user.pack(pady=(20, 8), padx=30)

        self.entry_pass = ctk.CTkEntry(contenedor, placeholder_text="Contraseña", show="•", width=260)
        self.entry_pass.insert(0, CLAVE_DEMO)
        self.entry_pass.pack(pady=(0, 8), padx=30)
        self.entry_pass.bind("<Return>", lambda e: self._intentar_login())

        ctk.CTkButton(
            contenedor, text="✨ Empezar turno", width=260,
            fg_color="#C9834E", hover_color="#A9683A",
            command=self._intentar_login
        ).pack(pady=(10, 6), padx=30)

        self.lbl_error = ctk.CTkLabel(
            contenedor, text="", text_color="#B23A3A",
            font=ctk.CTkFont(size=11, weight="bold"), wraplength=260, justify="center"
        )
        self.lbl_error.pack(pady=(0, 20), padx=30)

        ctk.CTkLabel(
            contenedor, text=f"Equipo detectado: {self.config_data['hostname_actual']}",
            font=ctk.CTkFont(size=10), text_color="#A9825D"
        ).pack(pady=(0, 16))

    def _crear_tarjeta_sede(self, master, texto, sede_id):
        return ctk.CTkButton(
            master, text=texto, width=120, height=70,
            fg_color="#F1E4D4", text_color="#4B2E1E", hover_color="#E4CBA8",
            command=lambda: self._seleccionar_sede(sede_id)
        )

    def _seleccionar_sede(self, sede_id):
        self.sede_elegida = sede_id
        activo, inactivo = "#C9834E", "#F1E4D4"
        self.btn_norte.configure(
            fg_color=activo if sede_id == 1 else inactivo,
            text_color="white" if sede_id == 1 else "#4B2E1E"
        )
        self.btn_sur.configure(
            fg_color=activo if sede_id == 2 else inactivo,
            text_color="white" if sede_id == 2 else "#4B2E1E"
        )
        # lbl_error todavía no existe la primera vez que se llama este método
        # (se usa también para preseleccionar la tarjeta antes de crear el label de error).
        if hasattr(self, "lbl_error"):
            self.lbl_error.configure(text="")

    def _intentar_login(self):
        usuario = self.entry_user.get().strip()
        clave = self.entry_pass.get().strip()

        if usuario != USUARIO_DEMO or clave != CLAVE_DEMO:
            self.lbl_error.configure(text="⚠️ Usuario o contraseña incorrectos")
            return

        # Regla clave: la sede elegida DEBE coincidir con la sede fija de esta máquina.
        if self.sede_elegida != self.config_data["sede_id"]:
            self.lbl_error.configure(
                text=f"⚠️ Esta máquina es '{self.config_data['sede_nombre']}'. "
                     f"No se puede iniciar turno en la otra sede desde aquí."
            )
            return

        self.on_login_success()

import customtkinter as ctk


class PaletteForgeWindow(ctk.CTk):

    def __init__(self):
        super().__init__()

        # -------------------------
        # Window Settings
        # -------------------------

        self.title("PaletteForge v0.1")

        self.geometry("1200x700")

        self.minsize(1000, 650)

        # -------------------------
        # Main Title
        # -------------------------

        self.title_label = ctk.CTkLabel(
            self,
            text="PaletteForge",
            font=("Arial", 34, "bold")
        )

        self.title_label.pack(pady=(25, 5))

        self.subtitle = ctk.CTkLabel(
            self,
            text="Pokemon Sprite Palette Editor",
            font=("Arial", 16)
        )

        self.subtitle.pack(pady=(0, 25))

        # -------------------------
        # Main Content
        # -------------------------

        self.content = ctk.CTkFrame(self)

        self.content.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=10
        )

        # Left Side
        self.left_panel = ctk.CTkFrame(self.content)

        self.left_panel.pack(
            side="left",
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        # Right Side
        self.right_panel = ctk.CTkFrame(self.content)

        self.right_panel.pack(
            side="right",
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        # -------------------------
        # Sprite A
        # -------------------------

        self.sprite_a_title = ctk.CTkLabel(
            self.left_panel,
            text="Sprite A",
            font=("Arial", 22, "bold")
        )

        self.sprite_a_title.pack(pady=(20, 10))

        self.load_a = ctk.CTkButton(
            self.left_panel,
            text="Load GIF A",
            width=180,
            height=40
        )

        self.load_a.pack(pady=10)

        self.preview_a = ctk.CTkLabel(
            self.left_panel,
            text="Preview Coming Soon",
            width=350,
            height=350,
            fg_color="#2B2D31",
            corner_radius=10
        )

        self.preview_a.pack(pady=20)

        # -------------------------
        # Sprite B
        # -------------------------

        self.sprite_b_title = ctk.CTkLabel(
            self.right_panel,
            text="Sprite B",
            font=("Arial", 22, "bold")
        )

        self.sprite_b_title.pack(pady=(20, 10))

        self.load_b = ctk.CTkButton(
            self.right_panel,
            text="Load GIF B",
            width=180,
            height=40
        )

        self.load_b.pack(pady=10)

        self.preview_b = ctk.CTkLabel(
            self.right_panel,
            text="Preview Coming Soon",
            width=350,
            height=350,
            fg_color="#2B2D31",
            corner_radius=10
        )

        self.preview_b.pack(pady=20)

        # -------------------------
        # Status Bar
        # -------------------------

        self.status = ctk.CTkLabel(
            self,
            text="Status: Waiting for sprites...",
            anchor="w",
            height=35
        )

        self.status.pack(
            fill="x",
            padx=20,
            pady=(0, 15)
        )
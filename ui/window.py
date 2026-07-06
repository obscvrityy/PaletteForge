import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageTk


class PaletteForgeWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("PaletteForge v0.1")
        self.geometry("1100x700")
        self.minsize(900, 600)

        self.loaded_image = None
        self.preview_image = None

        self.configure(fg_color="#111214")

        self.create_layout()

    def create_layout(self):
        # Main grid
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        self.grid_rowconfigure(0, weight=1)

        # Left sidebar
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color="#1E1F22", corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="PaletteForge",
            font=("Arial", 24, "bold"),
            text_color="#FFFFFF"
        )
        self.logo_label.pack(pady=(25, 10))

        self.version_label = ctk.CTkLabel(
            self.sidebar,
            text="Version 0.1",
            font=("Arial", 12),
            text_color="#B5BAC1"
        )
        self.version_label.pack(pady=(0, 25))

        self.load_button = ctk.CTkButton(
            self.sidebar,
            text="Load Sprite / GIF",
            command=self.load_image,
            height=40,
            fg_color="#5865F2",
            hover_color="#4752C4"
        )
        self.load_button.pack(padx=20, pady=10, fill="x")

        self.clear_button = ctk.CTkButton(
            self.sidebar,
            text="Clear Preview",
            command=self.clear_preview,
            height=40,
            fg_color="#2B2D31",
            hover_color="#383A40"
        )
        self.clear_button.pack(padx=20, pady=10, fill="x")

        # Center preview area
        self.preview_frame = ctk.CTkFrame(self, fg_color="#15161A", corner_radius=0)
        self.preview_frame.grid(row=0, column=1, sticky="nsew", padx=1)
        self.preview_frame.grid_columnconfigure(0, weight=1)
        self.preview_frame.grid_rowconfigure(0, weight=1)

        self.preview_label = ctk.CTkLabel(
            self.preview_frame,
            text="Load a sprite or GIF to begin",
            font=("Arial", 22, "bold"),
            text_color="#B5BAC1"
        )
        self.preview_label.grid(row=0, column=0)

        # Right inspector panel
        self.inspector = ctk.CTkFrame(self, width=260, fg_color="#1E1F22", corner_radius=0)
        self.inspector.grid(row=0, column=2, sticky="nsew")
        self.inspector.grid_propagate(False)

        self.inspector_title = ctk.CTkLabel(
            self.inspector,
            text="Palette Inspector",
            font=("Arial", 20, "bold"),
            text_color="#FFFFFF"
        )
        self.inspector_title.pack(pady=(25, 10))

        self.file_info_label = ctk.CTkLabel(
            self.inspector,
            text="No file loaded",
            font=("Arial", 13),
            text_color="#B5BAC1",
            wraplength=220,
            justify="left"
        )
        self.file_info_label.pack(padx=20, pady=10, anchor="w")

    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Sprite or GIF",
            filetypes=[
                ("Image files", "*.png *.gif *.jpg *.jpeg *.webp"),
                ("PNG files", "*.png"),
                ("GIF files", "*.gif"),
                ("All files", "*.*")
            ]
        )

        if not file_path:
            return

        image = Image.open(file_path)
        self.loaded_image = image

        display_image = image.copy()
        display_image.thumbnail((500, 500), Image.Resampling.NEAREST)

        self.preview_image = ImageTk.PhotoImage(display_image)

        self.preview_label.configure(
            image=self.preview_image,
            text=""
        )

        file_name = file_path.split("/")[-1]

        self.file_info_label.configure(
            text=(
                f"Loaded File:\n{file_name}\n\n"
                f"Size:\n{image.width} x {image.height}\n\n"
                f"Mode:\n{image.mode}\n\n"
                f"Format:\n{image.format}"
            )
        )

    def clear_preview(self):
        self.loaded_image = None
        self.preview_image = None

        self.preview_label.configure(
            image=None,
            text="Load a sprite or GIF to begin"
        )

        self.file_info_label.configure(text="No file loaded")
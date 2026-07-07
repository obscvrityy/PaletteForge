import os
import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageTk

from core.swapper import PaletteMatcher
from core.renderer import PaletteRenderer
from core.segmentation import SpriteSegmenter


class PaletteForgeWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("PaletteForge v0.3.0 — Professional UI Foundation")
        self.geometry("1480x860")
        self.minsize(1200, 760)

        self.source_image = None
        self.target_image = None

        self.source_preview_image = None
        self.target_preview_image = None

        self.source_frames = []
        self.source_durations = []
        self.target_frames = []
        self.target_durations = []

        self.source_frame_index = 0
        self.target_frame_index = 0

        self.source_animation_job = None
        self.target_animation_job = None

        self.source_palette_colors = []
        self.target_palette_colors = []

        self.source_palette_widgets = []
        self.target_palette_widgets = []

        self.palette_mapping = []
        self.mapping_widgets = []
        self.mapping_controls = []

        self.original_source_title_text = "SOURCE"
        self.swapped_preview_frames = []
        self.swapped_preview_durations = []
        self.swapped_preview_index = 0
        self.swapped_preview_job = None
        self.is_showing_swapped_preview = False

        self.configure(fg_color="#060B18")

        self.create_layout()

    def create_layout(self):
        # PaletteForge v0.3.0 Professional Workspace UI Foundation
        # Dark purple/blue creator-studio layout inspired by the v1.0 UI direction.
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        self.theme = {
            "bg": "#060B18",
            "surface": "#0B1224",
            "surface_2": "#101A32",
            "surface_3": "#15213D",
            "border": "#22345E",
            "primary": "#5B4BFF",
            "primary_hover": "#3F35D6",
            "blue": "#2F80FF",
            "blue_hover": "#2567CC",
            "cyan": "#38D9FF",
            "text": "#F5F7FF",
            "muted": "#9FB0D1",
            "dim": "#647391",
            "success": "#31D0AA",
        }

        # Top app bar
        self.topbar = ctk.CTkFrame(
            self,
            height=58,
            fg_color=self.theme["surface"],
            corner_radius=0,
            border_width=1,
            border_color=self.theme["border"]
        )
        self.topbar.grid(row=0, column=0, columnspan=3, sticky="nsew")
        self.topbar.grid_propagate(False)
        self.topbar.grid_columnconfigure(3, weight=1)

        self.logo_badge = ctk.CTkLabel(
            self.topbar,
            text="PF",
            width=36,
            height=36,
            fg_color="#111B35",
            corner_radius=8,
            font=("Arial", 16, "bold"),
            text_color=self.theme["cyan"]
        )
        self.logo_badge.grid(row=0, column=0, padx=(14, 8), pady=10)

        self.logo_label = ctk.CTkLabel(
            self.topbar,
            text="PaletteForge",
            font=("Arial", 24, "bold"),
            text_color=self.theme["text"]
        )
        self.logo_label.grid(row=0, column=1, padx=(0, 18), pady=10, sticky="w")

        self.version_pill = ctk.CTkLabel(
            self.topbar,
            text="v0.3.0 UI Foundation",
            height=28,
            fg_color="#121C39",
            corner_radius=14,
            font=("Arial", 11, "bold"),
            text_color=self.theme["muted"]
        )
        self.version_pill.grid(row=0, column=2, padx=(0, 20), pady=14, sticky="w")

        menu_frame = ctk.CTkFrame(self.topbar, fg_color="transparent")
        menu_frame.grid(row=0, column=3, pady=10, sticky="w")
        for label in ["File", "Edit", "Sprite", "Palette", "View", "Window", "Help"]:
            ctk.CTkLabel(
                menu_frame,
                text=label,
                font=("Arial", 13),
                text_color=self.theme["muted"]
            ).pack(side="left", padx=12)

        self.topbar_status = ctk.CTkLabel(
            self.topbar,
            text="Professional Creator Workspace",
            font=("Arial", 12),
            text_color=self.theme["dim"]
        )
        self.topbar_status.grid(row=0, column=4, padx=(20, 18), sticky="e")

        # Left library / import panel
        self.sidebar = ctk.CTkFrame(
            self,
            width=280,
            fg_color=self.theme["surface"],
            corner_radius=0,
            border_width=1,
            border_color=self.theme["border"]
        )
        self.sidebar.grid(row=1, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        ctk.CTkLabel(
            self.sidebar,
            text="LIBRARY",
            font=("Arial", 12, "bold"),
            text_color=self.theme["dim"]
        ).pack(padx=18, pady=(18, 8), anchor="w")

        self.load_source_button = ctk.CTkButton(
            self.sidebar,
            text="＋  Load Source Image / GIF",
            command=lambda: self.load_image("source"),
            height=38,
            fg_color=self.theme["primary"],
            hover_color=self.theme["primary_hover"],
            text_color="#FFFFFF",
            corner_radius=10
        )
        self.load_source_button.pack(padx=16, pady=(0, 8), fill="x")

        self.load_target_button = ctk.CTkButton(
            self.sidebar,
            text="＋  Load Target Image / GIF",
            command=lambda: self.load_image("target"),
            height=38,
            fg_color=self.theme["blue"],
            hover_color=self.theme["blue_hover"],
            text_color="#FFFFFF",
            corner_radius=10
        )
        self.load_target_button.pack(padx=16, pady=8, fill="x")

        library_card = ctk.CTkFrame(
            self.sidebar,
            fg_color=self.theme["surface_2"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme["border"]
        )
        library_card.pack(padx=16, pady=(8, 14), fill="x")

        for icon, label, count in [
            ("▣", "All Sprites", "—"),
            ("◫", "Animations", "—"),
            ("◇", "Materials", "—"),
            ("✦", "Palette Presets", "Soon"),
        ]:
            row = ctk.CTkFrame(library_card, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=6)
            ctk.CTkLabel(row, text=icon, width=24, text_color=self.theme["cyan"], font=("Arial", 14, "bold")).pack(side="left")
            ctk.CTkLabel(row, text=label, text_color=self.theme["text"], font=("Arial", 12)).pack(side="left", padx=6)
            ctk.CTkLabel(row, text=count, text_color=self.theme["dim"], font=("Arial", 11)).pack(side="right")

        # Source palette card
        source_palette_card = ctk.CTkFrame(
            self.sidebar,
            fg_color=self.theme["surface_2"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme["border"]
        )
        source_palette_card.pack(padx=16, pady=(0, 12), fill="both", expand=True)

        source_header = ctk.CTkFrame(source_palette_card, fg_color="transparent")
        source_header.pack(fill="x", padx=12, pady=(12, 2))
        self.source_palette_title = ctk.CTkLabel(
            source_header,
            text="Source Palette",
            font=("Arial", 14, "bold"),
            text_color=self.theme["text"]
        )
        self.source_palette_title.pack(side="left")
        self.source_palette_count_label = ctk.CTkLabel(
            source_header,
            text="0 colors",
            font=("Arial", 11),
            text_color=self.theme["dim"]
        )
        self.source_palette_count_label.pack(side="right")

        self.source_palette_scroll = ctk.CTkScrollableFrame(
            source_palette_card,
            width=240,
            height=135,
            fg_color="#0A1022",
            corner_radius=10
        )
        self.source_palette_scroll.pack(padx=12, pady=(6, 12), fill="both", expand=True)

        # Target palette card
        target_palette_card = ctk.CTkFrame(
            self.sidebar,
            fg_color=self.theme["surface_2"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme["border"]
        )
        target_palette_card.pack(padx=16, pady=(0, 16), fill="both", expand=True)

        target_header = ctk.CTkFrame(target_palette_card, fg_color="transparent")
        target_header.pack(fill="x", padx=12, pady=(12, 2))
        self.target_palette_title = ctk.CTkLabel(
            target_header,
            text="Target Palette",
            font=("Arial", 14, "bold"),
            text_color=self.theme["text"]
        )
        self.target_palette_title.pack(side="left")
        self.target_palette_count_label = ctk.CTkLabel(
            target_header,
            text="0 colors",
            font=("Arial", 11),
            text_color=self.theme["dim"]
        )
        self.target_palette_count_label.pack(side="right")

        self.target_palette_scroll = ctk.CTkScrollableFrame(
            target_palette_card,
            width=240,
            height=135,
            fg_color="#0A1022",
            corner_radius=10
        )
        self.target_palette_scroll.pack(padx=12, pady=(6, 12), fill="both", expand=True)

        # Center workspace
        self.preview_frame = ctk.CTkFrame(
            self,
            fg_color=self.theme["bg"],
            corner_radius=0
        )
        self.preview_frame.grid(row=1, column=1, sticky="nsew", padx=0, pady=0)
        self.preview_frame.grid_columnconfigure(0, weight=1)
        self.preview_frame.grid_rowconfigure(1, weight=1)
        self.preview_frame.grid_rowconfigure(2, weight=0)

        # Action toolbar
        toolbar = ctk.CTkFrame(
            self.preview_frame,
            height=58,
            fg_color=self.theme["surface"],
            corner_radius=0,
            border_width=1,
            border_color=self.theme["border"]
        )
        toolbar.grid(row=0, column=0, sticky="nsew")
        toolbar.grid_propagate(False)
        toolbar.grid_columnconfigure(7, weight=1)

        toolbar_buttons = [
            ("⚡ Smart Match", self.auto_match_palettes, self.theme["primary"], self.theme["primary_hover"]),
            ("🧩 Analyze Sprite", self.analyze_sprite_regions, self.theme["blue"], self.theme["blue_hover"]),
            ("▶ Live Preview", self.render_live_swap_preview, "#2947B8", "#203B99"),
            ("↩ Show Original", self.restore_source_preview, self.theme["surface_3"], self.theme["border"]),
            ("✓ Apply Mapping", self.apply_manual_mapping, "#2451D6", "#1E41A8"),
            ("⬇ Export GIF", self.export_swapped_gif, "#226EEA", "#1D5DC5"),
        ]

        for col, (text, command, fg, hover) in enumerate(toolbar_buttons):
            ctk.CTkButton(
                toolbar,
                text=text,
                command=command,
                height=34,
                fg_color=fg,
                hover_color=hover,
                corner_radius=9,
                font=("Arial", 12, "bold")
            ).grid(row=0, column=col, padx=(12 if col == 0 else 4, 4), pady=12, sticky="w")

        self.pixel_pill = ctk.CTkLabel(
            toolbar,
            text="Pixel Perfect  ●  400%",
            height=32,
            fg_color="#101C3B",
            corner_radius=16,
            text_color=self.theme["cyan"],
            font=("Arial", 12, "bold")
        )
        self.pixel_pill.grid(row=0, column=8, padx=(6, 18), pady=12, sticky="e")

        # Preview comparison area
        comparison_area = ctk.CTkFrame(self.preview_frame, fg_color=self.theme["bg"], corner_radius=0)
        comparison_area.grid(row=1, column=0, sticky="nsew", padx=14, pady=14)
        comparison_area.grid_columnconfigure(0, weight=1)
        comparison_area.grid_columnconfigure(1, weight=1)
        comparison_area.grid_rowconfigure(0, weight=1)

        self.source_panel = ctk.CTkFrame(
            comparison_area,
            fg_color=self.theme["surface_2"],
            corner_radius=14,
            border_width=1,
            border_color=self.theme["border"]
        )
        self.source_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.source_panel.grid_columnconfigure(0, weight=1)
        self.source_panel.grid_rowconfigure(1, weight=1)

        source_header_frame = ctk.CTkFrame(self.source_panel, fg_color="transparent")
        source_header_frame.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 6))
        source_header_frame.grid_columnconfigure(1, weight=1)
        self.source_title = ctk.CTkLabel(
            source_header_frame,
            text="BEFORE / SOURCE",
            font=("Arial", 14, "bold"),
            text_color=self.theme["text"]
        )
        self.source_title.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            source_header_frame,
            text="Image / GIF",
            height=24,
            fg_color="#0A1022",
            corner_radius=12,
            text_color=self.theme["muted"],
            font=("Arial", 10, "bold")
        ).grid(row=0, column=2, sticky="e")

        self.source_canvas = ctk.CTkFrame(
            self.source_panel,
            fg_color="#0A1022",
            corner_radius=12,
            border_width=1,
            border_color="#1A2A50"
        )
        self.source_canvas.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self.source_canvas.grid_columnconfigure(0, weight=1)
        self.source_canvas.grid_rowconfigure(0, weight=1)

        self.source_preview_label = ctk.CTkLabel(
            self.source_canvas,
            text="\nDrop or load a source image / GIF",
            font=("Arial", 18, "bold"),
            text_color=self.theme["muted"]
        )
        self.source_preview_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.target_panel = ctk.CTkFrame(
            comparison_area,
            fg_color=self.theme["surface_2"],
            corner_radius=14,
            border_width=1,
            border_color=self.theme["border"]
        )
        self.target_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self.target_panel.grid_columnconfigure(0, weight=1)
        self.target_panel.grid_rowconfigure(1, weight=1)

        target_header_frame = ctk.CTkFrame(self.target_panel, fg_color="transparent")
        target_header_frame.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 6))
        target_header_frame.grid_columnconfigure(1, weight=1)
        self.target_title = ctk.CTkLabel(
            target_header_frame,
            text="AFTER / TARGET",
            font=("Arial", 14, "bold"),
            text_color=self.theme["cyan"]
        )
        self.target_title.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            target_header_frame,
            text="Preview",
            height=24,
            fg_color="#0A1022",
            corner_radius=12,
            text_color=self.theme["muted"],
            font=("Arial", 10, "bold")
        ).grid(row=0, column=2, sticky="e")

        self.target_canvas = ctk.CTkFrame(
            self.target_panel,
            fg_color="#0A1022",
            corner_radius=12,
            border_width=1,
            border_color="#1A2A50"
        )
        self.target_canvas.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self.target_canvas.grid_columnconfigure(0, weight=1)
        self.target_canvas.grid_rowconfigure(0, weight=1)

        self.target_preview_label = ctk.CTkLabel(
            self.target_canvas,
            text="\nDrop or load a target image / GIF",
            font=("Arial", 18, "bold"),
            text_color=self.theme["muted"]
        )
        self.target_preview_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Bottom mapping/editor panel
        self.mapping_panel = ctk.CTkFrame(
            self.preview_frame,
            height=220,
            fg_color=self.theme["surface"],
            corner_radius=14,
            border_width=1,
            border_color=self.theme["border"]
        )
        self.mapping_panel.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self.mapping_panel.grid_propagate(False)
        self.mapping_panel.grid_columnconfigure(0, weight=1)
        self.mapping_panel.grid_rowconfigure(1, weight=1)

        mapping_header = ctk.CTkFrame(self.mapping_panel, fg_color="transparent")
        mapping_header.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 4))
        mapping_header.grid_columnconfigure(4, weight=1)

        for i, label in enumerate(["PALETTE MAP", "SWATCHES", "RAMP EDITOR", "ANALYSIS"]):
            active = i == 0
            ctk.CTkLabel(
                mapping_header,
                text=label,
                height=28,
                fg_color=self.theme["primary"] if active else "transparent",
                corner_radius=8,
                text_color="#FFFFFF" if active else self.theme["muted"],
                font=("Arial", 11, "bold")
            ).grid(row=0, column=i, padx=(0, 8), sticky="w")

        self.mapping_count_label = ctk.CTkLabel(
            mapping_header,
            text="0 matches",
            font=("Arial", 11),
            text_color=self.theme["dim"]
        )
        self.mapping_count_label.grid(row=0, column=5, sticky="e")

        self.mapping_scroll = ctk.CTkScrollableFrame(
            self.mapping_panel,
            fg_color="#0A1022",
            corner_radius=10
        )
        self.mapping_scroll.grid(row=1, column=0, sticky="nsew", padx=14, pady=(4, 14))

        # Right inspector panel
        self.inspector = ctk.CTkFrame(
            self,
            width=340,
            fg_color=self.theme["surface"],
            corner_radius=0,
            border_width=1,
            border_color=self.theme["border"]
        )
        self.inspector.grid(row=1, column=2, sticky="nsew")
        self.inspector.grid_propagate(False)

        ctk.CTkLabel(
            self.inspector,
            text="SMART MATCH ANALYSIS",
            font=("Arial", 12, "bold"),
            text_color=self.theme["dim"]
        ).pack(padx=18, pady=(18, 8), anchor="w")

        smart_card = ctk.CTkFrame(
            self.inspector,
            fg_color=self.theme["surface_2"],
            corner_radius=14,
            border_width=1,
            border_color=self.theme["border"]
        )
        smart_card.pack(padx=16, pady=(0, 12), fill="x")

        ctk.CTkLabel(
            smart_card,
            text="92%",
            font=("Arial", 34, "bold"),
            text_color=self.theme["cyan"]
        ).pack(pady=(16, 0))
        ctk.CTkLabel(
            smart_card,
            text="Match confidence placeholder\nupdates with future engine passes",
            font=("Arial", 11),
            justify="center",
            text_color=self.theme["muted"]
        ).pack(padx=14, pady=(0, 16))

        ctk.CTkLabel(
            self.inspector,
            text="SPRITE INSPECTOR",
            font=("Arial", 12, "bold"),
            text_color=self.theme["dim"]
        ).pack(padx=18, pady=(2, 8), anchor="w")

        info_card = ctk.CTkFrame(
            self.inspector,
            fg_color=self.theme["surface_2"],
            corner_radius=14,
            border_width=1,
            border_color=self.theme["border"]
        )
        info_card.pack(padx=16, pady=(0, 12), fill="both", expand=True)

        self.file_info_label = ctk.CTkLabel(
            info_card,
            text="Load a source and target image/GIF to begin.",
            font=("Arial", 12),
            text_color=self.theme["muted"],
            wraplength=280,
            justify="left"
        )
        self.file_info_label.pack(padx=14, pady=14, anchor="nw", fill="both", expand=True)

        ctk.CTkLabel(
            self.inspector,
            text="RESIZE & EXPORT",
            font=("Arial", 12, "bold"),
            text_color=self.theme["dim"]
        ).pack(padx=18, pady=(2, 8), anchor="w")

        resize_card = ctk.CTkFrame(
            self.inspector,
            fg_color=self.theme["surface_2"],
            corner_radius=14,
            border_width=1,
            border_color=self.theme["border"]
        )
        resize_card.pack(padx=16, pady=(0, 16), fill="x")

        ctk.CTkLabel(
            resize_card,
            text="Image + GIF Resizer is next after Smart Match Pass 1.",
            wraplength=280,
            justify="left",
            font=("Arial", 12),
            text_color=self.theme["muted"]
        ).pack(padx=14, pady=(14, 8), anchor="w")

        self.clear_button = ctk.CTkButton(
            resize_card,
            text="Clear Workspace",
            command=self.clear_all,
            height=34,
            fg_color=self.theme["surface_3"],
            hover_color=self.theme["border"],
            corner_radius=9
        )
        self.clear_button.pack(padx=14, pady=(4, 14), fill="x")

        # Bottom status bar
        self.status_bar = ctk.CTkFrame(
            self,
            height=34,
            fg_color="#050A15",
            corner_radius=0,
            border_width=1,
            border_color=self.theme["border"]
        )
        self.status_bar.grid(row=2, column=0, columnspan=3, sticky="nsew")
        self.status_bar.grid_propagate(False)
        self.status_bar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self.status_bar,
            text="✦",
            font=("Arial", 14, "bold"),
            text_color=self.theme["cyan"]
        ).grid(row=0, column=0, padx=(14, 6), pady=6, sticky="w")

        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Status: Ready",
            font=("Arial", 12),
            text_color=self.theme["muted"],
            anchor="w"
        )
        self.status_label.grid(row=0, column=1, padx=4, pady=6, sticky="ew")

        ctk.CTkLabel(
            self.status_bar,
            text="RGBA  •  Indexed Palette  •  GIF/Image Support",
            font=("Arial", 11),
            text_color=self.theme["dim"]
        ).grid(row=0, column=2, padx=(8, 14), pady=6, sticky="e")

    def load_image(self, slot):
        file_path = filedialog.askopenfilename(
            title=f"Select {slot.title()} Sprite or GIF",
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

        if slot == "source":
            self.clear_slot("source")
            self.source_title.configure(text=self.original_source_title_text)
            self.source_image = image
            self.load_preview(image, "source")
            self.source_palette_colors = self.extract_palette(image)
            self.display_palette(self.source_palette_colors, "source")
        else:
            self.clear_slot("target")
            self.target_image = image
            self.load_preview(image, "target")
            self.target_palette_colors = self.extract_palette(image)
            self.display_palette(self.target_palette_colors, "target")

        self.clear_mapping_display()
        self.update_file_info()

    def load_preview(self, image, slot):
        is_animated = bool(getattr(image, "is_animated", False))

        if image.format == "GIF" and is_animated:
            self.load_animated_preview(image, slot)
        else:
            display_image = image.copy().convert("RGBA")
            display_image.thumbnail((500, 500), Image.Resampling.NEAREST)

            preview = ImageTk.PhotoImage(display_image)

            if slot == "source":
                self.source_preview_image = preview
                self.source_preview_label.configure(image=self.source_preview_image, text="")
            else:
                self.target_preview_image = preview
                self.target_preview_label.configure(image=self.target_preview_image, text="")

    def load_animated_preview(self, image, slot):
        frames = []
        durations = []

        for frame_index in range(image.n_frames):
            image.seek(frame_index)

            frame = image.copy().convert("RGBA")
            frame.thumbnail((500, 500), Image.Resampling.NEAREST)

            frames.append(ImageTk.PhotoImage(frame))
            durations.append(image.info.get("duration", 100))

        if slot == "source":
            self.source_frames = frames
            self.source_durations = durations
            self.source_frame_index = 0
            self.animate_source()
        else:
            self.target_frames = frames
            self.target_durations = durations
            self.target_frame_index = 0
            self.animate_target()

    def animate_source(self):
        if not self.source_frames:
            return

        self.source_preview_label.configure(
            image=self.source_frames[self.source_frame_index],
            text=""
        )

        delay = self.source_durations[self.source_frame_index]
        self.source_frame_index = (self.source_frame_index + 1) % len(self.source_frames)

        self.source_animation_job = self.after(delay, self.animate_source)

    def animate_target(self):
        if not self.target_frames:
            return

        self.target_preview_label.configure(
            image=self.target_frames[self.target_frame_index],
            text=""
        )

        delay = self.target_durations[self.target_frame_index]
        self.target_frame_index = (self.target_frame_index + 1) % len(self.target_frames)

        self.target_animation_job = self.after(delay, self.animate_target)

    def stop_source_animation(self):
        if self.source_animation_job is not None:
            self.after_cancel(self.source_animation_job)
            self.source_animation_job = None

    def stop_target_animation(self):
        if self.target_animation_job is not None:
            self.after_cancel(self.target_animation_job)
            self.target_animation_job = None

    def extract_palette(self, image, max_colors=24):
        color_counts = {}
        frame_count = getattr(image, "n_frames", 1)

        for frame_index in range(frame_count):
            try:
                image.seek(frame_index)
            except EOFError:
                break

            frame = image.copy().convert("RGBA")

            for pixel in frame.getdata():
                r, g, b, a = pixel

                if a == 0:
                    continue

                rgb = (r, g, b)
                color_counts[rgb] = color_counts.get(rgb, 0) + 1

        sorted_colors = sorted(
            color_counts.items(),
            key=lambda item: item[1],
            reverse=True
        )

        return sorted_colors[:max_colors]

    def display_palette(self, colors, slot):
        self.clear_palette_display(slot)

        if slot == "source":
            parent = self.source_palette_scroll
            widgets = self.source_palette_widgets
            self.source_palette_count_label.configure(text=f"{len(colors)} colors shown")
        else:
            parent = self.target_palette_scroll
            widgets = self.target_palette_widgets
            self.target_palette_count_label.configure(text=f"{len(colors)} colors shown")

        if not colors:
            empty_label = ctk.CTkLabel(
                parent,
                text="No colors detected",
                text_color="#9FB0D1"
            )
            empty_label.pack(pady=10)
            widgets.append(empty_label)
            return

        for index, (rgb, count) in enumerate(colors, start=1):
            hex_color = "#{:02X}{:02X}{:02X}".format(*rgb)

            row = ctk.CTkFrame(
                parent,
                fg_color="#101A32",
                corner_radius=6
            )
            row.pack(fill="x", padx=6, pady=3)

            swatch = ctk.CTkFrame(
                row,
                width=28,
                height=28,
                fg_color=hex_color,
                corner_radius=4
            )
            swatch.pack(side="left", padx=(7, 8), pady=7)
            swatch.pack_propagate(False)

            label = ctk.CTkLabel(
                row,
                text=f"{index:02d}  {hex_color}\n{count} px",
                font=("Arial", 10),
                text_color="#FFFFFF",
                justify="left"
            )
            label.pack(side="left", anchor="w")

            widgets.append(row)


    def auto_match_palettes(self):
        if not self.source_palette_colors or not self.target_palette_colors:
            self.set_status("Load both images/GIFs first")
            self.file_info_label.configure(
                text="Auto Match needs both a source palette and a target palette."
            )
            return

        matcher = PaletteMatcher(
            self.source_palette_colors,
            self.target_palette_colors,
            source_image=self.source_image,
            target_image=self.target_image
        )

        mapping = matcher.auto_match()
        self.palette_mapping = mapping[:]

        self.display_mapping(mapping)
        self.mapping_count_label.configure(text=f"{len(mapping)} matches")
        self.set_status(f"Pokémon smart matched {len(mapping)} colors")
        self.update_file_info()

    def display_mapping(self, mapping):
        self.clear_mapping_display(clear_data=False)

        if not mapping:
            empty_label = ctk.CTkLabel(
                self.mapping_scroll,
                text="No matches yet",
                text_color="#9FB0D1"
            )
            empty_label.pack(pady=10)
            self.mapping_widgets.append(empty_label)
            self.mapping_count_label.configure(text="0 matches")
            return

        target_options = self.get_target_palette_hex_options()

        for index, entry in enumerate(mapping, start=1):
            source_hex = entry["source_hex"]
            target_hex = entry["target_hex"]

            row = ctk.CTkFrame(
                self.mapping_scroll,
                fg_color="#101A32",
                corner_radius=6
            )
            row.pack(fill="x", padx=6, pady=3)

            number_label = ctk.CTkLabel(
                row,
                text=f"{index:02d}",
                font=("Arial", 10, "bold"),
                text_color="#9FB0D1",
                width=28
            )
            number_label.pack(side="left", padx=(6, 4), pady=7)

            source_swatch = ctk.CTkFrame(
                row,
                width=22,
                height=22,
                fg_color=source_hex,
                corner_radius=4
            )
            source_swatch.pack(side="left", padx=3, pady=7)
            source_swatch.pack_propagate(False)

            arrow_label = ctk.CTkLabel(
                row,
                text="→",
                font=("Arial", 13, "bold"),
                text_color="#FFFFFF",
                width=18
            )
            arrow_label.pack(side="left", padx=2)

            target_swatch = ctk.CTkFrame(
                row,
                width=22,
                height=22,
                fg_color=target_hex,
                corner_radius=4
            )
            target_swatch.pack(side="left", padx=3, pady=7)
            target_swatch.pack_propagate(False)

            values = target_options if target_options else [target_hex]

            target_menu = ctk.CTkOptionMenu(
                row,
                values=values,
                width=105,
                height=26,
                fg_color="#15213D",
                button_color="#22345E",
                button_hover_color="#3B82F6",
                command=lambda selected_hex, mapping_index=index - 1, swatch=target_swatch: self.update_mapping_target(
                    mapping_index,
                    selected_hex,
                    swatch
                )
            )
            target_menu.set(target_hex)
            target_menu.pack(side="left", padx=(6, 4), anchor="w")

            self.mapping_widgets.append(row)
            self.mapping_controls.append(target_menu)

        self.mapping_count_label.configure(text=f"{len(mapping)} matches")

    def get_target_palette_hex_options(self):
        options = []

        for item in self.target_palette_colors:
            if isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], tuple):
                rgb = item[0]
            else:
                rgb = item

            if isinstance(rgb, tuple) and len(rgb) >= 3:
                options.append("#{:02X}{:02X}{:02X}".format(
                    int(rgb[0]),
                    int(rgb[1]),
                    int(rgb[2])
                ))

        return options

    def update_mapping_target(self, mapping_index, selected_hex, target_swatch):
        if mapping_index < 0 or mapping_index >= len(self.palette_mapping):
            return

        target_rgb = self.hex_to_rgb(selected_hex)

        self.palette_mapping[mapping_index]["target_hex"] = selected_hex
        self.palette_mapping[mapping_index]["target_rgb"] = target_rgb

        target_swatch.configure(fg_color=selected_hex)
        self.set_status("Manual mapping updated")

    def apply_manual_mapping(self):
        if not self.palette_mapping:
            self.set_status("Create a mapping first")
            return

        self.render_live_swap_preview()

    def analyze_sprite_regions(self):
        if self.source_image is None:
            self.set_status("Load a source image/GIF first")
            return

        segmenter = SpriteSegmenter(self.source_image)
        report = segmenter.analyze()

        total_regions = report.get("total_regions", 0)
        largest_regions = report.get("largest_regions", [])
        material_summary = report.get("material_summary", {})
        graph_summary = report.get("graph_summary", {})

        lines = [
            "Pokémon Smart Match Analysis:",
            f"Regions detected: {total_regions}",
            f"Graph links: {graph_summary.get('edge_count', 0)}",
            "",
            "Materials:"
        ]

        if material_summary:
            for material, count in material_summary.items():
                lines.append(f"{material}: {count}")
        else:
            lines.append("No material summary available.")

        lines.extend(["", "Largest regions:"])

        if not largest_regions:
            lines.append("No regions detected.")
        else:
            for region in largest_regions[:8]:
                lines.append(
                    f"{region['label']} • {region['pixel_count']} px • "
                    f"{region['dominant_hex']} • {region['likely_role']}"
                )

        self.file_info_label.configure(text="\n".join(lines))
        self.set_status(f"Detected {total_regions} regions")

    def export_swapped_gif(self):
        if self.source_image is None:
            self.set_status("Load a source image/GIF first")
            return

        if not self.palette_mapping:
            self.auto_match_palettes()

        if not self.palette_mapping:
            self.set_status("Create a mapping first")
            return

        save_path = filedialog.asksaveasfilename(
            title="Export Swapped GIF",
            defaultextension=".gif",
            filetypes=[
                ("GIF files", "*.gif"),
                ("All files", "*.*")
            ]
        )

        if not save_path:
            self.set_status("Export cancelled")
            return

        renderer = PaletteRenderer(self.palette_mapping)
        rendered_frames, durations = renderer.render_gif_frames(self.source_image)

        if not rendered_frames:
            self.set_status("Export failed: no frames rendered")
            return

        export_frames = []

        for frame in rendered_frames:
            export_frames.append(frame.convert("RGBA"))

        first_frame = export_frames[0]
        remaining_frames = export_frames[1:]

        first_frame.save(
            save_path,
            save_all=True,
            append_images=remaining_frames,
            duration=durations,
            loop=0,
            disposal=2,
            transparency=0
        )

        self.set_status("GIF exported successfully")

    def hex_to_rgb(self, hex_color):
        clean_hex = hex_color.replace("#", "")
        return (
            int(clean_hex[0:2], 16),
            int(clean_hex[2:4], 16),
            int(clean_hex[4:6], 16)
        )

    def render_live_swap_preview(self):
        if self.source_image is None:
            self.set_status("Load a source image/GIF first")
            return

        if not self.palette_mapping:
            self.auto_match_palettes()

        if not self.palette_mapping:
            self.set_status("Create a mapping first")
            return

        self.stop_swapped_preview_animation()

        renderer = PaletteRenderer(self.palette_mapping)
        rendered_frames, durations = renderer.render_gif_frames(self.source_image)

        self.swapped_preview_frames = []
        self.swapped_preview_durations = durations
        self.swapped_preview_index = 0

        for frame in rendered_frames:
            display_frame = frame.copy().convert("RGBA")
            display_frame.thumbnail((500, 500), Image.Resampling.NEAREST)
            self.swapped_preview_frames.append(ImageTk.PhotoImage(display_frame))

        if not self.swapped_preview_frames:
            self.set_status("Could not render preview")
            return

        self.stop_source_animation()
        self.source_title.configure(text="LIVE SWAP PREVIEW")
        self.is_showing_swapped_preview = True
        self.animate_swapped_preview()
        self.set_status(f"Live preview rendered ({len(self.swapped_preview_frames)} frames)")

    def animate_swapped_preview(self):
        if not self.swapped_preview_frames:
            return

        self.source_preview_label.configure(
            image=self.swapped_preview_frames[self.swapped_preview_index],
            text=""
        )

        delay = self.swapped_preview_durations[self.swapped_preview_index]
        self.swapped_preview_index = (self.swapped_preview_index + 1) % len(self.swapped_preview_frames)

        self.swapped_preview_job = self.after(delay, self.animate_swapped_preview)

    def stop_swapped_preview_animation(self):
        if self.swapped_preview_job is not None:
            self.after_cancel(self.swapped_preview_job)
            self.swapped_preview_job = None

    def restore_source_preview(self):
        self.stop_swapped_preview_animation()
        self.is_showing_swapped_preview = False
        self.source_title.configure(text=self.original_source_title_text)

        if self.source_frames:
            self.source_frame_index = 0
            self.animate_source()
            self.set_status("Original source restored")
        elif self.source_preview_image is not None:
            self.source_preview_label.configure(image=self.source_preview_image, text="")
            self.set_status("Original source restored")
        else:
            self.source_preview_label.configure(image=None, text="\nLoad source image/GIF")
            self.set_status("Ready")

    def clear_mapping_display(self, clear_data=True):
        for widget in self.mapping_widgets:
            widget.destroy()

        self.mapping_widgets = []
        self.mapping_controls = []

        if clear_data:
            self.palette_mapping = []
            self.mapping_count_label.configure(text="0 matches")

    def clear_palette_display(self, slot):
        if slot == "source":
            for widget in self.source_palette_widgets:
                widget.destroy()

            self.source_palette_widgets = []
            self.source_palette_count_label.configure(text="0 colors")
        else:
            for widget in self.target_palette_widgets:
                widget.destroy()

            self.target_palette_widgets = []
            self.target_palette_count_label.configure(text="0 colors")

    def clear_slot(self, slot):
        if slot == "source":
            self.stop_source_animation()
            self.stop_swapped_preview_animation()
            self.is_showing_swapped_preview = False
            self.source_title.configure(text=self.original_source_title_text)
            self.source_image = None
            self.source_preview_image = None
            self.source_frames = []
            self.source_durations = []
            self.source_frame_index = 0
            self.source_palette_colors = []
            self.swapped_preview_frames = []
            self.swapped_preview_durations = []
            self.swapped_preview_index = 0
            self.source_preview_label.configure(image=None, text="\nLoad source image/GIF")
            self.clear_palette_display("source")
        else:
            self.stop_target_animation()
            self.target_image = None
            self.target_preview_image = None
            self.target_frames = []
            self.target_durations = []
            self.target_frame_index = 0
            self.target_palette_colors = []
            self.target_preview_label.configure(image=None, text="\nLoad target image/GIF")
            self.clear_palette_display("target")

    def clear_all(self):
        self.clear_slot("source")
        self.clear_slot("target")
        self.clear_mapping_display()
        self.file_info_label.configure(text="Load a source and target image/GIF to begin.")
        self.set_status("Ready")

    def update_file_info(self):
        source_text = "Source: Not loaded"
        target_text = "Target: Not loaded"
        mapping_text = "Mapping: Not matched"

        if self.source_image is not None:
            source_frames = getattr(self.source_image, "n_frames", 1)
            source_text = (
                f"Source:\n"
                f"{self.source_image.format} • {self.source_image.width}x{self.source_image.height}\n"
                f"Frames: {source_frames}\n"
                f"Colors: {len(self.source_palette_colors)} shown"
            )

        if self.target_image is not None:
            target_frames = getattr(self.target_image, "n_frames", 1)
            target_text = (
                f"Target:\n"
                f"{self.target_image.format} • {self.target_image.width}x{self.target_image.height}\n"
                f"Frames: {target_frames}\n"
                f"Colors: {len(self.target_palette_colors)} shown"
            )

        if self.palette_mapping:
            mapping_text = f"Mapping:\n{len(self.palette_mapping)} auto matches created"

        self.file_info_label.configure(text=f"{source_text}\n\n{target_text}\n\n{mapping_text}")

    def set_status(self, message):
        self.status_label.configure(text=f"Status: {message}")

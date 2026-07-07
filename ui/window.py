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

        self.title("PaletteForge v0.3.0 — Professional Workspace UI")
        self.geometry("1500x900")
        self.minsize(1280, 760)

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

        self.configure(fg_color="#0B0D10")

        self.create_layout()

    def create_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.font_title = ("Segoe UI", 24, "bold")
        self.font_section = ("Segoe UI", 15, "bold")
        self.font_body = ("Segoe UI", 12)
        self.font_small = ("Segoe UI", 10)

        # Top product bar
        self.topbar = ctk.CTkFrame(self, height=64, fg_color="#111318", corner_radius=0)
        self.topbar.grid(row=0, column=0, sticky="ew")
        self.topbar.grid_propagate(False)
        self.topbar.grid_columnconfigure(0, weight=1)
        self.topbar.grid_columnconfigure(1, weight=0)

        self.brand_label = ctk.CTkLabel(
            self.topbar,
            text="🎨 PaletteForge Studio",
            font=("Segoe UI", 24, "bold"),
            text_color="#FFFFFF"
        )
        self.brand_label.grid(row=0, column=0, padx=24, pady=(10, 0), sticky="w")

        self.build_label = ctk.CTkLabel(
            self.topbar,
            text="v0.3.0  •  Professional Workspace UI",
            font=("Segoe UI", 12),
            text_color="#9AA3B2"
        )
        self.build_label.grid(row=1, column=0, padx=26, pady=(0, 10), sticky="w")

        self.priority_label = ctk.CTkLabel(
            self.topbar,
            text="Priority Stack: Interface → Smart Match → Resizer",
            font=("Segoe UI", 12, "bold"),
            text_color="#F0B232"
        )
        self.priority_label.grid(row=0, column=1, rowspan=2, padx=24, pady=12, sticky="e")

        # Main workspace
        self.workspace = ctk.CTkFrame(self, fg_color="#0B0D10", corner_radius=0)
        self.workspace.grid(row=1, column=0, sticky="nsew")
        self.workspace.grid_columnconfigure(0, weight=0)
        self.workspace.grid_columnconfigure(1, weight=1)
        self.workspace.grid_columnconfigure(2, weight=0)
        self.workspace.grid_rowconfigure(0, weight=1)

        # Left action rail
        self.sidebar = ctk.CTkFrame(self.workspace, width=255, fg_color="#151922", corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        self.actions_title = ctk.CTkLabel(
            self.sidebar,
            text="Workspace Actions",
            font=self.font_section,
            text_color="#FFFFFF"
        )
        self.actions_title.pack(padx=18, pady=(22, 10), anchor="w")

        self.load_source_button = ctk.CTkButton(
            self.sidebar,
            text="Load Source Image / GIF",
            command=lambda: self.load_image("source"),
            height=40,
            fg_color="#5865F2",
            hover_color="#4752C4",
            font=self.font_body
        )
        self.load_source_button.pack(padx=18, pady=6, fill="x")

        self.load_target_button = ctk.CTkButton(
            self.sidebar,
            text="Load Target Image / GIF",
            command=lambda: self.load_image("target"),
            height=40,
            fg_color="#3BA55D",
            hover_color="#2D7D46",
            font=self.font_body
        )
        self.load_target_button.pack(padx=18, pady=6, fill="x")

        self.tool_divider_1 = ctk.CTkFrame(self.sidebar, height=1, fg_color="#2A303B")
        self.tool_divider_1.pack(padx=18, pady=16, fill="x")

        self.smart_tools_label = ctk.CTkLabel(
            self.sidebar,
            text="Smart Tools",
            font=self.font_section,
            text_color="#FFFFFF"
        )
        self.smart_tools_label.pack(padx=18, pady=(0, 8), anchor="w")

        self.auto_match_button = ctk.CTkButton(
            self.sidebar,
            text="⚡ Smart Match",
            command=self.auto_match_palettes,
            height=40,
            fg_color="#F0B232",
            hover_color="#C98F1E",
            text_color="#111214",
            font=("Segoe UI", 12, "bold")
        )
        self.auto_match_button.pack(padx=18, pady=6, fill="x")

        self.live_preview_button = ctk.CTkButton(
            self.sidebar,
            text="🔥 Live Swap Preview",
            command=self.render_live_swap_preview,
            height=40,
            fg_color="#EB459E",
            hover_color="#C63D86",
            font=self.font_body
        )
        self.live_preview_button.pack(padx=18, pady=6, fill="x")

        self.show_original_button = ctk.CTkButton(
            self.sidebar,
            text="Show Original Source",
            command=self.restore_source_preview,
            height=38,
            fg_color="#252B35",
            hover_color="#333A46",
            font=self.font_body
        )
        self.show_original_button.pack(padx=18, pady=6, fill="x")

        self.apply_mapping_button = ctk.CTkButton(
            self.sidebar,
            text="Apply Manual Mapping",
            command=self.apply_manual_mapping,
            height=38,
            fg_color="#5865F2",
            hover_color="#4752C4",
            font=self.font_body
        )
        self.apply_mapping_button.pack(padx=18, pady=6, fill="x")

        self.analyze_sprite_button = ctk.CTkButton(
            self.sidebar,
            text="🧩 Analyze Sprite",
            command=self.analyze_sprite_regions,
            height=38,
            fg_color="#7289DA",
            hover_color="#5865F2",
            font=self.font_body
        )
        self.analyze_sprite_button.pack(padx=18, pady=6, fill="x")

        self.tool_divider_2 = ctk.CTkFrame(self.sidebar, height=1, fg_color="#2A303B")
        self.tool_divider_2.pack(padx=18, pady=16, fill="x")

        self.export_tools_label = ctk.CTkLabel(
            self.sidebar,
            text="Export",
            font=self.font_section,
            text_color="#FFFFFF"
        )
        self.export_tools_label.pack(padx=18, pady=(0, 8), anchor="w")

        self.export_gif_button = ctk.CTkButton(
            self.sidebar,
            text="📦 Export GIF",
            command=self.export_swapped_gif,
            height=40,
            fg_color="#57F287",
            hover_color="#3BA55D",
            text_color="#111214",
            font=("Segoe UI", 12, "bold")
        )
        self.export_gif_button.pack(padx=18, pady=6, fill="x")

        self.resize_placeholder = ctk.CTkButton(
            self.sidebar,
            text="↔ Resizer Coming Next",
            command=lambda: self.set_status("Image + GIF Resizer is PF-003, next after Smart Match pass."),
            height=38,
            fg_color="#252B35",
            hover_color="#333A46",
            text_color="#9AA3B2",
            font=self.font_body
        )
        self.resize_placeholder.pack(padx=18, pady=6, fill="x")

        self.clear_button = ctk.CTkButton(
            self.sidebar,
            text="Clear Workspace",
            command=self.clear_all,
            height=38,
            fg_color="#252B35",
            hover_color="#333A46",
            font=self.font_body
        )
        self.clear_button.pack(padx=18, pady=(16, 6), fill="x")

        self.status_card = ctk.CTkFrame(self.sidebar, fg_color="#10131A", corner_radius=12)
        self.status_card.pack(padx=18, pady=(18, 14), fill="x", side="bottom")
        self.status_label = ctk.CTkLabel(
            self.status_card,
            text="Status:\nReady",
            font=self.font_body,
            text_color="#C7D0DD",
            wraplength=200,
            justify="left"
        )
        self.status_label.pack(padx=14, pady=12, anchor="w")

        # Center canvas + bottom mapping workspace
        self.center_area = ctk.CTkFrame(self.workspace, fg_color="#0B0D10", corner_radius=0)
        self.center_area.grid(row=0, column=1, sticky="nsew")
        self.center_area.grid_columnconfigure(0, weight=1)
        self.center_area.grid_rowconfigure(0, weight=1)
        self.center_area.grid_rowconfigure(1, weight=0)

        self.preview_frame = ctk.CTkFrame(self.center_area, fg_color="#0B0D10", corner_radius=0)
        self.preview_frame.grid(row=0, column=0, sticky="nsew", padx=16, pady=(16, 8))
        self.preview_frame.grid_columnconfigure(0, weight=1)
        self.preview_frame.grid_columnconfigure(1, weight=1)
        self.preview_frame.grid_rowconfigure(0, weight=1)

        self.source_panel = ctk.CTkFrame(self.preview_frame, fg_color="#151922", corner_radius=16)
        self.source_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=0)
        self.source_panel.grid_columnconfigure(0, weight=1)
        self.source_panel.grid_rowconfigure(1, weight=1)

        self.source_title = ctk.CTkLabel(
            self.source_panel,
            text="SOURCE",
            font=("Segoe UI", 16, "bold"),
            text_color="#FFFFFF"
        )
        self.source_title.grid(row=0, column=0, padx=16, pady=(14, 4), sticky="w")

        self.source_canvas = ctk.CTkFrame(self.source_panel, fg_color="#0F1218", corner_radius=14)
        self.source_canvas.grid(row=1, column=0, sticky="nsew", padx=14, pady=(6, 14))
        self.source_canvas.grid_columnconfigure(0, weight=1)
        self.source_canvas.grid_rowconfigure(0, weight=1)

        self.source_preview_label = ctk.CTkLabel(
            self.source_canvas,
            text="Drop or load source image / GIF",
            font=("Segoe UI", 18, "bold"),
            text_color="#7D8795"
        )
        self.source_preview_label.grid(row=0, column=0, padx=20, pady=20)

        self.target_panel = ctk.CTkFrame(self.preview_frame, fg_color="#151922", corner_radius=16)
        self.target_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=0)
        self.target_panel.grid_columnconfigure(0, weight=1)
        self.target_panel.grid_rowconfigure(1, weight=1)

        self.target_title = ctk.CTkLabel(
            self.target_panel,
            text="TARGET",
            font=("Segoe UI", 16, "bold"),
            text_color="#FFFFFF"
        )
        self.target_title.grid(row=0, column=0, padx=16, pady=(14, 4), sticky="w")

        self.target_canvas = ctk.CTkFrame(self.target_panel, fg_color="#0F1218", corner_radius=14)
        self.target_canvas.grid(row=1, column=0, sticky="nsew", padx=14, pady=(6, 14))
        self.target_canvas.grid_columnconfigure(0, weight=1)
        self.target_canvas.grid_rowconfigure(0, weight=1)

        self.target_preview_label = ctk.CTkLabel(
            self.target_canvas,
            text="Drop or load target image / GIF",
            font=("Segoe UI", 18, "bold"),
            text_color="#7D8795"
        )
        self.target_preview_label.grid(row=0, column=0, padx=20, pady=20)

        # Bottom mapping dock
        self.mapping_dock = ctk.CTkFrame(self.center_area, height=235, fg_color="#151922", corner_radius=16)
        self.mapping_dock.grid(row=1, column=0, sticky="ew", padx=16, pady=(8, 16))
        self.mapping_dock.grid_propagate(False)
        self.mapping_dock.grid_columnconfigure(0, weight=1)
        self.mapping_dock.grid_rowconfigure(1, weight=1)

        self.mapping_header = ctk.CTkFrame(self.mapping_dock, fg_color="transparent")
        self.mapping_header.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 4))
        self.mapping_header.grid_columnconfigure(0, weight=1)

        self.mapping_title = ctk.CTkLabel(
            self.mapping_header,
            text="Palette Mapping Editor",
            font=self.font_section,
            text_color="#FFFFFF"
        )
        self.mapping_title.grid(row=0, column=0, sticky="w")

        self.mapping_count_label = ctk.CTkLabel(
            self.mapping_header,
            text="0 matches",
            font=self.font_body,
            text_color="#9AA3B2"
        )
        self.mapping_count_label.grid(row=0, column=1, sticky="e")

        self.mapping_scroll = ctk.CTkScrollableFrame(
            self.mapping_dock,
            fg_color="#0F1218",
            corner_radius=12
        )
        self.mapping_scroll.grid(row=1, column=0, sticky="nsew", padx=14, pady=(4, 14))

        # Right inspector panel
        self.inspector = ctk.CTkFrame(self.workspace, width=345, fg_color="#151922", corner_radius=0)
        self.inspector.grid(row=0, column=2, sticky="nsew")
        self.inspector.grid_propagate(False)

        self.inspector_title = ctk.CTkLabel(
            self.inspector,
            text="Inspector",
            font=("Segoe UI", 20, "bold"),
            text_color="#FFFFFF"
        )
        self.inspector_title.pack(padx=20, pady=(22, 4), anchor="w")

        self.inspector_subtitle = ctk.CTkLabel(
            self.inspector,
            text="Sprite stats, palettes, and analysis",
            font=self.font_body,
            text_color="#9AA3B2"
        )
        self.inspector_subtitle.pack(padx=20, pady=(0, 12), anchor="w")

        self.file_info_card = ctk.CTkFrame(self.inspector, fg_color="#0F1218", corner_radius=12)
        self.file_info_card.pack(padx=18, pady=(0, 14), fill="x")

        self.file_info_label = ctk.CTkLabel(
            self.file_info_card,
            text="Load a source and target image/GIF to begin.",
            font=self.font_body,
            text_color="#C7D0DD",
            wraplength=285,
            justify="left"
        )
        self.file_info_label.pack(padx=14, pady=12, anchor="w")

        self.source_palette_title = ctk.CTkLabel(
            self.inspector,
            text="Source Palette",
            font=self.font_section,
            text_color="#FFFFFF"
        )
        self.source_palette_title.pack(padx=20, pady=(2, 0), anchor="w")

        self.source_palette_count_label = ctk.CTkLabel(
            self.inspector,
            text="0 colors",
            font=self.font_body,
            text_color="#9AA3B2"
        )
        self.source_palette_count_label.pack(padx=20, pady=(0, 6), anchor="w")

        self.source_palette_scroll = ctk.CTkScrollableFrame(
            self.inspector,
            width=300,
            height=155,
            fg_color="#0F1218",
            corner_radius=12
        )
        self.source_palette_scroll.pack(padx=18, pady=(0, 14), fill="x")

        self.target_palette_title = ctk.CTkLabel(
            self.inspector,
            text="Target Palette",
            font=self.font_section,
            text_color="#FFFFFF"
        )
        self.target_palette_title.pack(padx=20, pady=(2, 0), anchor="w")

        self.target_palette_count_label = ctk.CTkLabel(
            self.inspector,
            text="0 colors",
            font=self.font_body,
            text_color="#9AA3B2"
        )
        self.target_palette_count_label.pack(padx=20, pady=(0, 6), anchor="w")

        self.target_palette_scroll = ctk.CTkScrollableFrame(
            self.inspector,
            width=300,
            height=155,
            fg_color="#0F1218",
            corner_radius=12
        )
        self.target_palette_scroll.pack(padx=18, pady=(0, 14), fill="x")

        self.next_up_card = ctk.CTkFrame(self.inspector, fg_color="#10131A", corner_radius=12)
        self.next_up_card.pack(padx=18, pady=(0, 14), fill="x", side="bottom")

        self.next_up_label = ctk.CTkLabel(
            self.next_up_card,
            text="Next Milestones\nPF-002 Smart Match Perfection\nPF-003 Image + GIF Resizer",
            font=self.font_body,
            text_color="#C7D0DD",
            wraplength=285,
            justify="left"
        )
        self.next_up_label.pack(padx=14, pady=12, anchor="w")

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
            display_image.thumbnail((520, 520), Image.Resampling.NEAREST)

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
            frame.thumbnail((520, 520), Image.Resampling.NEAREST)

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
                text_color="#B5BAC1"
            )
            empty_label.pack(pady=10)
            widgets.append(empty_label)
            return

        for index, (rgb, count) in enumerate(colors, start=1):
            hex_color = "#{:02X}{:02X}{:02X}".format(*rgb)

            row = ctk.CTkFrame(
                parent,
                fg_color="#1E1F22",
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
            self.set_status("Load both GIFs first")
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
                text_color="#B5BAC1"
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
                fg_color="#1E1F22",
                corner_radius=6
            )
            row.pack(fill="x", padx=6, pady=3)

            number_label = ctk.CTkLabel(
                row,
                text=f"{index:02d}",
                font=("Arial", 10, "bold"),
                text_color="#B5BAC1",
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
                fg_color="#2B2D31",
                button_color="#383A40",
                button_hover_color="#4752C4",
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
            self.set_status("Load a source GIF first")
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
            self.set_status("Load a source GIF first")
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
            self.set_status("Load a source GIF first")
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
            display_frame.thumbnail((520, 520), Image.Resampling.NEAREST)
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
        self.status_label.configure(text=f"Status:\n{message}")

"""
PaletteForge
core/swapper.py

v0.1.4.1 - Auto Match Fix

Palette matching engine for PaletteForge.
"""

import math


class PaletteMatcher:
    """
    Matches source palette colors to target palette colors.

    Strategy:
    - Normalize Palette Explorer data into RGB tuples.
    - Sort source colors by perceived brightness.
    - Sort target colors by perceived brightness.
    - Pair colors by brightness order.
    - If source has more colors than target, use closest RGB fallback.
    """

    def __init__(self, source_palette, target_palette):
        self.source_palette = self._normalize_palette(source_palette)
        self.target_palette = self._normalize_palette(target_palette)
        self.mapping = []

    def auto_match(self):
        self.mapping = []

        if not self.source_palette or not self.target_palette:
            return self.mapping

        source_sorted = sorted(self.source_palette, key=self.color_brightness)
        target_sorted = sorted(self.target_palette, key=self.color_brightness)

        for index, source_color in enumerate(source_sorted):
            if index < len(target_sorted):
                target_color = target_sorted[index]
            else:
                target_color = self.find_closest_color(source_color, target_sorted)

            self.mapping.append(
                {
                    "source_rgb": source_color,
                    "target_rgb": target_color,
                    "source_hex": self.rgb_to_hex(source_color),
                    "target_hex": self.rgb_to_hex(target_color),
                    "source_brightness": round(self.color_brightness(source_color), 2),
                    "target_brightness": round(self.color_brightness(target_color), 2),
                }
            )

        return self.mapping

    def get_mapping(self):
        return self.mapping

    def get_mapping_dict(self):
        return {
            entry["source_rgb"]: entry["target_rgb"]
            for entry in self.mapping
        }

    def find_closest_color(self, source_color, target_colors):
        return min(
            target_colors,
            key=lambda target_color: self.color_distance(source_color, target_color)
        )

    @staticmethod
    def color_brightness(color):
        r, g, b = color
        return (0.299 * r) + (0.587 * g) + (0.114 * b)

    @staticmethod
    def color_distance(color_a, color_b):
        return math.sqrt(
            (color_a[0] - color_b[0]) ** 2
            + (color_a[1] - color_b[1]) ** 2
            + (color_a[2] - color_b[2]) ** 2
        )

    @staticmethod
    def rgb_to_hex(color):
        return "#{:02X}{:02X}{:02X}".format(*color)

    @staticmethod
    def _normalize_palette(palette):
        normalized = []

        for item in palette:
            # Current Palette Explorer format:
            # [((r, g, b), pixel_count), ...]
            if isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], tuple):
                rgb = item[0]
            else:
                rgb = item

            if isinstance(rgb, tuple) and len(rgb) >= 3:
                normalized.append((int(rgb[0]), int(rgb[1]), int(rgb[2])))

        return normalized

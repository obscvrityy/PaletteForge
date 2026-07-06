"""
PaletteForge
core/swapper.py

v0.1.4 - Auto Match Engine

This module contains the first real palette matching engine for PaletteForge.
It is intentionally separated from the UI so future features like live preview,
manual mapping, GIF export, presets, and batch processing can build on it cleanly.
"""

import math


class PaletteMatcher:
    """
    Matches source palette colors to target palette colors.

    Current v0.1.4 strategy:
    - Sort source colors by brightness.
    - Sort target colors by brightness.
    - Pair colors by brightness order.
    - If there are more source colors than target colors, use nearest-color fallback.
    """

    def __init__(self, source_palette, target_palette):
        self.source_palette = self._normalize_palette(source_palette)
        self.target_palette = self._normalize_palette(target_palette)
        self.mapping = []

    def auto_match(self):
        """
        Creates a source-to-target palette mapping.

        Returns:
            list[dict]: Mapping entries with source RGB, target RGB, hex values, and brightness.
        """
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
        """
        Returns the most recent mapping.
        """
        return self.mapping

    def get_mapping_dict(self):
        """
        Returns a simple dictionary version of the current mapping.

        Example:
            {(255, 0, 0): (0, 0, 255)}
        """
        return {
            entry["source_rgb"]: entry["target_rgb"]
            for entry in self.mapping
        }

    def find_closest_color(self, source_color, target_colors):
        """
        Finds the closest target color by RGB distance.
        """
        return min(
            target_colors,
            key=lambda target_color: self.color_distance(source_color, target_color)
        )

    @staticmethod
    def color_brightness(color):
        """
        Calculates perceived brightness using the standard luma formula.
        """
        r, g, b = color
        return (0.299 * r) + (0.587 * g) + (0.114 * b)

    @staticmethod
    def color_distance(color_a, color_b):
        """
        Calculates straight RGB distance between two colors.
        """
        return math.sqrt(
            (color_a[0] - color_b[0]) ** 2
            + (color_a[1] - color_b[1]) ** 2
            + (color_a[2] - color_b[2]) ** 2
        )

    @staticmethod
    def rgb_to_hex(color):
        """
        Converts an RGB tuple into a HEX string.
        """
        return "#{:02X}{:02X}{:02X}".format(*color)

    @staticmethod
    def _normalize_palette(palette):
        """
        Accepts palette formats from the current app and converts them into RGB tuples.

        Current Palette Explorer stores colors as:
            [((r, g, b), pixel_count), ...]

        This method also accepts:
            [(r, g, b), ...]
        """
        normalized = []

        for item in palette:
            if isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], tuple):
                rgb = item[0]
            else:
                rgb = item

            if isinstance(rgb, tuple) and len(rgb) >= 3:
                normalized.append((int(rgb[0]), int(rgb[1]), int(rgb[2])))

        return normalized

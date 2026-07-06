"""
PaletteForge
core/analyzer.py

v0.2.3 - Sprite Role Detection

This module analyzes what each palette color is doing inside a sprite.

The goal is to move PaletteForge away from simple color-to-color matching and
toward sprite-part-aware matching:
- outline
- shadow
- primary body
- secondary body
- highlight
- neutral / belly / light regions
- accent colors

This is not final "perfect Pokémon recognition" yet, but it gives the matcher
much better information than RGB values alone.
"""

import colorsys
from collections import defaultdict


class SpriteAnalyzer:
    """
    Analyzes palette colors and assigns each one a likely sprite role.
    """

    def __init__(self, palette):
        self.palette_entries = self._normalize_palette_with_counts(palette)
        self.total_pixels = sum(entry["count"] for entry in self.palette_entries) or 1

    def analyze(self):
        analyzed = []

        for rank, entry in enumerate(self.palette_entries):
            analyzed_entry = self._analyze_entry(entry, rank)
            analyzed.append(analyzed_entry)

        return self._assign_body_roles(analyzed)

    def _analyze_entry(self, entry, rank):
        rgb = entry["rgb"]
        r, g, b = rgb

        hue, saturation, value = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        brightness = self.color_brightness(rgb)
        coverage = entry["count"] / self.total_pixels

        family = self._classify_family(hue, saturation, brightness)
        role = self._classify_base_role(brightness, saturation, value, coverage, family)

        return {
            "rgb": rgb,
            "count": entry["count"],
            "coverage": coverage,
            "rank": rank,
            "hue": hue,
            "saturation": saturation,
            "value": value,
            "brightness": brightness,
            "family": family,
            "role": role,
            "semantic_role": role,
        }

    def _assign_body_roles(self, colors):
        """
        Promotes important color families into body roles.

        This is the key step for Charizard/Greninja-style matching:
        the most common saturated family becomes primary_body instead of just
        "warm" or "cool".
        """
        family_counts = defaultdict(int)

        for color in colors:
            if color["role"] in ("outline", "neutral", "highlight"):
                continue

            if color["saturation"] < 0.18:
                continue

            family_counts[color["family"]] += color["count"]

        ranked_families = [
            family
            for family, _count in sorted(
                family_counts.items(),
                key=lambda item: item[1],
                reverse=True
            )
        ]

        primary_family = ranked_families[0] if len(ranked_families) >= 1 else None
        secondary_family = ranked_families[1] if len(ranked_families) >= 2 else None

        for color in colors:
            if color["role"] in ("outline", "shadow", "highlight", "neutral"):
                color["semantic_role"] = color["role"]
                continue

            if color["family"] == primary_family:
                if color["brightness"] < 90:
                    color["semantic_role"] = "primary_body_shadow"
                elif color["brightness"] > 180:
                    color["semantic_role"] = "primary_body_highlight"
                else:
                    color["semantic_role"] = "primary_body"

            elif color["family"] == secondary_family:
                if color["brightness"] < 100:
                    color["semantic_role"] = "secondary_body_shadow"
                elif color["brightness"] > 185:
                    color["semantic_role"] = "secondary_body_highlight"
                else:
                    color["semantic_role"] = "secondary_body"

            else:
                color["semantic_role"] = "accent"

        return colors

    def _classify_base_role(self, brightness, saturation, value, coverage, family):
        if brightness < 38:
            return "outline"

        if brightness < 76 and saturation < 0.35:
            return "shadow"

        if saturation < 0.12 and brightness > 185:
            return "highlight"

        if saturation < 0.16:
            return "neutral"

        if coverage > 0.08 and saturation > 0.20:
            return "body_candidate"

        if brightness > 188:
            return "highlight"

        if saturation > 0.30:
            return "accent_candidate"

        return "midtone"

    def _classify_family(self, hue, saturation, brightness):
        if brightness < 45:
            return "outline"

        if saturation < 0.16:
            return "neutral"

        if hue <= 0.06 or hue >= 0.92:
            return "red"

        if 0.06 < hue <= 0.16:
            return "orange"

        if 0.16 < hue <= 0.25:
            return "yellow"

        if 0.25 < hue <= 0.45:
            return "green"

        if 0.45 < hue <= 0.58:
            return "cyan"

        if 0.58 < hue <= 0.72:
            return "blue"

        if 0.72 < hue <= 0.86:
            return "purple"

        return "pink"

    @staticmethod
    def color_brightness(color):
        r, g, b = color
        return (0.299 * r) + (0.587 * g) + (0.114 * b)

    @staticmethod
    def rgb_to_hex(color):
        return "#{:02X}{:02X}{:02X}".format(*color)

    @staticmethod
    def _normalize_palette_with_counts(palette):
        normalized = []

        for item in palette:
            if isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], tuple):
                rgb = item[0]
                count = item[1]
            else:
                rgb = item
                count = 1

            if isinstance(rgb, tuple) and len(rgb) >= 3:
                normalized.append(
                    {
                        "rgb": (int(rgb[0]), int(rgb[1]), int(rgb[2])),
                        "count": int(count),
                    }
                )

        return normalized

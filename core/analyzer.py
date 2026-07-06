"""
PaletteForge
core/analyzer.py

v0.2.5 - Material-Aware Sprite Role Detection

This version combines palette information with spatial region information:
- edge ratio
- interior ratio
- coverage
- neighboring colors
- body-family dominance

This helps avoid bad mappings where body, belly, wing, outline, and accent
colors are treated as interchangeable.
"""

import colorsys
from collections import defaultdict

from core.material_analyzer import MaterialAnalyzer


class SpriteAnalyzer:
    def __init__(self, palette, region_metadata=None):
        self.palette_entries = self._normalize_palette_with_counts(palette)
        self.region_metadata = region_metadata or {}
        self.total_pixels = sum(entry["count"] for entry in self.palette_entries) or 1
        self.material_analyzer = MaterialAnalyzer()

    def analyze(self):
        analyzed = []

        for rank, entry in enumerate(self.palette_entries):
            analyzed_entry = self._analyze_entry(entry, rank)
            analyzed.append(analyzed_entry)

        analyzed = self._assign_body_roles(analyzed)
        analyzed = self._assign_region_roles(analyzed)
        analyzed = self._assign_material_roles(analyzed)

        return analyzed


    def _assign_material_roles(self, colors):
        for color in colors:
            color["material"] = self.material_analyzer.classify(color)

        return colors

    def _analyze_entry(self, entry, rank):
        rgb = entry["rgb"]
        r, g, b = rgb

        hue, saturation, value = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        brightness = self.color_brightness(rgb)
        coverage = entry["count"] / self.total_pixels

        region = self.region_metadata.get(rgb, {})
        edge_ratio = region.get("edge_ratio", 0)
        interior_ratio = region.get("interior_ratio", 0)
        touch_count = region.get("touch_count", 0)

        family = self._classify_family(hue, saturation, brightness)
        role = self._classify_base_role(
            brightness,
            saturation,
            value,
            coverage,
            family,
            edge_ratio,
            interior_ratio
        )

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
            "edge_ratio": edge_ratio,
            "interior_ratio": interior_ratio,
            "touch_count": touch_count,
            "region": region,
        }

    def _assign_body_roles(self, colors):
        family_counts = defaultdict(int)

        for color in colors:
            if color["role"] in ("outline", "neutral", "highlight"):
                continue

            if color["saturation"] < 0.18:
                continue

            # Give interior-heavy colors more body importance.
            body_weight = 1.0 + color["interior_ratio"]
            family_counts[color["family"]] += color["count"] * body_weight

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

    def _assign_region_roles(self, colors):
        """
        Spatial correction pass.

        This is where v0.2.4 improves over v0.2.3:
        - edge-heavy dark colors become outline
        - large interior saturated colors become body
        - low-saturation interior colors become neutral/belly-like
        - small saturated colors become accent
        """
        for color in colors:
            if color["brightness"] < 55 and color["edge_ratio"] > 0.18:
                color["semantic_role"] = "outline"
                continue

            if color["coverage"] > 0.03 and color["interior_ratio"] > 0.65 and color["saturation"] > 0.22:
                if "primary_body" not in color["semantic_role"] and "secondary_body" not in color["semantic_role"]:
                    color["semantic_role"] = "primary_body"

            if color["coverage"] > 0.015 and color["interior_ratio"] > 0.55 and color["saturation"] < 0.25:
                if color["brightness"] > 125:
                    color["semantic_role"] = "neutral"

            if color["coverage"] < 0.012 and color["saturation"] > 0.28 and color["brightness"] > 80:
                if color["semantic_role"] not in ("outline", "highlight"):
                    color["semantic_role"] = "accent"

        return colors

    def _classify_base_role(self, brightness, saturation, value, coverage, family, edge_ratio, interior_ratio):
        if brightness < 42 and edge_ratio > 0.12:
            return "outline"

        if brightness < 70 and edge_ratio > 0.08:
            return "shadow"

        if saturation < 0.12 and brightness > 185:
            return "highlight"

        if saturation < 0.16:
            return "neutral"

        if coverage > 0.06 and saturation > 0.20 and interior_ratio > 0.45:
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

"""
PaletteForge
core/material_analyzer.py

v0.2.9 - Material Graph Alpha
"""


class MaterialAnalyzer:
    def classify(self, color):
        semantic_role = color.get("semantic_role", "")
        family = color.get("family", "")
        saturation = color.get("saturation", 0)
        brightness = color.get("brightness", 0)
        coverage = color.get("coverage", 0)
        edge_ratio = color.get("edge_ratio", 0)
        interior_ratio = color.get("interior_ratio", 0)

        if semantic_role == "outline" or (brightness < 55 and edge_ratio > 0.12):
            return "line_art"

        if semantic_role in ("primary_body", "primary_body_shadow", "primary_body_highlight"):
            return "main_body"

        if semantic_role in ("secondary_body", "secondary_body_shadow", "secondary_body_highlight"):
            return "secondary_body"

        if saturation < 0.22 and brightness > 125 and interior_ratio > 0.35:
            return "belly_light"

        if saturation < 0.16 and brightness > 172:
            return "highlight_light"

        if coverage < 0.018 and saturation > 0.30:
            if family in ("red", "orange", "yellow"):
                return "energy_accent"
            return "small_accent"

        if semantic_role == "accent":
            return "accent"

        if saturation > 0.25 and coverage > 0.022:
            return "colored_surface"

        return "misc"

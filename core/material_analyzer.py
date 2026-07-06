"""
PaletteForge
core/material_analyzer.py

v0.2.5 - Material-Aware Matching

This module classifies what a palette color probably represents as a material.

The purpose is to avoid bad matches like:
- body color -> scarf/accent
- belly color -> body shadow
- outline color -> body fill
- flame/accent color -> neutral belly

This is still heuristic-based, but gives the matcher stronger guidance.
"""


class MaterialAnalyzer:
    """
    Assigns high-level material classes to analyzed sprite colors.
    """

    def classify(self, color):
        semantic_role = color.get("semantic_role", "")
        family = color.get("family", "")
        saturation = color.get("saturation", 0)
        brightness = color.get("brightness", 0)
        coverage = color.get("coverage", 0)
        edge_ratio = color.get("edge_ratio", 0)
        interior_ratio = color.get("interior_ratio", 0)

        if semantic_role == "outline" or (brightness < 50 and edge_ratio > 0.14):
            return "line_art"

        if semantic_role in ("primary_body", "primary_body_shadow", "primary_body_highlight"):
            return "main_body"

        if semantic_role in ("secondary_body", "secondary_body_shadow", "secondary_body_highlight"):
            return "secondary_body"

        if semantic_role in ("neutral", "highlight") and interior_ratio > 0.45 and brightness > 120:
            return "belly_light"

        if saturation < 0.16 and brightness > 170:
            return "highlight_light"

        if coverage < 0.018 and saturation > 0.30:
            if family in ("red", "orange", "yellow"):
                return "energy_accent"
            return "small_accent"

        if family in ("red", "orange", "yellow") and saturation > 0.35 and coverage < 0.04:
            return "energy_accent"

        if semantic_role == "accent":
            return "accent"

        if saturation > 0.25 and coverage > 0.025:
            return "colored_surface"

        return "misc"

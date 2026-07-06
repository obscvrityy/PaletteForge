"""
PaletteForge
core/swapper.py

v0.2.9 - Pokémon Smart Match Alpha

Bundled features:
- region graph foundation
- material graph foundation
- role-aware matching
- material-aware matching
- outline protection
- body-to-body preference
"""

import math

from core.analyzer import SpriteAnalyzer
from core.region_analyzer import SpriteRegionAnalyzer


class PaletteMatcher:
    def __init__(self, source_palette, target_palette, source_image=None, target_image=None):
        source_regions = SpriteRegionAnalyzer(source_image).analyze() if source_image is not None else {}
        target_regions = SpriteRegionAnalyzer(target_image).analyze() if target_image is not None else {}

        self.source_colors = SpriteAnalyzer(source_palette, source_regions).analyze()
        self.target_colors = SpriteAnalyzer(target_palette, target_regions).analyze()
        self.mapping = []

    def auto_match(self):
        self.mapping = []

        if not self.source_colors or not self.target_colors:
            return self.mapping

        source_groups = self._group_by_material(self.source_colors)
        target_groups = self._group_by_material(self.target_colors)

        used_sources = set()
        used_targets = set()

        material_order = [
            "line_art",
            "main_body",
            "secondary_body",
            "belly_light",
            "highlight_light",
            "colored_surface",
            "accent",
            "energy_accent",
            "small_accent",
            "misc",
        ]

        for material in material_order:
            source_group = source_groups.get(material, [])

            if not source_group:
                continue

            target_group = self._best_target_material_group(material, target_groups)

            if not target_group:
                continue

            pairs = self._map_group_by_brightness(source_group, target_group)

            for source, target in pairs:
                if source["rgb"] in used_sources:
                    continue

                self.mapping.append(self._make_mapping_entry(source, target))
                used_sources.add(source["rgb"])
                used_targets.add(target["rgb"])

        for source in self.source_colors:
            if source["rgb"] in used_sources:
                continue

            target = min(
                self.target_colors,
                key=lambda candidate: self._match_score(source, candidate, used_targets)
            )

            self.mapping.append(self._make_mapping_entry(source, target))
            used_sources.add(source["rgb"])
            used_targets.add(target["rgb"])

        source_order = {entry["rgb"]: index for index, entry in enumerate(self.source_colors)}
        self.mapping = sorted(
            self.mapping,
            key=lambda entry: source_order.get(entry["source_rgb"], 9999)
        )

        return self.mapping

    def get_mapping(self):
        return self.mapping

    def get_mapping_dict(self):
        return {entry["source_rgb"]: entry["target_rgb"] for entry in self.mapping}

    def _group_by_material(self, colors):
        groups = {}

        for color in colors:
            material = color.get("material", "misc")
            groups.setdefault(material, []).append(color)

        for material in groups:
            groups[material] = sorted(groups[material], key=lambda entry: entry["brightness"])

        return groups

    def _best_target_material_group(self, source_material, target_groups):
        if source_material in target_groups:
            return target_groups[source_material]

        fallback_materials = {
            "line_art": ["misc"],
            "main_body": ["colored_surface", "secondary_body", "accent"],
            "secondary_body": ["accent", "colored_surface", "main_body", "belly_light"],
            "belly_light": ["highlight_light", "secondary_body", "misc"],
            "highlight_light": ["belly_light", "secondary_body", "misc"],
            "colored_surface": ["main_body", "secondary_body", "accent"],
            "accent": ["small_accent", "energy_accent", "secondary_body"],
            "energy_accent": ["small_accent", "accent"],
            "small_accent": ["accent", "energy_accent"],
            "misc": ["colored_surface", "secondary_body", "belly_light"],
        }

        for fallback in fallback_materials.get(source_material, []):
            if fallback in target_groups:
                return target_groups[fallback]

        if target_groups:
            largest_material = max(
                target_groups.keys(),
                key=lambda material: sum(color["count"] for color in target_groups[material])
            )
            return target_groups[largest_material]

        return []

    def _map_group_by_brightness(self, source_group, target_group):
        if not source_group or not target_group:
            return []

        source_sorted = sorted(source_group, key=lambda entry: entry["brightness"])
        target_sorted = sorted(target_group, key=lambda entry: entry["brightness"])

        if len(source_sorted) == 1:
            target = target_sorted[len(target_sorted) // 2]
            return [(source_sorted[0], target)]

        pairs = []

        for source_index, source in enumerate(source_sorted):
            position = source_index / max(len(source_sorted) - 1, 1)
            target_index = round(position * max(len(target_sorted) - 1, 0))
            pairs.append((source, target_sorted[target_index]))

        return pairs

    def _match_score(self, source, target, used_targets):
        score = 0.0

        if target["rgb"] in used_targets:
            score += 24

        if source.get("material") == target.get("material"):
            score -= 135
        elif self._materials_compatible(source.get("material"), target.get("material")):
            score -= 60
        else:
            score += 48

        if source["semantic_role"] == target["semantic_role"]:
            score -= 70
        elif self._roles_compatible(source["semantic_role"], target["semantic_role"]):
            score -= 28
        else:
            score += 24

        score += abs(source.get("edge_ratio", 0) - target.get("edge_ratio", 0)) * 42
        score += abs(source.get("interior_ratio", 0) - target.get("interior_ratio", 0)) * 24
        score += abs(source["brightness"] - target["brightness"]) * 0.34
        score += abs(source["saturation"] - target["saturation"]) * 18
        score += abs(source["rank"] - target["rank"]) * 0.45

        if source.get("material") == "line_art" and target["brightness"] > 90:
            score += 150

        if source.get("material") != "line_art" and target.get("material") == "line_art":
            score += 120

        if source.get("material") == "belly_light" and target["brightness"] < 110:
            score += 90

        return score

    def _materials_compatible(self, material_a, material_b):
        compatible_groups = [
            {"main_body", "colored_surface"},
            {"secondary_body", "accent", "colored_surface"},
            {"belly_light", "highlight_light", "misc"},
            {"accent", "small_accent", "energy_accent"},
        ]

        return any(material_a in group and material_b in group for group in compatible_groups)

    def _roles_compatible(self, role_a, role_b):
        compatible_groups = [
            {"primary_body_shadow", "primary_body", "primary_body_highlight"},
            {"secondary_body_shadow", "secondary_body", "secondary_body_highlight"},
            {"primary_body", "secondary_body", "accent"},
            {"outline", "shadow"},
            {"neutral", "highlight"},
        ]

        return any(role_a in group and role_b in group for group in compatible_groups)

    def _make_mapping_entry(self, source, target):
        return {
            "source_rgb": source["rgb"],
            "target_rgb": target["rgb"],
            "source_hex": self.rgb_to_hex(source["rgb"]),
            "target_hex": self.rgb_to_hex(target["rgb"]),
            "source_brightness": round(source["brightness"], 2),
            "target_brightness": round(target["brightness"], 2),
            "source_role": source["semantic_role"],
            "target_role": target["semantic_role"],
            "source_family": source["family"],
            "target_family": target["family"],
            "source_material": source.get("material", "misc"),
            "target_material": target.get("material", "misc"),
            "source_edge_ratio": round(source.get("edge_ratio", 0), 3),
            "target_edge_ratio": round(target.get("edge_ratio", 0), 3),
        }

    @staticmethod
    def rgb_to_hex(color):
        return "#{:02X}{:02X}{:02X}".format(*color)

    @staticmethod
    def color_distance(color_a, color_b):
        return math.sqrt(
            (color_a[0] - color_b[0]) ** 2
            + (color_a[1] - color_b[1]) ** 2
            + (color_a[2] - color_b[2]) ** 2
        )

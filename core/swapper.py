"""
PaletteForge
core/swapper.py

v0.2.4 - Region Detection Matching

This matcher uses both palette analysis and sprite-region analysis.

Main improvements:
- Source/target images are inspected spatially.
- Outline-like colors are protected.
- Interior body colors are favored for body-to-body mapping.
- Small saturated colors are treated more like accents.
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

        source_groups = self._group_by_semantic_role(self.source_colors)
        target_groups = self._group_by_semantic_role(self.target_colors)

        used_sources = set()
        used_targets = set()

        role_order = [
            "outline",
            "primary_body_shadow",
            "primary_body",
            "primary_body_highlight",
            "secondary_body_shadow",
            "secondary_body",
            "secondary_body_highlight",
            "shadow",
            "neutral",
            "highlight",
            "accent",
        ]

        for role in role_order:
            source_group = source_groups.get(role, [])

            if not source_group:
                continue

            target_group = self._best_target_group(role, target_groups)

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
        return {
            entry["source_rgb"]: entry["target_rgb"]
            for entry in self.mapping
        }

    def _group_by_semantic_role(self, colors):
        groups = {}

        for color in colors:
            role = color["semantic_role"]
            groups.setdefault(role, []).append(color)

        for role in groups:
            groups[role] = sorted(groups[role], key=lambda entry: entry["brightness"])

        return groups

    def _best_target_group(self, source_role, target_groups):
        if source_role in target_groups:
            return target_groups[source_role]

        fallback_roles = {
            "primary_body_shadow": ["primary_body", "shadow", "secondary_body_shadow"],
            "primary_body": ["secondary_body", "accent"],
            "primary_body_highlight": ["primary_body", "highlight", "secondary_body_highlight"],
            "secondary_body_shadow": ["secondary_body", "shadow", "primary_body_shadow"],
            "secondary_body": ["primary_body", "accent", "neutral"],
            "secondary_body_highlight": ["secondary_body", "highlight", "primary_body_highlight"],
            "outline": ["shadow"],
            "shadow": ["outline", "primary_body_shadow", "secondary_body_shadow"],
            "neutral": ["highlight", "secondary_body"],
            "highlight": ["neutral", "primary_body_highlight", "secondary_body_highlight"],
            "accent": ["secondary_body", "primary_body", "highlight"],
        }

        for fallback in fallback_roles.get(source_role, []):
            if fallback in target_groups:
                return target_groups[fallback]

        if target_groups:
            largest_role = max(
                target_groups.keys(),
                key=lambda role: sum(color["count"] for color in target_groups[role])
            )
            return target_groups[largest_role]

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
            score += 22

        if source["semantic_role"] == target["semantic_role"]:
            score -= 95
        elif self._roles_compatible(source["semantic_role"], target["semantic_role"]):
            score -= 36
        else:
            score += 28

        # Region behavior should matter.
        score += abs(source.get("edge_ratio", 0) - target.get("edge_ratio", 0)) * 38
        score += abs(source.get("interior_ratio", 0) - target.get("interior_ratio", 0)) * 20

        if source["family"] == target["family"]:
            score -= 8

        score += abs(source["brightness"] - target["brightness"]) * 0.38
        score += abs(source["saturation"] - target["saturation"]) * 20
        score += abs(source["rank"] - target["rank"]) * 0.55

        if source["semantic_role"] == "outline" and target["brightness"] > 90:
            score += 120

        if source["semantic_role"] != "outline" and target["semantic_role"] == "outline":
            score += 90

        return score

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

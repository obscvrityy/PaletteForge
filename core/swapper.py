"""
PaletteForge
core/swapper.py

v0.2.3 - Sprite Role Detection Matching

This matcher uses SpriteAnalyzer to match colors by what they appear to do in
the sprite, not just by brightness or hue.

The main improvement:
- primary_body maps to primary_body
- secondary_body maps to secondary_body
- outline maps to outline
- highlights stay highlights
- accents stay accents when possible
"""

import math

from core.analyzer import SpriteAnalyzer


class PaletteMatcher:
    def __init__(self, source_palette, target_palette):
        self.source_colors = SpriteAnalyzer(source_palette).analyze()
        self.target_colors = SpriteAnalyzer(target_palette).analyze()
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

        # Fallback for any source colors that were not handled.
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
            "outline": ["shadow", "neutral"],
            "shadow": ["outline", "primary_body_shadow", "secondary_body_shadow"],
            "neutral": ["highlight", "secondary_body", "accent"],
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
            score += 18

        if source["semantic_role"] == target["semantic_role"]:
            score -= 90
        elif self._roles_compatible(source["semantic_role"], target["semantic_role"]):
            score -= 35
        else:
            score += 25

        if source["family"] == target["family"]:
            score -= 12

        score += abs(source["brightness"] - target["brightness"]) * 0.42
        score += abs(source["saturation"] - target["saturation"]) * 24
        score += abs(source["rank"] - target["rank"]) * 0.65

        if source["semantic_role"] == "outline" and target["brightness"] > 90:
            score += 100

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

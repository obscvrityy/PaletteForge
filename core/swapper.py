"""
PaletteForge
core/swapper.py

v0.2.1 - Smart Palette Matching

This replaces the original brightness-only matcher with a smarter palette matcher
that considers hue, saturation, brightness, and color roles.

It is still automatic and fast, but produces much better sprite swaps than
simple darkest-to-darkest matching.
"""

import colorsys
import math


class PaletteMatcher:
    """
    Matches source palette colors to target palette colors.

    v0.2.1 strategy:
    - Normalize Palette Explorer data into RGB tuples.
    - Analyze each color's role:
      outline, neutral, highlight, shadow, saturated, warm, cool, etc.
    - Score potential source-to-target pairings using:
      role similarity
      brightness similarity
      saturation similarity
      hue relationship
      pixel-rank importance
    - Avoid reusing target colors until needed.
    """

    def __init__(self, source_palette, target_palette):
        self.source_entries = self._normalize_palette_with_counts(source_palette)
        self.target_entries = self._normalize_palette_with_counts(target_palette)

        self.source_palette = [entry["rgb"] for entry in self.source_entries]
        self.target_palette = [entry["rgb"] for entry in self.target_entries]

        self.mapping = []

    def auto_match(self):
        self.mapping = []

        if not self.source_entries or not self.target_entries:
            return self.mapping

        analyzed_sources = [self._analyze_entry(entry, index) for index, entry in enumerate(self.source_entries)]
        analyzed_targets = [self._analyze_entry(entry, index) for index, entry in enumerate(self.target_entries)]

        # Match important/high-coverage colors first.
        analyzed_sources = sorted(
            analyzed_sources,
            key=lambda entry: (
                self._role_priority(entry),
                -entry["count"],
                entry["brightness"]
            )
        )

        unused_targets = analyzed_targets[:]

        for source in analyzed_sources:
            if unused_targets:
                target = min(
                    unused_targets,
                    key=lambda candidate: self._match_score(source, candidate)
                )
                unused_targets.remove(target)
            else:
                target = min(
                    analyzed_targets,
                    key=lambda candidate: self._match_score(source, candidate)
                )

            self.mapping.append(
                {
                    "source_rgb": source["rgb"],
                    "target_rgb": target["rgb"],
                    "source_hex": self.rgb_to_hex(source["rgb"]),
                    "target_hex": self.rgb_to_hex(target["rgb"]),
                    "source_brightness": round(source["brightness"], 2),
                    "target_brightness": round(target["brightness"], 2),
                    "source_role": source["role"],
                    "target_role": target["role"],
                }
            )

        # Display mapping in source palette order so the UI feels predictable.
        source_order = {entry["rgb"]: index for index, entry in enumerate(self.source_entries)}
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

    def _match_score(self, source, target):
        score = 0.0

        # Color role is the strongest signal.
        if source["role"] == target["role"]:
            score -= 55
        elif self._roles_are_compatible(source["role"], target["role"]):
            score -= 28
        else:
            score += 20

        # Preserve value/ramp structure.
        score += abs(source["brightness"] - target["brightness"]) * 0.55

        # Preserve intensity where possible.
        score += abs(source["saturation"] - target["saturation"]) * 35

        # Hue matters most for colorful sprite regions, less for neutral colors.
        if source["saturation"] > 0.18 and target["saturation"] > 0.18:
            score += self._hue_distance(source["hue"], target["hue"]) * 25

        # Prefer similar palette importance.
        score += abs(source["rank"] - target["rank"]) * 1.35

        # Keep outlines dark.
        if source["role"] == "outline" and target["brightness"] > 90:
            score += 80

        # Keep highlights light.
        if source["role"] == "highlight" and target["brightness"] < 120:
            score += 55

        # Keep neutral/white/gray from hijacking saturated body colors.
        if source["is_neutral"] != target["is_neutral"]:
            score += 30

        return score

    def _roles_are_compatible(self, role_a, role_b):
        compatible_groups = [
            {"outline", "shadow"},
            {"highlight", "light"},
            {"neutral", "highlight", "light"},
            {"warm", "saturated"},
            {"cool", "saturated"},
            {"shadow", "midtone"},
            {"midtone", "saturated"},
        ]

        return any(role_a in group and role_b in group for group in compatible_groups)

    def _role_priority(self, entry):
        priority = {
            "outline": 0,
            "shadow": 1,
            "midtone": 2,
            "saturated": 3,
            "warm": 4,
            "cool": 4,
            "neutral": 5,
            "light": 6,
            "highlight": 7,
        }

        return priority.get(entry["role"], 99)

    def _analyze_entry(self, entry, rank):
        rgb = entry["rgb"]
        r, g, b = rgb

        hue, saturation, value = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        brightness = self.color_brightness(rgb)

        is_neutral = saturation < 0.14
        role = self._classify_role(rgb, hue, saturation, value, brightness)

        return {
            "rgb": rgb,
            "count": entry["count"],
            "rank": rank,
            "hue": hue,
            "saturation": saturation,
            "value": value,
            "brightness": brightness,
            "is_neutral": is_neutral,
            "role": role,
        }

    def _classify_role(self, rgb, hue, saturation, value, brightness):
        r, g, b = rgb

        if brightness < 38:
            return "outline"

        if brightness < 80:
            return "shadow"

        if saturation < 0.12 and brightness > 190:
            return "highlight"

        if saturation < 0.14:
            return "neutral"

        if brightness > 185 and value > 0.7:
            return "light"

        if saturation > 0.35 and 0.02 <= hue <= 0.17:
            return "warm"

        if saturation > 0.35 and 0.50 <= hue <= 0.75:
            return "cool"

        if saturation > 0.30:
            return "saturated"

        return "midtone"

    @staticmethod
    def _hue_distance(hue_a, hue_b):
        distance = abs(hue_a - hue_b)
        return min(distance, 1 - distance)

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
    def _normalize_palette_with_counts(palette):
        normalized = []

        for item in palette:
            count = 0

            # Current Palette Explorer format:
            # [((r, g, b), pixel_count), ...]
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

    @staticmethod
    def _normalize_palette(palette):
        return [
            entry["rgb"]
            for entry in PaletteMatcher._normalize_palette_with_counts(palette)
        ]

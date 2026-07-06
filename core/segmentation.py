"""
PaletteForge
core/segmentation.py

v0.2.6 - Sprite Segmentation

This is the first real step toward sprite understanding.

Instead of only looking at palette colors, this module detects connected regions
inside the sprite. Later versions will use this to understand:
- body areas
- belly areas
- wings/scarf/accessories
- flame/energy regions
- outline regions

Current goal:
produce reliable region data for debugging and future matching.
"""

from collections import Counter, deque


class SpriteSegmenter:
    def __init__(self, image, alpha_threshold=1):
        self.image = image
        self.alpha_threshold = alpha_threshold

    def analyze(self):
        if self.image is None:
            return {
                "total_regions": 0,
                "regions": [],
                "largest_regions": [],
            }

        # For now, analyze the first frame. GIF-wide segmentation comes later.
        try:
            self.image.seek(0)
        except EOFError:
            pass

        frame = self.image.copy().convert("RGBA")
        width, height = frame.size
        pixels = frame.load()

        visited = set()
        regions = []

        for y in range(height):
            for x in range(width):
                if (x, y) in visited:
                    continue

                r, g, b, a = pixels[x, y]

                if a < self.alpha_threshold:
                    visited.add((x, y))
                    continue

                region = self._flood_fill(frame, pixels, x, y, visited, width, height)

                if region["pixel_count"] > 0:
                    regions.append(region)

        regions = sorted(regions, key=lambda item: item["pixel_count"], reverse=True)

        for index, region in enumerate(regions, start=1):
            region["label"] = f"Region {index:02d}"
            region["likely_role"] = self._classify_region(region, width, height)

        return {
            "total_regions": len(regions),
            "regions": regions,
            "largest_regions": regions[:12],
        }

    def _flood_fill(self, frame, pixels, start_x, start_y, visited, width, height):
        queue = deque()
        queue.append((start_x, start_y))
        visited.add((start_x, start_y))

        color_counter = Counter()
        pixel_count = 0

        min_x = start_x
        max_x = start_x
        min_y = start_y
        max_y = start_y

        edge_pixels = 0
        transparent_touch_pixels = 0

        while queue:
            x, y = queue.popleft()

            r, g, b, a = pixels[x, y]

            if a < self.alpha_threshold:
                continue

            rgb = (r, g, b)
            color_counter[rgb] += 1
            pixel_count += 1

            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)

            if self._is_canvas_edge(x, y, width, height):
                edge_pixels += 1

            if self._touches_transparency(pixels, x, y, width, height):
                transparent_touch_pixels += 1

            for nx, ny in self._neighbors(x, y, width, height):
                if (nx, ny) in visited:
                    continue

                nr, ng, nb, na = pixels[nx, ny]

                if na < self.alpha_threshold:
                    visited.add((nx, ny))
                    continue

                visited.add((nx, ny))
                queue.append((nx, ny))

        dominant_rgb, dominant_count = color_counter.most_common(1)[0]

        bbox_width = max_x - min_x + 1
        bbox_height = max_y - min_y + 1

        edge_ratio = edge_pixels / pixel_count if pixel_count else 0
        transparency_touch_ratio = transparent_touch_pixels / pixel_count if pixel_count else 0

        return {
            "pixel_count": pixel_count,
            "dominant_rgb": dominant_rgb,
            "dominant_hex": self.rgb_to_hex(dominant_rgb),
            "dominant_count": dominant_count,
            "color_count": len(color_counter),
            "colors": dict(color_counter),
            "bbox": (min_x, min_y, max_x, max_y),
            "bbox_width": bbox_width,
            "bbox_height": bbox_height,
            "center_x": (min_x + max_x) / 2,
            "center_y": (min_y + max_y) / 2,
            "edge_ratio": edge_ratio,
            "transparency_touch_ratio": transparency_touch_ratio,
        }

    def _classify_region(self, region, width, height):
        pixel_count = region["pixel_count"]
        bbox_width = region["bbox_width"]
        bbox_height = region["bbox_height"]
        transparency_touch_ratio = region["transparency_touch_ratio"]
        color_count = region["color_count"]
        center_x = region["center_x"]
        center_y = region["center_y"]

        sprite_area = width * height
        coverage = pixel_count / sprite_area if sprite_area else 0

        if coverage > 0.18 and color_count >= 4:
            return "large connected body cluster"

        if transparency_touch_ratio > 0.35 and coverage > 0.04:
            return "outer silhouette / outline-connected area"

        if coverage < 0.01:
            return "small detail / accent"

        if bbox_height > bbox_width * 1.8 and coverage > 0.015:
            return "vertical appendage / tail / limb"

        if bbox_width > bbox_height * 1.8 and coverage > 0.015:
            return "wide appendage / wing / scarf"

        if center_y < height * 0.35:
            return "upper body / head area"

        if center_y > height * 0.70:
            return "lower body / feet / tail area"

        if center_x < width * 0.35 or center_x > width * 0.65:
            return "side appendage / wing / arm"

        return "central body detail"

    def _touches_transparency(self, pixels, x, y, width, height):
        for nx, ny in self._neighbors(x, y, width, height):
            _r, _g, _b, a = pixels[nx, ny]
            if a < self.alpha_threshold:
                return True

        return False

    @staticmethod
    def _is_canvas_edge(x, y, width, height):
        return x == 0 or y == 0 or x == width - 1 or y == height - 1

    @staticmethod
    def _neighbors(x, y, width, height):
        for nx, ny in (
            (x - 1, y),
            (x + 1, y),
            (x, y - 1),
            (x, y + 1),
        ):
            if 0 <= nx < width and 0 <= ny < height:
                yield nx, ny

    @staticmethod
    def rgb_to_hex(color):
        return "#{:02X}{:02X}{:02X}".format(*color)

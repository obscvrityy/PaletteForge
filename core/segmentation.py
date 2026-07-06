"""
PaletteForge
core/segmentation.py

v0.2.9 - Pokémon Smart Match Alpha Segmentation

This module detects connected sprite regions and adds region graph + material
classification metadata for Pokémon-style palette matching.
"""

from collections import Counter, defaultdict, deque


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
                "material_summary": {},
                "graph_summary": {"edge_count": 0},
            }

        try:
            self.image.seek(0)
        except EOFError:
            pass

        frame = self.image.copy().convert("RGBA")
        width, height = frame.size
        pixels = frame.load()

        visited = set()
        regions = []
        pixel_to_region = {}

        for y in range(height):
            for x in range(width):
                if (x, y) in visited:
                    continue

                r, g, b, a = pixels[x, y]

                if a < self.alpha_threshold:
                    visited.add((x, y))
                    continue

                region = self._flood_fill_by_similarity(
                    pixels,
                    x,
                    y,
                    visited,
                    pixel_to_region,
                    width,
                    height,
                    len(regions)
                )

                if region["pixel_count"] > 0:
                    regions.append(region)

        regions = sorted(regions, key=lambda item: item["pixel_count"], reverse=True)

        # Relabel after sorting
        old_to_new = {}
        for new_index, region in enumerate(regions, start=1):
            old_to_new[region["raw_id"]] = new_index - 1
            region["label"] = f"Region {new_index:02d}"
            region["likely_role"] = self._classify_region(region, width, height)
            region["material"] = self._classify_material(region)

        graph_edges = self._build_region_graph(pixels, width, height, pixel_to_region, old_to_new)
        material_summary = Counter(region["material"] for region in regions)

        return {
            "total_regions": len(regions),
            "regions": regions,
            "largest_regions": regions[:12],
            "graph_edges": graph_edges,
            "material_summary": dict(material_summary),
            "graph_summary": {"edge_count": len(graph_edges)},
        }

    def _flood_fill_by_similarity(self, pixels, start_x, start_y, visited, pixel_to_region, width, height, raw_id):
        queue = deque()
        queue.append((start_x, start_y))
        visited.add((start_x, start_y))

        sr, sg, sb, _sa = pixels[start_x, start_y]
        seed_rgb = (sr, sg, sb)

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
            pixel_to_region[(x, y)] = raw_id

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

                # Similar-color segmentation creates smaller, useful regions
                # rather than one giant connected sprite blob.
                if self._color_distance(seed_rgb, (nr, ng, nb)) <= 48:
                    visited.add((nx, ny))
                    queue.append((nx, ny))

        dominant_rgb, dominant_count = color_counter.most_common(1)[0]

        bbox_width = max_x - min_x + 1
        bbox_height = max_y - min_y + 1

        edge_ratio = edge_pixels / pixel_count if pixel_count else 0
        transparency_touch_ratio = transparent_touch_pixels / pixel_count if pixel_count else 0

        return {
            "raw_id": raw_id,
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

    def _build_region_graph(self, pixels, width, height, pixel_to_region, old_to_new):
        edges = Counter()

        for (x, y), raw_region in pixel_to_region.items():
            for nx, ny in self._neighbors(x, y, width, height):
                neighbor_raw = pixel_to_region.get((nx, ny))

                if neighbor_raw is None or neighbor_raw == raw_region:
                    continue

                a = old_to_new.get(raw_region)
                b = old_to_new.get(neighbor_raw)

                if a is None or b is None or a == b:
                    continue

                edge = tuple(sorted((a, b)))
                edges[edge] += 1

        return {
            f"{a}->{b}": count
            for (a, b), count in edges.items()
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

        if coverage > 0.12 and color_count >= 2:
            return "main body cluster"

        if transparency_touch_ratio > 0.38 and coverage > 0.025:
            return "outer silhouette / outline region"

        if coverage < 0.008:
            return "small detail / accent"

        if bbox_height > bbox_width * 1.7 and coverage > 0.012:
            return "vertical appendage / tail / limb"

        if bbox_width > bbox_height * 1.7 and coverage > 0.012:
            return "wide appendage / wing / scarf"

        if center_y < height * 0.35:
            return "upper body / head area"

        if center_y > height * 0.70:
            return "lower body / feet / tail area"

        if center_x < width * 0.35 or center_x > width * 0.65:
            return "side appendage / wing / arm"

        return "central body detail"

    def _classify_material(self, region):
        r, g, b = region["dominant_rgb"]
        brightness = (0.299 * r) + (0.587 * g) + (0.114 * b)
        saturation = self._saturation(region["dominant_rgb"])
        coverage_hint = region["pixel_count"]
        transparency_touch_ratio = region["transparency_touch_ratio"]
        role = region["likely_role"]

        if brightness < 55 and transparency_touch_ratio > 0.22:
            return "line_art"

        if "main body" in role or coverage_hint > 120:
            if saturation < 0.18 and brightness > 120:
                return "belly_light"
            return "main_body"

        if "wing" in role or "appendage" in role or "scarf" in role:
            return "secondary_body"

        if brightness > 175 and saturation < 0.28:
            return "highlight_light"

        if "accent" in role:
            return "accent"

        if saturation > 0.34 and brightness > 80:
            return "colored_surface"

        return "misc"

    def _touches_transparency(self, pixels, x, y, width, height):
        for nx, ny in self._neighbors(x, y, width, height):
            _r, _g, _b, a = pixels[nx, ny]
            if a < self.alpha_threshold:
                return True

        return False

    @staticmethod
    def _saturation(rgb):
        r, g, b = rgb
        max_channel = max(r, g, b)
        min_channel = min(r, g, b)

        if max_channel == 0:
            return 0

        return (max_channel - min_channel) / max_channel

    @staticmethod
    def _color_distance(color_a, color_b):
        return (
            (color_a[0] - color_b[0]) ** 2
            + (color_a[1] - color_b[1]) ** 2
            + (color_a[2] - color_b[2]) ** 2
        ) ** 0.5

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

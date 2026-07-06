"""
PaletteForge
core/region_analyzer.py

v0.2.9 - Region Graph Metadata
"""

from collections import defaultdict


class SpriteRegionAnalyzer:
    def __init__(self, image):
        self.image = image

    def analyze(self):
        if self.image is None:
            return {}

        color_stats = defaultdict(self._new_color_stats)
        frame_count = getattr(self.image, "n_frames", 1)

        for frame_index in range(frame_count):
            try:
                self.image.seek(frame_index)
            except EOFError:
                break

            frame = self.image.copy().convert("RGBA")
            width, height = frame.size
            pixels = frame.load()

            for y in range(height):
                for x in range(width):
                    r, g, b, a = pixels[x, y]

                    if a == 0:
                        continue

                    rgb = (r, g, b)
                    stats = color_stats[rgb]

                    stats["count"] += 1
                    stats["x_sum"] += x
                    stats["y_sum"] += y
                    stats["min_x"] = min(stats["min_x"], x)
                    stats["max_x"] = max(stats["max_x"], x)
                    stats["min_y"] = min(stats["min_y"], y)
                    stats["max_y"] = max(stats["max_y"], y)

                    if self._touches_transparency_or_border(pixels, x, y, width, height):
                        stats["edge_count"] += 1
                    else:
                        stats["interior_count"] += 1

                    for neighbor_rgb in self._neighbor_colors(pixels, x, y, width, height):
                        if neighbor_rgb != rgb:
                            stats["touches"][neighbor_rgb] += 1

        return self._finalize(color_stats)

    def _touches_transparency_or_border(self, pixels, x, y, width, height):
        if x == 0 or y == 0 or x == width - 1 or y == height - 1:
            return True

        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            _r, _g, _b, a = pixels[nx, ny]
            if a == 0:
                return True

        return False

    def _neighbor_colors(self, pixels, x, y, width, height):
        neighbors = []

        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if nx < 0 or ny < 0 or nx >= width or ny >= height:
                continue

            r, g, b, a = pixels[nx, ny]
            if a == 0:
                continue

            neighbors.append((r, g, b))

        return neighbors

    def _finalize(self, color_stats):
        finalized = {}
        total_pixels = sum(stats["count"] for stats in color_stats.values()) or 1

        for rgb, stats in color_stats.items():
            count = stats["count"]
            edge_ratio = stats["edge_count"] / count if count else 0
            interior_ratio = stats["interior_count"] / count if count else 0
            coverage = count / total_pixels
            avg_x = stats["x_sum"] / count if count else 0
            avg_y = stats["y_sum"] / count if count else 0
            bbox_width = max(stats["max_x"] - stats["min_x"] + 1, 1)
            bbox_height = max(stats["max_y"] - stats["min_y"] + 1, 1)

            finalized[rgb] = {
                "count": count,
                "coverage": coverage,
                "edge_count": stats["edge_count"],
                "interior_count": stats["interior_count"],
                "edge_ratio": edge_ratio,
                "interior_ratio": interior_ratio,
                "avg_x": avg_x,
                "avg_y": avg_y,
                "bbox": (stats["min_x"], stats["min_y"], stats["max_x"], stats["max_y"]),
                "bbox_width": bbox_width,
                "bbox_height": bbox_height,
                "touches": dict(stats["touches"]),
                "touch_count": sum(stats["touches"].values()),
            }

        return finalized

    @staticmethod
    def _new_color_stats():
        return {
            "count": 0,
            "edge_count": 0,
            "interior_count": 0,
            "x_sum": 0,
            "y_sum": 0,
            "min_x": 10**9,
            "max_x": -1,
            "min_y": 10**9,
            "max_y": -1,
            "touches": defaultdict(int),
        }

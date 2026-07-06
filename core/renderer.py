"""
PaletteForge
core/renderer.py

v0.1.5 - Live Swap Preview

This module handles applying palette mappings to images and GIF frames.
"""

from PIL import Image


class PaletteRenderer:
    """
    Applies source-to-target palette mappings to sprites and GIF frames.
    """

    def __init__(self, mapping):
        self.mapping = self._normalize_mapping(mapping)

    def render_image(self, image):
        """
        Applies the palette mapping to a single PIL image.

        Args:
            image (PIL.Image): Source image.

        Returns:
            PIL.Image: Recolored RGBA image.
        """
        frame = image.copy().convert("RGBA")
        pixels = frame.load()
        width, height = frame.size

        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]

                if a == 0:
                    continue

                replacement = self.mapping.get((r, g, b))

                if replacement is not None:
                    pixels[x, y] = (
                        replacement[0],
                        replacement[1],
                        replacement[2],
                        a
                    )

        return frame

    def render_gif_frames(self, image):
        """
        Applies the palette mapping to every frame of a GIF or image.

        Args:
            image (PIL.Image): Source GIF or still image.

        Returns:
            tuple[list[PIL.Image], list[int]]: Recolored frames and frame durations.
        """
        frames = []
        durations = []

        frame_count = getattr(image, "n_frames", 1)

        for frame_index in range(frame_count):
            try:
                image.seek(frame_index)
            except EOFError:
                break

            rendered_frame = self.render_image(image)
            frames.append(rendered_frame)
            durations.append(image.info.get("duration", 100))

        return frames, durations

    @staticmethod
    def _normalize_mapping(mapping):
        """
        Accepts PaletteMatcher mapping list and converts it into:
            {(r, g, b): (r, g, b)}
        """
        normalized = {}

        for entry in mapping:
            source = entry.get("source_rgb")
            target = entry.get("target_rgb")

            if source is None or target is None:
                continue

            normalized[
                (int(source[0]), int(source[1]), int(source[2]))
            ] = (
                int(target[0]),
                int(target[1]),
                int(target[2])
            )

        return normalized

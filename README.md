# PaletteForge v0.3.0 — Professional Workspace UI

## Patch type
Professional interface foundation.

## Files included
- `ui/window.py`
- `docs/PRODUCT_ROADMAP.md`
- `docs/FEATURE_BACKLOG.md`
- `docs/CHANGELOG.md`

## What changed
- Reworked the app into a more professional studio-style interface.
- Added a top product bar and priority stack label.
- Added a cleaner left action rail.
- Expanded the center preview/canvas workspace.
- Moved Palette Mapping into a bottom dock so manual mapping has more room.
- Rebuilt the right inspector panel for sprite stats, palettes, and analysis.
- Preserved all existing v0.2.9 functionality.
- Added a placeholder for the upcoming Image + GIF Resizer.

## Replace instructions
Copy the included folders into your PaletteForge project root and replace existing files when prompted.

## Test checklist
1. Run `python main.py`
2. Load a source image/GIF.
3. Load a target image/GIF.
4. Click `Analyze Sprite`.
5. Click `Smart Match`.
6. Click `Live Swap Preview`.
7. Adjust one manual mapping dropdown.
8. Click `Apply Manual Mapping`.
9. Export GIF.

## Commit message
```bash
git add .
git commit -m "feat: add professional workspace ui"
git push
```

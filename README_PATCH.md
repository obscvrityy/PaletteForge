# PaletteForge v0.3.0 — Professional UI Foundation

This patch replaces the prototype interface with the first real PaletteForge creator-workspace layout.

## Replace

- `ui/window.py`

## What changed

- New dark purple/blue professional interface foundation
- Top app bar with product branding and menu structure
- Left library/import/palette area
- Larger before/after preview workspace
- Bottom palette mapping editor area
- Right Smart Match / Sprite Inspector panel
- Dedicated future slot for Image + GIF Resizer
- Existing engine functions preserved: load, analyze, smart match, live preview, manual mapping, export GIF

## Test checklist

1. Run `python main.py`
2. Load Source image/GIF
3. Load Target image/GIF
4. Analyze Sprite
5. Smart Match
6. Live Preview
7. Change one manual mapping dropdown
8. Apply Manual Mapping
9. Export GIF
10. Clear Workspace

## Commit

```bash
git add .
git commit -m "feat: add professional workspace ui"
git push
```

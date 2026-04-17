"""Compose the README hero image from two dashboard screenshots.

Stitches Playwright captures of the Next.js Time Series tab (Vercel) and
the Streamlit Forecasts page side-by-side into a single PNG, with both
halves forced to the exact same dimensions so neither dashboard visually
dominates.

Usage: python scripts/make_hero_image.py

Source captures (live next to the output):
  - docs/images/hero-src-vercel-timeseries.png
  - docs/images/hero-src-streamlit-forecasts.png

Both were captured at a 1440x900 Playwright viewport; the script still
produces equal halves via resize + center-crop even if future captures
use different dimensions.
"""

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
IMG_DIR = ROOT / "docs" / "images"
LEFT_SRC = IMG_DIR / "hero-src-vercel-timeseries.png"
RIGHT_SRC = IMG_DIR / "hero-src-streamlit-forecasts.png"
OUT = IMG_DIR / "hero-dashboards.png"

# Per-half dimensions. 1200x750 preserves a 16:10 viewport aspect ratio
# and gives a final ~2400 px wide image — crisp on GitHub without being
# heavy to commit.
HALF_W = 1200
HALF_H = 750

CANVAS_BG = (10, 10, 10)
DIVIDER = (60, 60, 60)
DIVIDER_PX = 2


def fit_and_center_crop(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Aspect-preserving resize followed by center crop to exact target."""
    src_aspect = img.width / img.height
    tgt_aspect = target_w / target_h
    if src_aspect > tgt_aspect:
        # Source is wider than target — fit height first, then crop width.
        new_h = target_h
        new_w = round(img.width * new_h / img.height)
    else:
        # Source is taller/narrower — fit width first, then crop height.
        new_w = target_w
        new_h = round(img.height * new_w / img.width)
    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))


def main() -> int:
    if not LEFT_SRC.exists() or not RIGHT_SRC.exists():
        raise SystemExit(
            f"missing source screenshots: {LEFT_SRC.name} and/or {RIGHT_SRC.name} "
            f"must exist under {IMG_DIR.relative_to(ROOT)}/."
        )

    left = fit_and_center_crop(Image.open(LEFT_SRC).convert("RGB"), HALF_W, HALF_H)
    right = fit_and_center_crop(Image.open(RIGHT_SRC).convert("RGB"), HALF_W, HALF_H)

    total_w = left.width + DIVIDER_PX + right.width
    canvas = Image.new("RGB", (total_w, left.height), CANVAS_BG)
    canvas.paste(left, (0, 0))
    canvas.paste(
        Image.new("RGB", (DIVIDER_PX, left.height), DIVIDER),
        (left.width, 0),
    )
    canvas.paste(right, (left.width + DIVIDER_PX, 0))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUT, format="PNG", optimize=True)
    size_kb = OUT.stat().st_size / 1024
    print(f"wrote {OUT.relative_to(ROOT)} ({canvas.width}×{canvas.height}, {size_kb:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

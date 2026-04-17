"""Compose the README hero image from two dashboard screenshots.

Reads Playwright captures of the Next.js and Streamlit Statistics pages
from the repo root and writes a side-by-side composite with a thin
divider to `docs/images/hero-dashboards.png`.

Usage: python scripts/make_hero_image.py
"""

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
LEFT_SRC = ROOT / "vercel-stats.png"
RIGHT_SRC = ROOT / "streamlit-prod-stats.png"
OUT = ROOT / "docs" / "images" / "hero-dashboards.png"

# Both dashboards render on dark-ish backgrounds but not identical — use a
# neutral dark canvas behind them so the edges blend rather than jar.
CANVAS_BG = (10, 10, 10)
DIVIDER = (60, 60, 60)
DIVIDER_PX = 2
TARGET_HEIGHT = 900  # Shared height after resize; keeps aspect ratios.
MAX_WIDTH = 2400  # Cap final width; keeps GitHub rendering crisp.


def fit_to_height(img: Image.Image, height: int) -> Image.Image:
    scale = height / img.height
    return img.resize(
        (round(img.width * scale), height),
        Image.Resampling.LANCZOS,
    )


def main() -> int:
    if not LEFT_SRC.exists() or not RIGHT_SRC.exists():
        raise SystemExit(
            f"missing source screenshots: {LEFT_SRC.name} and/or {RIGHT_SRC.name} "
            "must exist at the repo root (see scripts/make_hero_image.py)."
        )

    left = fit_to_height(Image.open(LEFT_SRC).convert("RGB"), TARGET_HEIGHT)
    right = fit_to_height(Image.open(RIGHT_SRC).convert("RGB"), TARGET_HEIGHT)

    total_w = left.width + DIVIDER_PX + right.width
    if total_w > MAX_WIDTH:
        scale = MAX_WIDTH / total_w
        left = fit_to_height(left, round(left.height * scale))
        right = fit_to_height(right, round(right.height * scale))
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

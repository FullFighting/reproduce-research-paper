#!/usr/bin/env python3
"""Upscale a screenshot to high resolution and pixelate player-identifying text.

Built for the Apex Legends spectate-banner screenshot (three player cards):
the default mosaic regions cover the three nameplate headers, and
--include-ids extends the mosaic to the numeric player-ID rows at the bottom.
Regions are fractions of the image size, so they hold at any resolution of
the same layout; pass --region to mosaic arbitrary areas of other images.

Requires Pillow (pip install pillow).

Example:
    python scripts/upscale_and_mosaic.py screenshot.png -o out.png --scale 2 --include-ids
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageFilter
except ImportError:  # pragma: no cover - exercised only without Pillow
    print("error: Pillow is required (pip install pillow)", file=sys.stderr)
    sys.exit(2)

# Fractional (x0, y0, x1, y1) boxes for the three nameplate headers.
NAME_REGIONS: dict[str, tuple[float, float, float, float]] = {
    "player1-name": (0.046, 0.136, 0.176, 0.190),
    "player2-name": (0.356, 0.136, 0.497, 0.190),
    "player3-name": (0.672, 0.136, 0.812, 0.190),
}

# The numeric "ID：..." rows under the second and third cards.
ID_REGIONS: dict[str, tuple[float, float, float, float]] = {
    "player2-id": (0.348, 0.955, 0.515, 0.997),
    "player3-id": (0.666, 0.955, 0.840, 0.997),
}


def parse_region(text: str) -> tuple[float, float, float, float]:
    parts = [float(part) for part in text.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("region must be x0,y0,x1,y1")
    x0, y0, x1, y1 = parts
    if not (0.0 <= x0 < x1 <= 1.0 and 0.0 <= y0 < y1 <= 1.0):
        raise argparse.ArgumentTypeError("region fractions must satisfy 0 <= start < end <= 1")
    return x0, y0, x1, y1


def upscale(image: Image.Image, scale: int, sharpen: bool) -> Image.Image:
    if scale > 1:
        image = image.resize((image.width * scale, image.height * scale), Image.Resampling.LANCZOS)
    if sharpen:
        image = image.filter(ImageFilter.UnsharpMask(radius=2, percent=120, threshold=2))
    return image


def mosaic_region(image: Image.Image, box: tuple[float, float, float, float], block: int) -> None:
    x0 = max(0, int(box[0] * image.width))
    y0 = max(0, int(box[1] * image.height))
    x1 = min(image.width, int(box[2] * image.width))
    y1 = min(image.height, int(box[3] * image.height))
    if x1 - x0 < 2 or y1 - y0 < 2:
        return
    patch = image.crop((x0, y0, x1, y1))
    small = patch.resize(
        (max(1, (x1 - x0) // block), max(1, (y1 - y0) // block)),
        Image.Resampling.BOX,
    )
    image.paste(small.resize(patch.size, Image.Resampling.NEAREST), (x0, y0))


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("input", type=Path, help="input image path")
    parser.add_argument("-o", "--output", type=Path, help="output path (default: <input>_hd_mosaic.png)")
    parser.add_argument("--scale", type=int, default=2, choices=range(1, 5), help="upscale factor (default 2)")
    parser.add_argument("--no-sharpen", action="store_true", help="skip the unsharp-mask pass after upscaling")
    parser.add_argument("--block", type=int, help="mosaic block size in output pixels (default: auto)")
    parser.add_argument("--include-ids", action="store_true", help="also mosaic the numeric player-ID rows")
    parser.add_argument(
        "--region",
        action="append",
        type=parse_region,
        metavar="X0,Y0,X1,Y1",
        help="extra fractional region to mosaic; repeatable, replaces the presets when given with --no-presets",
    )
    parser.add_argument("--no-presets", action="store_true", help="do not mosaic the preset nameplate regions")
    args = parser.parse_args()

    if not args.input.is_file():
        print(f"error: {args.input} is not a file", file=sys.stderr)
        return 1
    output = args.output or args.input.with_name(args.input.stem + "_hd_mosaic.png")

    image = Image.open(args.input).convert("RGB")
    image = upscale(image, args.scale, sharpen=not args.no_sharpen)
    block = args.block or max(8, min(image.width, image.height) // 90)

    regions: dict[str, tuple[float, float, float, float]] = {}
    if not args.no_presets:
        regions.update(NAME_REGIONS)
        if args.include_ids:
            regions.update(ID_REGIONS)
    for index, box in enumerate(args.region or []):
        regions[f"custom-{index}"] = box

    for name, box in regions.items():
        mosaic_region(image, box, block)
        print(f"mosaic applied: {name}")

    image.save(output)
    print(f"saved {output} ({image.width}x{image.height}, scale {args.scale}x, block {block}px)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

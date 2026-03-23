#!/usr/bin/env python3
"""Post-process generated frames into production-ready sprites.

Steps: background removal (rembg) -> magenta despill -> crop -> resize -> bottom-align -> flip

Usage:
    python postprocess.py \
        --input-dir art/generated_raw/player/walk/ \
        --output-dir art/characters/player/ \
        --target-width 40 --target-height 40 \
        --prefix run
"""

import argparse
import sys
from pathlib import Path

from PIL import Image


def parse_args():
    parser = argparse.ArgumentParser(description="Post-process generated frames into sprites")
    parser.add_argument("--input-dir", required=True, help="Directory of generated PNGs")
    parser.add_argument("--output-dir", required=True, help="Output directory for processed sprites")
    parser.add_argument("--target-width", type=int, required=True, help="Final sprite width")
    parser.add_argument("--target-height", type=int, required=True, help="Final sprite height")
    parser.add_argument("--prefix", default="frame", help="Output filename prefix (default: frame)")
    parser.add_argument("--flip", action="store_true", help="Flip horizontally")
    parser.add_argument("--no-rembg", action="store_true", help="Skip rembg, use chroma-key only")
    return parser.parse_args()


def remove_background_rembg(img):
    """Remove background using rembg (ML-based)."""
    try:
        from rembg import remove
        result = remove(img)

        # Check if rembg preserved enough content
        opaque_count = sum(
            1 for y in range(result.size[1]) for x in range(result.size[0])
            if result.getpixel((x, y))[3] > 128
        )
        # Character typically covers 30-50% of the image
        min_pixels = int(result.size[0] * result.size[1] * 0.05)
        if opaque_count < min_pixels:
            print(f"    rembg too aggressive ({opaque_count} opaque pixels), falling back to chroma-key")
            return None

        # Threshold alpha to binary
        pixels = result.load()
        w, h = result.size
        for y in range(h):
            for x in range(w):
                r, g, b, a = pixels[x, y]
                if a > 128:
                    pixels[x, y] = (r, g, b, 255)
                else:
                    pixels[x, y] = (0, 0, 0, 0)

        return result
    except ImportError:
        print("    rembg not installed, using chroma-key only")
        return None


def remove_background_chromakey(img):
    """Remove background using corner-sampled chroma-key."""
    result = img.copy()
    pixels = result.load()
    w, h = result.size

    # Sample background color from corners
    samples = []
    for cx, cy in [(5, 5), (w - 5, 5), (5, h - 5), (w - 5, h - 5)]:
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                px = max(0, min(w - 1, cx + dx))
                py = max(0, min(h - 1, cy + dy))
                samples.append(pixels[px, py][:3])
    bg = tuple(sum(s[c] for s in samples) // len(samples) for c in range(3))

    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            dist = ((r - bg[0]) ** 2 + (g - bg[1]) ** 2 + (b - bg[2]) ** 2) ** 0.5
            if dist < 100:
                pixels[x, y] = (0, 0, 0, 0)
            else:
                pixels[x, y] = (r, g, b, 255)

    return result


def despill_magenta(result):
    """Remove magenta contamination from edge pixels."""
    pixels = result.load()
    w, h = result.size

    # Remove fully magenta pixels
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a == 255 and r > 150 and b > 150 and g < 100:
                pixels[x, y] = (0, 0, 0, 0)

    # Despill magenta-tinted edge pixels
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a == 255 and r > 120 and b > 120 and g < 80:
                for radius in range(1, 15):
                    found = False
                    for dy in range(-radius, radius + 1):
                        for dx in range(-radius, radius + 1):
                            if abs(dx) != radius and abs(dy) != radius:
                                continue
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < w and 0 <= ny < h:
                                nr, ng, nb, na = pixels[nx, ny]
                                if na == 255 and not (nr > 120 and nb > 120 and ng < 80):
                                    pixels[x, y] = (nr, ng, nb, 255)
                                    found = True
                                    break
                        if found:
                            break
                    if found:
                        break

    return result


def process_frame(src_path, out_path, target_w, target_h, flip=False, use_rembg=True):
    """Process a single frame: remove bg, despill, crop, resize, bottom-align."""
    print(f"  Processing: {src_path.name}")

    img = Image.open(src_path).convert("RGBA")

    # Background removal
    result = None
    if use_rembg:
        result = remove_background_rembg(img)
    if result is None:
        result = remove_background_chromakey(img)

    # Despill magenta
    result = despill_magenta(result)

    # Crop to bounding box
    bbox = result.getbbox()
    if bbox is None:
        print(f"    Warning: Empty image after background removal, skipping")
        return False
    cropped = result.crop(bbox)

    # Flip if needed
    if flip:
        cropped = cropped.transpose(Image.FLIP_LEFT_RIGHT)

    # Fit-within resize (never crop sides)
    cw, ch = cropped.size
    scale = min(target_w / cw, target_h / ch)
    new_w = max(1, int(cw * scale))
    new_h = max(1, int(ch * scale))
    resized = cropped.resize((new_w, new_h), Image.NEAREST)

    # Bottom-align on target canvas
    canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    paste_x = (target_w - new_w) // 2
    paste_y = target_h - new_h  # bottom-align
    canvas.paste(resized, (paste_x, paste_y))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)
    print(f"    Saved: {out_path} ({target_w}x{target_h})")
    return True


def main():
    args = parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    if not input_dir.is_dir():
        print(f"Error: Input directory not found: {input_dir}", file=sys.stderr)
        sys.exit(1)

    # Find all image files, sorted
    image_files = sorted(
        p for p in input_dir.iterdir()
        if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")
    )

    if not image_files:
        print(f"Error: No image files found in {input_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Input:  {input_dir} ({len(image_files)} files)")
    print(f"Output: {output_dir}")
    print(f"Target: {args.target_width}x{args.target_height}")
    print(f"Prefix: {args.prefix}")
    if args.flip:
        print("Flip:   horizontal")
    print()

    success_count = 0
    for i, src_path in enumerate(image_files, 1):
        frame_num = f"{i:02d}"
        out_path = output_dir / f"{args.prefix}_{frame_num}.png"
        if process_frame(
            src_path, out_path,
            args.target_width, args.target_height,
            flip=args.flip,
            use_rembg=not args.no_rembg,
        ):
            success_count += 1

    print(f"\nDone! Processed {success_count}/{len(image_files)} frames.")


if __name__ == "__main__":
    main()

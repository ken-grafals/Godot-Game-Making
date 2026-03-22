#!/usr/bin/env python3
"""Generate game art using OpenAI's image generation API.

Usage:
    # Basic generation
    python generate_art.py --prompt "A goblin enemy" --output enemy.png

    # With reference images (uses edit endpoint)
    python generate_art.py --prompt "Hurt version of this character" \
        --reference ref.png --output enemy_hurt.png

    # Multiple variations
    python generate_art.py --prompt "A goblin enemy" --output enemy.png --count 3
"""

import argparse
import base64
import os
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate game art using OpenAI's image generation API"
    )
    parser.add_argument(
        "--prompt", required=True, help="Text description of the image to generate"
    )
    parser.add_argument(
        "--reference",
        nargs="+",
        help="One or more reference image paths (triggers edit endpoint)",
    )
    parser.add_argument(
        "--output", required=True, help="Output file path for the generated image"
    )
    parser.add_argument(
        "--size",
        default="1024x1024",
        choices=["1024x1024", "1024x1536", "1536x1024", "auto"],
        help="Image dimensions (default: 1024x1024)",
    )
    parser.add_argument(
        "--quality",
        default="medium",
        choices=["low", "medium", "high"],
        help="Image quality (default: medium)",
    )
    parser.add_argument(
        "--model",
        default="gpt-image-1",
        help="Model to use (default: gpt-image-1)",
    )
    parser.add_argument(
        "--background",
        default="transparent",
        choices=["transparent", "opaque"],
        help="Background type (default: transparent)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of variations to generate (default: 1)",
    )
    return parser.parse_args()


def get_client():
    """Create OpenAI client, checking for API key."""
    api_key = os.environ.get("GODOT_OPENAI_API_KEY")
    if not api_key:
        print("Error: GODOT_OPENAI_API_KEY environment variable not set.", file=sys.stderr)
        print("Add to ~/.zshrc: export GODOT_OPENAI_API_KEY='sk-proj-...'", file=sys.stderr)
        sys.exit(1)

    try:
        from openai import OpenAI
    except ImportError:
        print("Error: openai package not installed.", file=sys.stderr)
        print("Run: pip install openai", file=sys.stderr)
        sys.exit(1)

    return OpenAI(api_key=api_key)


def save_image(b64_data: str, output_path: Path):
    """Save base64-encoded image data to a file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image_bytes = base64.b64decode(b64_data)
    output_path.write_bytes(image_bytes)
    print(f"Saved: {output_path} ({len(image_bytes)} bytes)")


def generate_image(client, args):
    """Generate image(s) from text prompt."""
    result = client.images.generate(
        model=args.model,
        prompt=args.prompt,
        n=args.count,
        size=args.size,
        quality=args.quality,
        background=args.background,
        output_format="png",
    )
    return result.data


def edit_image(client, args):
    """Edit/generate image using reference images."""
    image_files = []
    for ref_path in args.reference:
        ref = Path(ref_path)
        if not ref.exists():
            print(f"Error: Reference image not found: {ref}", file=sys.stderr)
            sys.exit(1)
        image_files.append(open(ref, "rb"))

    try:
        result = client.images.edit(
            model=args.model,
            image=image_files[0],
            prompt=args.prompt,
            n=args.count,
            size=args.size,
            quality=args.quality,
        )
    finally:
        for f in image_files:
            f.close()

    return result.data


def main():
    args = parse_args()
    client = get_client()
    output_path = Path(args.output)

    print(f"Model: {args.model}")
    print(f"Prompt: {args.prompt}")
    print(f"Size: {args.size} | Quality: {args.quality} | Background: {args.background}")

    if args.reference:
        print(f"Reference images: {', '.join(args.reference)}")
        images = edit_image(client, args)
    else:
        images = generate_image(client, args)

    if len(images) == 1:
        save_image(images[0].b64_json, output_path)
    else:
        for i, img in enumerate(images, 1):
            stem = output_path.stem
            suffix = output_path.suffix
            numbered_path = output_path.parent / f"{stem}_{i:03d}{suffix}"
            save_image(img.b64_json, numbered_path)

    print("Done.")


if __name__ == "__main__":
    main()

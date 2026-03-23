#!/usr/bin/env python3
"""Generate animation frames using fal.ai with IP-Adapter + ControlNet pose control.

Usage:
    python generate_frames.py \
        --reference character_ref.png \
        --poses poses/walk_4frame/ \
        --prompt "SNES pixel art boy, white gi, side view" \
        --output-dir output/
"""

import argparse
import os
import sys
from pathlib import Path

import fal_client
import requests


# Default model and component paths
DEFAULT_MODEL = "fal-ai/flux-general"
DEFAULT_IP_ADAPTER_PATH = "XLabs-AI/flux-ip-adapter"
DEFAULT_IMAGE_ENCODER_PATH = "openai/clip-vit-large-patch14"
DEFAULT_CONTROLNET_UNION_PATH = "InstantX/FLUX.1-dev-Controlnet-Union"

# Known per-megapixel rates (USD) for cost estimation
MODEL_RATES = {
    "fal-ai/flux-general": 0.075,
    "fal-ai/flux/schnell": 0.003,
    "fal-ai/flux/dev": 0.025,
}
DEFAULT_RATE = 0.075  # fallback


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate animation frames using fal.ai with IP-Adapter + ControlNet"
    )
    parser.add_argument(
        "--reference", required=True, help="Character reference image for IP-Adapter"
    )
    parser.add_argument(
        "--poses", required=True, help="Directory of OpenPose guide PNGs"
    )
    parser.add_argument(
        "--prompt", required=True, help="Positive prompt (character/style description)"
    )
    parser.add_argument(
        "--output-dir", required=True, help="Output directory for generated frames"
    )
    parser.add_argument("--width", type=int, default=512, help="Generation width (default: 512)")
    parser.add_argument("--height", type=int, default=512, help="Generation height (default: 512)")
    parser.add_argument(
        "--ip-adapter-weight", type=float, default=0.6,
        help="IP-Adapter influence 0.0-1.0 (default: 0.6)",
    )
    parser.add_argument(
        "--controlnet-weight", type=float, default=0.7,
        help="ControlNet pose strength 0.0-2.0 (default: 0.7)",
    )
    parser.add_argument("--steps", type=int, default=28, help="Inference steps (default: 28)")
    parser.add_argument("--cfg-scale", type=float, default=3.5, help="Guidance scale (default: 3.5)")
    parser.add_argument("--seed", type=int, default=None, help="Seed (default: random)")
    parser.add_argument(
        "--model", default=DEFAULT_MODEL,
        help=f"fal.ai model endpoint (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print arguments without submitting",
    )
    return parser.parse_args()


def upload_image(image_path):
    """Upload a local image to fal.ai CDN. Returns the access URL."""
    image_path = Path(image_path)
    if not image_path.exists():
        print(f"Error: Image not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    url = fal_client.upload_file(image_path)
    return url


def build_arguments(*, prompt, reference_url, pose_url,
                    ip_adapter_weight, controlnet_weight, width, height,
                    steps, cfg, seed):
    """Build the fal.ai arguments dict for flux-general."""
    args = {
        "prompt": prompt,
        "image_size": {"width": width, "height": height},
        "num_inference_steps": steps,
        "guidance_scale": cfg,
        "num_images": 1,
        "output_format": "png",
        "enable_safety_checker": False,
        "ip_adapters": [
            {
                "path": DEFAULT_IP_ADAPTER_PATH,
                "image_encoder_path": DEFAULT_IMAGE_ENCODER_PATH,
                "image_url": reference_url,
                "scale": ip_adapter_weight,
                "weight_name": "ip_adapter.safetensors",
            }
        ],
        "controlnet_unions": [
            {
                "path": DEFAULT_CONTROLNET_UNION_PATH,
                "controls": [
                    {
                        "control_image_url": pose_url,
                        "control_mode": "pose",
                        "conditioning_scale": controlnet_weight,
                    }
                ],
            }
        ],
    }

    if seed is not None:
        args["seed"] = seed

    return args


def estimate_cost(width, height, model, num_images=1):
    """Estimate cost from resolution and model pricing."""
    megapixels = (width * height) / 1_000_000
    rate = MODEL_RATES.get(model, DEFAULT_RATE)
    return megapixels * rate * num_images


def download_image(url, output_path):
    """Download an image from a URL to a local path."""
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(resp.content)
    return len(resp.content)


def main():
    args = parse_args()

    if "FAL_KEY" not in os.environ:
        print("Error: FAL_KEY not set. Add it to ~/.zshrc and source it.", file=sys.stderr)
        sys.exit(1)

    # Collect pose images
    poses_dir = Path(args.poses)
    if not poses_dir.is_dir():
        print(f"Error: Poses directory not found: {poses_dir}", file=sys.stderr)
        sys.exit(1)

    pose_files = sorted(
        p for p in poses_dir.iterdir()
        if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")
    )

    if not pose_files:
        print(f"Error: No image files found in {poses_dir}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Model:        {args.model}")
    print(f"Reference:    {args.reference}")
    print(f"Poses:        {len(pose_files)} files in {poses_dir}")
    print(f"Prompt:       {args.prompt}")
    print(f"Output:       {output_dir}")
    print(f"Resolution:   {args.width}x{args.height}")
    print(f"Weights:      IP-Adapter={args.ip_adapter_weight}, ControlNet={args.controlnet_weight}")
    print()

    # Upload reference image once
    print("Uploading reference image to fal.ai CDN...")
    ref_url = upload_image(args.reference)
    print(f"  URL: {ref_url}")

    if args.dry_run:
        print("\n--- DRY RUN: uploading one pose to show full arguments ---")
        pose_url = upload_image(pose_files[0])
        arguments = build_arguments(
            prompt=args.prompt,
            reference_url=ref_url,
            pose_url=pose_url,
            ip_adapter_weight=args.ip_adapter_weight,
            controlnet_weight=args.controlnet_weight,
            width=args.width,
            height=args.height,
            steps=args.steps,
            cfg=args.cfg_scale,
            seed=args.seed,
        )
        import json
        print(json.dumps(arguments, indent=2))
        cost = estimate_cost(args.width, args.height, args.model)
        print(f"\nEstimated cost per frame: ${cost:.4f}")
        print(f"Estimated total ({len(pose_files)} frames): ${cost * len(pose_files):.4f}")
        return

    # Generate each frame
    total_cost = 0.0
    downloaded = []

    for i, pose_path in enumerate(pose_files, 1):
        frame_num = f"{i:02d}"
        print(f"\n--- Frame {frame_num}/{len(pose_files):02d}: {pose_path.name} ---")

        # Upload pose image
        print("  Uploading pose image...")
        pose_url = upload_image(pose_path)

        # Build arguments
        arguments = build_arguments(
            prompt=args.prompt,
            reference_url=ref_url,
            pose_url=pose_url,
            ip_adapter_weight=args.ip_adapter_weight,
            controlnet_weight=args.controlnet_weight,
            width=args.width,
            height=args.height,
            steps=args.steps,
            cfg=args.cfg_scale,
            seed=args.seed,
        )

        # Submit and wait for result
        print("  Generating...")
        result = fal_client.subscribe(args.model, arguments=arguments)

        # Download output image
        img_url = result["images"][0]["url"]
        out_path = output_dir / f"frame_{frame_num}.png"
        size = download_image(img_url, out_path)

        # Cost
        frame_cost = estimate_cost(args.width, args.height, args.model)
        total_cost += frame_cost

        print(f"  Saved: {out_path} ({size:,} bytes)")
        print(f"  Frame {frame_num}/{len(pose_files):02d}: {pose_path.name} — ${frame_cost:.4f}")
        downloaded.append(out_path)

    # Summary
    print(f"\n{'─' * 40}")
    print(f"Generated {len(downloaded)} frame(s) in {output_dir}")
    print(f"Total: {len(downloaded)} frames — ${total_cost:.4f}")
    print(f"{'─' * 40}")


if __name__ == "__main__":
    main()

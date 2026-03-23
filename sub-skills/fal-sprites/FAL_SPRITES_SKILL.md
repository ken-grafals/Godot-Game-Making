# fal.ai Sprite Animation Pipeline

**Status: Work in progress.** Pose control (ControlNet Union) is unreliable on FLUX. Use OpenAI image gen for production art until this is resolved.

You are assisting with generating consistent multi-frame sprite animations using fal.ai's cloud-hosted models. This skill uses FLUX.1 + IP-Adapter + ControlNet Union (pose mode) to produce walk cycles, run cycles, and other animations where character identity must stay consistent across frames.

## When to Use This Sub-Skill

Use this for:
- **Multi-frame animations** (walk cycles, run cycles, attack sequences) where character consistency matters
- **Pose-controlled generation** where you need specific body positions per frame

Use the OpenAI image gen sub-skill instead for:
- Quick single-frame concepts, backgrounds, items
- Production art (until ControlNet pose issues are resolved)

## Architecture

The pipeline separates three concerns:

- **IP-Adapter** answers: "Who is this character?" (fed a reference image)
- **ControlNet Union (pose)** answers: "What pose is this frame?" (fed a stick figure per frame)
- **Prompt** answers: "What style and rendering do I want?"
- **FLUX.1 model** renders the actual image (running on fal.ai cloud GPU)

Each animation frame is generated separately with the same character reference + different pose guide.

## Prerequisites

1. **fal.ai account** with API key
2. **Environment variable** set in `~/.zshrc`:
   - `FAL_KEY` — your fal.ai API key

## Generate Frames CLI

Use `~/Workspace/Godot/Godot-Game-Making/sub-skills/fal-sprites/scripts/generate_frames.py` to generate animation frames:

```bash
# Activate the skill's venv
source ~/Workspace/Godot/Godot-Game-Making/sub-skills/fal-sprites/.venv/bin/activate

# Generate a 4-frame walk cycle
python ~/Workspace/Godot/Godot-Game-Making/sub-skills/fal-sprites/scripts/generate_frames.py \
  --reference art/characters/player/idle.png \
  --poses ~/Workspace/Godot/Godot-Game-Making/sub-skills/fal-sprites/poses/walk_4frame/ \
  --prompt "SNES pixel art boy character, white karate gi, black belt, curly brown hair, brown sandals, side view, 16-bit game sprite, clean silhouette" \
  --output-dir art/generated_raw/player/walk/ \
  --width 512 --height 512
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--reference` | (required) | Character reference image for IP-Adapter |
| `--poses` | (required) | Directory of OpenPose guide PNGs |
| `--prompt` | (required) | Stable character/style description |
| `--output-dir` | (required) | Where to save generated frames |
| `--width` | `512` | Generation width |
| `--height` | `512` | Generation height |
| `--ip-adapter-weight` | `0.6` | IP-Adapter influence (0.0-1.0) |
| `--controlnet-weight` | `0.7` | ControlNet pose strength (0.0-2.0) |
| `--steps` | `28` | Inference steps |
| `--cfg-scale` | `3.5` | Guidance scale |
| `--seed` | random | Seed for reproducibility |
| `--model` | `fal-ai/flux-general` | fal.ai model endpoint |
| `--dry-run` | false | Print arguments without submitting |

**Output:** One PNG per pose file, downloaded from fal.ai. Prints per-frame and total estimated cost.

### Tuning Weights

| Problem | Fix |
|---------|-----|
| Every frame looks like the same still image | Lower IP-Adapter weight (try 0.4) |
| Character identity drifts between frames | Raise IP-Adapter weight (try 0.8) |
| Pose is ignored, character is static | Raise ControlNet weight (try 1.0) |
| Pose is right but character looks different | Lower ControlNet weight (try 0.5) |
| Both are fighting — muddy output | Lower both slightly (0.5 / 0.6) |

Start with IP-Adapter 0.6 + ControlNet 0.7 and adjust from there.

## Post-Processing

After generating and curating frames, run post-processing to make production-ready sprites:

```bash
python ~/Workspace/Godot/Godot-Game-Making/sub-skills/fal-sprites/scripts/postprocess.py \
  --input-dir art/generated_raw/player/walk/ \
  --output-dir art/characters/player/ \
  --target-width 40 --target-height 40 \
  --prefix run
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--input-dir` | (required) | Directory of generated PNGs |
| `--output-dir` | (required) | Where to save processed sprites |
| `--target-width` | (required) | Final sprite width |
| `--target-height` | (required) | Final sprite height |
| `--prefix` | `frame` | Output filename prefix (e.g., `run` → `run_01.png`) |
| `--flip` | false | Flip horizontally |
| `--no-rembg` | false | Skip rembg, use chroma-key only |

Pipeline steps:
1. Background removal with rembg (ML-based, falls back to chroma-key)
2. Magenta despill for edge pixels
3. Crop to bounding box
4. Fit-within resize to target canvas (never crops sides)
5. Bottom-align on transparent canvas (feet touch bottom edge)
6. Optional horizontal flip

## Pose Guides

### Included Poses

Pre-made pose guides in `~/Workspace/Godot/Godot-Game-Making/sub-skills/fal-sprites/poses/`:
- `walk_4frame/` — 4-frame walk cycle (contact, recoil, passing, high-point)

### Creating Custom Poses

Use the pose generator script:

```bash
python ~/Workspace/Godot/Godot-Game-Making/sub-skills/fal-sprites/scripts/create_poses.py
```

Or create your own 512x512 PNGs with:
- **Black background**
- **Colored circles** at joint positions (following OpenPose color convention)
- **Colored lines** connecting joints

The pose only needs to be approximate — ControlNet provides guidance, not pixel-perfect control.

## Art Pipeline

Same three-stage pipeline as the OpenAI-based workflow:

```
art/generated_raw/       # All fal.ai output (many variations) — gitignored
art/generated_selected/  # Human-curated best picks
art/characters/          # Production-ready, referenced by SpriteFrames .tres
```

1. **Generate** multiple variations into `generated_raw/`
2. **Curate** — pick the best results
3. **Process** — run postprocess.py to clean up, resize, align
4. **Deploy** — copy final PNGs to `art/characters/<name>/`

## Prompt Templates

FLUX works best with descriptive prompts. Include quality tokens.

**Character sprite (with IP-Adapter + ControlNet):**
```
SNES pixel art [character description], [outfit details], side view, [pose hint],
16-bit game sprite, clean silhouette, readable at small scale, masterpiece, best quality
```

**Tips:**
- Don't describe the pose in detail — ControlNet handles that
- Don't describe the character identity in detail — IP-Adapter handles that
- Focus the prompt on style and rendering
- **Do NOT use negative prompts** — they cause pipeline failures when combined with IP-Adapter + ControlNet on FLUX

## Before Generating: Checklist

1. **Character design doc exists** in project's `docs/` directory
2. **Reference image** ready (existing sprite or concept art — must be 512x512+, not tiny production sprites)
3. **Pose guides** created for the target animation
4. **Check sprite facing direction** — read the character's script to see which way the base sprite should face
5. **Check sprite dimensions** — read existing sprites or CollisionShape2D
6. **FAL_KEY** is set in environment

## Performance Notes

- Generation: ~5-15s per frame at 512x512
- A 4-frame walk cycle typically costs ~$0.04-0.08
- No cold starts — fal.ai models are always warm

## Troubleshooting

| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Check `FAL_KEY` is set correctly in `~/.zshrc` |
| Model not found | Check model endpoint ID (e.g., `fal-ai/flux-general`) |
| Character looks nothing like reference | IP-Adapter weight too low (try 0.7-0.8), or reference image too small (needs 512x512+) |
| Pose completely ignored | ControlNet weight too low (try 0.9-1.0) — note: ControlNet Union pose mode is unreliable on FLUX |
| Image is blurry or low quality | Increase `--steps` (try 35-40) |
| 422 pipeline load failure | Remove `negative_prompt` — it breaks IP-Adapter + ControlNet combo |

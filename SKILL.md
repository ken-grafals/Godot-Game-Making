---
name: godot-game-making
description: Triggers when user is making a Godot game, needs game art, wants to generate images for a Godot project, or asks about Godot game development with Claude Code
user-invocable: true
---

# Godot Game Making with Claude Code

You are assisting with Godot 4.x game development. This skill covers game development workflows and AI art generation.

## Godot + Claude Code Workflow

### Project Structure

Godot projects should follow this layout:

```
scenes/          # .tscn scene files
scripts/         # .gd script files
art/characters/  # Sprite PNGs + .tres SpriteFrames resources
assets/          # Sounds, fonts, UI
test/unit/       # GdUnit4 unit tests
test/integration/# Scene/signal tests
addons/          # Plugins (GdUnit4, etc.)
```

Always check for a project-level `CLAUDE.md` — it will have project-specific conventions, collision layers, input maps, and mechanics.

### Sprite System: AnimatedSprite2D + SpriteFrames

The standard pattern for 2D character art:

1. **PNGs** in `art/characters/<name>/` — one file per animation frame
2. **SpriteFrames .tres** references those PNGs and defines animations (idle, run, jump, attack, hurt, etc.)
3. **AnimatedSprite2D** node uses the SpriteFrames resource
4. **Scripts** call `animated_sprite.play("animation_name")`

**To replace placeholder art with real art:** just swap the PNGs at the same paths. The SpriteFrames resource and scripts don't need changes.

### Testing with GdUnit4

```bash
# Run all tests headlessly
/Applications/Godot.app/Contents/MacOS/Godot --path . -s addons/gdUnit4/bin/GdUnitCmdTool.gd --headless

# Run specific test file
/Applications/Godot.app/Contents/MacOS/Godot --path . -s addons/gdUnit4/bin/GdUnitCmdTool.gd -a test/unit/test_player.gd --headless
```

Tests extend `GdUnitTestSuite`. Use `auto_free()` for cleanup, `simulate()` for physics frames.

### Key Patterns

- **Collision layers:** Use separate bits for World (1), Player (2), Enemy (4), PlayerAttack (8), EnemyAttack (16)
- **Input actions:** Define in Input Map, use `Input.is_action_pressed("action_name")` in scripts
- **Signals:** Use for cross-system communication (e.g., player damage → HUD update)
- **Export vars:** `@export var speed: float = 300.0` for designer-tunable values

## AI Art Generation

Two tools are available for generating game art:

### 1. Python Script (Repeatable Production Jobs)

Use `~/Workspace/Godot-Game-Making/scripts/generate_art.py` for batch/repeatable generation:

```bash
# Basic generation
python ~/Workspace/Godot-Game-Making/scripts/generate_art.py \
  --prompt "A goblin enemy for a 2D platformer, side view, transparent background" \
  --output art/generated_raw/enemies/goblin_001.png \
  --size 1024x1024 \
  --quality medium \
  --background transparent

# With reference image (edit endpoint)
python ~/Workspace/Godot-Game-Making/scripts/generate_art.py \
  --prompt "Create a hurt version of this character, same style" \
  --reference art/characters/enemy/idle.png \
  --output art/generated_raw/enemies/goblin_hurt_001.png

# Multiple variations
python ~/Workspace/Godot-Game-Making/scripts/generate_art.py \
  --prompt "A treasure chest item" \
  --output art/generated_raw/items/chest.png \
  --count 3
```

**Options:**
- `--prompt` — text description (required)
- `--reference` — reference image path(s), triggers edit endpoint
- `--output` — output file path (required)
- `--size` — 1024x1024, 1024x1536, 1536x1024, auto (default: 1024x1024)
- `--quality` — low, medium, high (default: medium)
- `--model` — model name (default: gpt-image-1)
- `--background` — transparent, opaque (default: transparent)
- `--count` — number of variations (default: 1)

Requires `GODOT_OPENAI_API_KEY` environment variable and `pip install openai`.

#### Recommended generation settings

| Parameter | Value | Notes |
|-----------|-------|-------|
| **model** | `gpt-image-1` | Best model for game art generation |
| **size** | `1024x1024` | Standard square output; downscaled in post-processing |
| **quality** | `medium` | Best cost/quality balance. `high` is not worth the extra cost for sprites that get downscaled to 28x48 |

Always use these defaults unless there's a specific reason to deviate.

### 2. MCP Server (Conversational Exploration)

If the `openai-gpt-image` MCP server is configured, two tools are available:

- **`create-image`** — generate from text prompt. Use for quick concept exploration in conversation.
- **`edit-image`** — modify existing images with a prompt and optional mask. Use for iterating on existing art.

**When to use script vs MCP:**
- **Script:** Repeatable jobs, batch generation, CI/automation, precise output paths
- **MCP:** Quick exploration, "show me what X looks like", iterating in conversation

### Art Pipeline: Raw → Selected → Production

```
art/generated_raw/       # All AI output (many variations) — gitignored
art/generated_selected/  # Human-curated best picks
art/characters/          # Production-ready, referenced by SpriteFrames .tres
```

1. **Generate** multiple variations into `generated_raw/`
2. **Curate** — pick the best results, move to `generated_selected/`
3. **Process** — remove background, resize, flip, ensure consistency across frames
4. **Deploy** — copy final PNGs to `art/characters/<name>/`, replacing placeholders

### Before Generating: Write a Character Design Doc

Before generating any sprites for a new character, write a `.md` file in the project's `docs/` directory describing the character. Include:

- Physical description (hair, skin, build, expression)
- Outfit details (colors, accessories)
- Art style and proportions (e.g., chibi, SNES pixel art)
- Sprite dimensions and facing direction
- List of animations needed
- Key visual details that MUST be preserved across all frames

This doc serves as the prompt reference for all future frame generation and ensures consistency.

### `create-image` Still Needs Background Removal

Even though `create-image` supports `background: transparent`, the AI often produces a faint colored background glow or halo instead of true transparency. **Always run rembg on the output regardless of whether you requested transparent background.** Don't assume the background is clean — verify by checking pixel alpha values.

### Generating Animation Frames (Sprite Sheets)

When generating multiple frames for an animation (e.g., a 4-frame walk cycle), follow these rules:

#### Use `edit-image` with a reference image for consistency

Always use `edit-image` (MCP) or `--reference` (script) to pass a reference image. This is critical for keeping the character's proportions, colors, and style consistent across frames. Do NOT use `create-image` without a reference for animation frames — the results will be too inconsistent.

#### Prompt for a chroma-key background, remove with `rembg`

The `edit-image` endpoint does NOT support `background: transparent`. Prompt for a solid magenta background to help the AI keep the character distinct from the background:

```
... on a solid bright magenta (#FF00FF) background. The entire background must be uniform #FF00FF with no gradients.
```

**For background removal, use `rembg` (ML-based), NOT color-matching.** The AI never produces truly uniform backgrounds — it generates gradients, color shifts, and pinkish variations that defeat chroma-key removal. Dark characters are especially problematic because their colors overlap with dark background gradients. `rembg` uses a neural network (U2Net) to segment foreground from background regardless of color similarity.

```python
from rembg import remove
result = remove(img)  # returns RGBA with transparent background
```

Install: `pip install "rembg[cpu]"` (available in `~/Workspace/Godot-Game-Making/.venv/`). First run downloads a ~176MB model to `~/.u2net/`.

#### Check sprite facing direction BEFORE generating

**This is a common mistake.** Before generating frames, read the character's script to determine which direction the sprite should face by default:

- If the script uses `flip_h = direction > 0.0` (flip when moving right), the base sprite must face **LEFT**
- If the script uses `flip_h = direction < 0.0` (flip when moving left), the base sprite must face **RIGHT**
- If unsure, check what direction existing placeholder sprites face

Generate sprites facing the direction the script expects, OR generate facing either direction and flip all PNGs horizontally during post-processing. Flipping during post-processing (via `Image.FLIP_LEFT_RIGHT` in Pillow) is reliable and easy.

#### Check sprite dimensions match the game

Read the existing placeholder PNGs or the CollisionShape2D to determine the expected sprite size (e.g., 28x48). AI generates at 1024x1024 minimum, so post-processing must:

1. Remove background with `rembg` (ML-based — never use color-matching)
2. Crop to bounding box of non-transparent content
3. Scale to **fit within** the target canvas (`min(TARGET_W/cw, TARGET_H/ch)`) — never crop sides
4. Place on target-size transparent canvas — **bottom-aligned** vertically, centered horizontally
5. Flip horizontally if needed for correct facing direction

**Bottom-alignment is critical.** Characters must have their feet touching the bottom edge of the sprite canvas. Godot aligns the collision shape bottom with the ground; if the sprite is vertically centered instead of bottom-aligned, the character will appear to float above the platform.

#### Use the best frame as reference for problem frames

If one frame comes out inconsistent (wrong colors, different proportions), regenerate it using a *good frame* as the reference image instead of the original concept art. This produces better style matching since the good frame is already in the right pose style.

### Post-Processing Script Pattern

```python
from PIL import Image
from rembg import remove

img = Image.open(src).convert("RGBA")

# Step 1: Background removal — try rembg, fall back to chroma-key
result = remove(img)

# Check if rembg preserved enough character content
opaque_count = sum(1 for y in range(result.size[1]) for x in range(result.size[0])
                   if result.getpixel((x, y))[3] > 128)
# Compare to expected: character typically covers 30-50% of 1024x1024 = ~300k-500k pixels
if opaque_count < 200000:
    # rembg removed too much — fall back to chroma-key
    print(f"rembg too aggressive ({opaque_count} pixels), using chroma-key fallback")
    result = img.copy()
    pixels = result.load()
    w, h = result.size
    # Sample background color from corners
    samples = []
    for cx, cy in [(5, 5), (w-5, 5), (5, h-5), (w-5, h-5)]:
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                px, py = max(0, min(w-1, cx+dx)), max(0, min(h-1, cy+dy))
                samples.append(pixels[px, py][:3])
    bg = tuple(sum(s[c] for s in samples) // len(samples) for c in range(3))
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            dist = ((r-bg[0])**2 + (g-bg[1])**2 + (b-bg[2])**2) ** 0.5
            if dist < 100:
                pixels[x, y] = (0, 0, 0, 0)
            else:
                pixels[x, y] = (r, g, b, 255)
else:
    # rembg succeeded — threshold alpha to binary + despill
    pixels = result.load()
    w, h = result.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a > 128:
                pixels[x, y] = (r, g, b, 255)
            else:
                pixels[x, y] = (0, 0, 0, 0)

# Step 2: Remove opaque magenta pixels
pixels = result.load()
w, h = result.size
for y in range(h):
    for x in range(w):
        r, g, b, a = pixels[x, y]
        if a == 255 and r > 150 and b > 150 and g < 100:
            pixels[x, y] = (0, 0, 0, 0)

# Step 3: Despill magenta-tinted opaque pixels
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

# Step 4: Crop, flip, fit-within, bottom-align
bbox = result.getbbox()
cropped = result.crop(bbox)
cropped = cropped.transpose(Image.FLIP_LEFT_RIGHT)  # if sprite needs to face opposite direction

cw, ch = cropped.size
scale = min(TARGET_W / cw, TARGET_H / ch)  # fit WITHIN — never crop sides
new_w = int(cw * scale)
new_h = int(ch * scale)
resized = cropped.resize((new_w, new_h), Image.NEAREST)

canvas = Image.new("RGBA", (TARGET_W, TARGET_H), (0, 0, 0, 0))
paste_x = (TARGET_W - new_w) // 2
paste_y = TARGET_H - new_h  # bottom-align feet to ground
canvas.paste(resized, (paste_x, paste_y))
canvas.save(out_path)
```

Requires: `pip install Pillow "rembg[cpu]"` (available in `~/Workspace/Godot-Game-Making/.venv/`).

**Key insight:** `rembg` doesn't work equally well on all frames. Sometimes it removes too much of the character (especially dark characters on dark-tinted backgrounds). The pipeline should check the result and fall back to chroma-key removal when `rembg` is too aggressive. Chroma-key works well when the background is cleanly magenta and the character has no magenta colors.

**Why the despill step matters:** `rembg` correctly removes the background but preserves semi-transparent anti-aliased edge pixels. Those pixels carry the background's RGB color (magenta) in their color channels. When resized, NEAREST/LANCZOS blends these into visible color fringe. The despill replaces edge pixel colors with the nearest opaque character pixel, preserving the alpha shape but removing the background color contamination.

**Always verify after processing:** Count pixels where R>150, B>150, G<100 — should be 0.

### Prompt Templates for 2D Platformer Art

**Character (concept / first generation):**
```
A [description] character for a 2D platformer game. [Physical details].
Side view, [art style] style, transparent background.
Game character, clean silhouette, readable at small scale.
```

**Character (animation frame with reference — use with edit-image):**
```
Same [character name] character as the reference. Same exact style, colors, proportions,
and pixel size. [Physical details that must be preserved, e.g., "bright yellow glowing eyes"].
[Pose description for this specific frame].
On a solid bright magenta (#FF00FF) background. The entire background must be uniform
#FF00FF with no gradients.
Side view, facing [direction]. Frame [N] of a [total]-frame [animation] cycle.
```

**Environment/Background:**
```
A [description] environment for a 2D platformer game.
[Art style] style, [perspective]. [Mood/lighting details].
Tileable horizontally for side-scrolling.
```

**Item/Collectible:**
```
A [description] item for a 2D platformer game.
[Art style] style, transparent background, centered.
Clear icon readable at 32x32 pixels.
```

### What AI Art Does Well vs. Struggles With

**Good at:** Concept exploration, color palettes, backgrounds, UI elements, icons, single character poses

**Struggles with:**
- Consistent multi-frame animation (mitigate: always use reference image + detailed prompts preserving specific visual details)
- Transparent backgrounds on ANY endpoint — even `create-image` with `background: transparent` often produces faint halos (mitigate: always run rembg regardless)
- Matching character proportions exactly across frames (mitigate: regenerate bad frames using a good frame as reference)
- Even skin/face coloring — produces washed-out near-white pixels on faces (mitigate: post-process to blend outlier skin pixels toward median skin color)

### When Changing Sprite Dimensions

If the new sprite dimensions differ from existing placeholders (e.g., 32x64 → 40x40), you must also update:

1. **CollisionShape2D** in the character's `.tscn` scene (body collision)
2. **Attack hitbox** CollisionShape2D and any debug ColorRect
3. **Attack hitbox offset** in the script (e.g., `hitbox.position.x = facing_direction * N`)
4. **All other placeholder sprites** for the same character — resize them to match so animations don't glitch between frames

Plan for 1-2 regeneration attempts per frame and manual review of every frame before deploying.

## Reference

For detailed patterns and conventions, see: `~/Workspace/Godot-Game-Making/references/godot-claude-code-guide.md`

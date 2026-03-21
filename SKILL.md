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
3. **Process** — resize, trim, ensure consistency across frames
4. **Deploy** — copy final PNGs to `art/characters/<name>/`, replacing placeholders

### Prompt Templates for 2D Platformer Art

**Character (idle):**
```
A [description] character for a 2D platformer game. [Physical details].
Side view, [art style] style, transparent background.
Game character, clean silhouette, readable at small scale.
```

**Character (animation frame):**
```
A [description] character in a [action] pose, matching this reference image's style and proportions.
Side view, [art style] style, transparent background.
Frame [N] of a [action] animation sequence.
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
**Struggles with:** Consistent multi-frame animation, exact pixel grid alignment, matching existing styles precisely

Plan for manual touch-up on animation frame consistency.

## Reference

For detailed patterns and conventions, see: `~/Workspace/Godot-Game-Making/references/godot-claude-code-guide.md`

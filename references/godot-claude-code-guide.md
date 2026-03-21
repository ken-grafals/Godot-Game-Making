# Godot + Claude Code Workflow Guide

Patterns and conventions learned from building Godot 4.x games with Claude Code.

## Project Structure

```
project-root/
├── project.godot          # Godot project file
├── CLAUDE.md              # Claude Code instructions (project-specific)
├── scenes/                # .tscn scene files
├── scripts/               # .gd script files
├── art/
│   ├── characters/        # Character spritesheets and frames
│   │   ├── player/        # Player PNGs + .tres SpriteFrames
│   │   └── enemy/         # Enemy PNGs + .tres SpriteFrames
│   ├── generated_raw/     # Raw AI-generated images (gitignored)
│   └── generated_selected/# Curated picks ready for processing
├── assets/                # Sounds, fonts, UI elements
├── docs/                  # Design documents
├── test/
│   ├── unit/              # GdUnit4 unit tests
│   └── integration/       # Scene and signal tests
└── addons/                # Godot plugins
```

## AnimatedSprite2D + SpriteFrames Pattern

This is the recommended sprite system for 2D games with Claude Code.

### How It Works

1. **PNGs** live in `art/characters/<name>/` — one file per frame
2. **SpriteFrames resource** (`.tres`) references those PNGs and defines animations
3. **AnimatedSprite2D** node in the scene uses the SpriteFrames resource
4. **Scripts** call `animated_sprite.play("animation_name")` to switch animations

### Placeholder-to-Production Pipeline

Start with colored rectangles as placeholders:
- Same dimensions as final art (e.g., 64x64 or 128x128)
- Different colors per character/state for visual distinction
- All animation logic wired up from day one

To add real art:
1. Generate images using `generate_art.py` → `art/generated_raw/`
2. Curate best results → `art/generated_selected/`
3. Process (resize, trim, consistency pass) → `art/characters/<name>/`
4. SpriteFrames `.tres` already references these paths — no code changes needed

### SpriteFrames .tres Format

```
[gd_resource type="SpriteFrames" format=3]

[ext_resource type="Texture2D" path="res://art/characters/player/idle.png" id="1"]
[ext_resource type="Texture2D" path="res://art/characters/player/run_01.png" id="2"]

[resource]
animations = [{
"frames": [{
"duration": 1.0,
"texture": ExtResource("1")
}],
"loop": true,
"name": &"idle",
"speed": 5.0
}, ...]
```

## Collision Layer Conventions

| Bit | Layer | Used By |
|-----|-------|---------|
| 1 | World | Ground, platforms, walls |
| 2 | Player | Player CharacterBody2D |
| 4 | Enemy | Enemy CharacterBody2D |
| 8 | PlayerAttack | Player attack hitbox (Area2D) |
| 16 | EnemyAttack | Enemy attack hitbox (Area2D) |
| 32 | Collectible | Pickups, items |

Set collision **layers** (what I am) and **masks** (what I detect) separately.

## Input Map Conventions

Define in Project Settings → Input Map. Common actions:

| Action | Keys | Notes |
|--------|------|-------|
| `move_left` | Left Arrow, A | Horizontal movement |
| `move_right` | Right Arrow, D | Horizontal movement |
| `jump` | Spacebar | Gated by `is_on_floor()` |
| `attack` | J | Activates hitbox briefly |
| `interact` | E | NPC/object interaction |
| `pause` | Escape | Toggle pause menu |

## Testing with GdUnit4

### Setup

1. Install GdUnit4 via Godot Asset Library or git submodule into `addons/`
2. Tests go in `test/unit/` and `test/integration/`
3. Test files: `test_<name>.gd`, classes extend `GdUnitTestSuite`

### Running Tests

```bash
# Via Godot CLI (headless)
/Applications/Godot.app/Contents/MacOS/Godot --path . -s addons/gdUnit4/bin/GdUnitCmdTool.gd --headless

# Specific test
/Applications/Godot.app/Contents/MacOS/Godot --path . -s addons/gdUnit4/bin/GdUnitCmdTool.gd -a test/unit/test_player.gd --headless
```

### Headless Limitations

- No rendering — visual tests won't work
- Physics simulation requires `await` with process frames
- Use `auto_free()` to prevent orphan nodes
- Timer-based logic needs `simulate()` calls

### Test Patterns

```gdscript
class_name TestPlayer extends GdUnitTestSuite

var player: CharacterBody2D

func before_test():
    player = auto_free(preload("res://scenes/player.tscn").instantiate())
    add_child(player)

func after_test():
    pass  # auto_free handles cleanup

func test_starts_with_zero_velocity():
    assert_vector(player.velocity).is_equal(Vector2.ZERO)

func test_gravity_applies():
    await simulate(player, 10, 1.0 / 60.0)
    assert_float(player.velocity.y).is_greater(0.0)
```

## Script Organization

- One script per scene/node type
- Keep scripts focused — player movement in `player.gd`, not split across helpers
- Signals for cross-system communication (player → HUD, enemy → score)
- Export variables for designer-tunable values

```gdscript
@export var speed: float = 300.0
@export var jump_velocity: float = -500.0
```

## AI Art Generation Pipeline

### Staging Directories

```
art/
├── generated_raw/          # Direct output from AI — many variations
│   └── enemies/
│       └── scroll_gremlin/ # Per-character subdirectories
├── generated_selected/     # Human-curated picks
│   └── enemies/
│       └── scroll_gremlin/
└── characters/             # Production-ready, referenced by .tres
    └── enemy/
```

### Prompt Tips for 2D Platformer Art

- Specify **side view** for characters
- Request **transparent background** for sprites
- Include **"clean silhouette, readable at small scale"** for game-ready art
- Mention **pixel-art style** or **hand-drawn style** for consistency
- Describe **pose/action** explicitly (idle, running, jumping, hurt)
- For animation frames, reference previous frames for consistency

### What AI Art Does Well

- Concept exploration — rapid iteration on character designs
- Color palette generation
- Background/environment art
- UI elements and icons

### What AI Art Struggles With

- Consistent multi-frame animation sequences
- Exact pixel-art grid alignment
- Matching an existing art style precisely
- Small details at game-resolution sizes

Plan for manual touch-up on animation consistency.

## Godot CLI Reference (macOS)

```bash
# Check version
/Applications/Godot.app/Contents/MacOS/Godot --version

# Open editor
/Applications/Godot.app/Contents/MacOS/Godot --path /path/to/project

# Run game
/Applications/Godot.app/Contents/MacOS/Godot --path /path/to/project --quit

# Headless mode (CI/testing)
/Applications/Godot.app/Contents/MacOS/Godot --path /path/to/project --headless

# Export (after configuring export presets)
/Applications/Godot.app/Contents/MacOS/Godot --path /path/to/project --export-release "preset_name" output_path
```

---
name: godot-game-making
description: Triggers when user is making a Godot game, needs game art, wants to generate images for a Godot project, or asks about Godot game development with Claude Code
user-invocable: true
---

# Godot Game Making with Claude Code

You are assisting with Godot 4.x game development. This skill covers game development workflows, project structure, sprite systems, and testing patterns.

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

### OpenAI Image Generation (preferred)

When the user needs to generate or process game art, **read and follow the sub-skill document:**

`~/Workspace/Godot-Game-Making/sub-skills/godot-openai-image-gen/GODOT_OPENAI_IMAGE_GEN_SKILL.md`

It covers: prompt templates, background removal (`rembg`), post-processing pipeline, animation frame generation, sprite direction/dimension validation, and the full raw → production art workflow.

### fal.ai Sprite Animations (work in progress)

For multi-frame animations needing character consistency across frames (walk cycles, run cycles), there is an experimental fal.ai pipeline:

`~/Workspace/Godot-Game-Making/sub-skills/fal-sprites/FAL_SPRITES_SKILL.md`

**Status:** Work in progress. ControlNet Union pose mode on FLUX has reliability issues with OpenPose skeletons — pose following is inconsistent. Use OpenAI image generation for production art until this is resolved.

## Reference

For detailed patterns and conventions, see: `~/Workspace/Godot-Game-Making/references/godot-claude-code-guide.md`

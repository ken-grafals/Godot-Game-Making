# Scaffolding a Godot Game with Claude Code

Bootstrapping checklist for a new Godot 4.x project.

---

## project.godot

Minimal working config:

```ini
config_version=5

[application]

config/name="My Game"
config/description="Short description."
run/main_scene="res://scenes/main.tscn"
config/features=PackedStringArray("4.6", "GL Compatibility")

[rendering]

renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"
```

Use `GL Compatibility` for 2D games (wider device support). Use `Forward+` or `Mobile` only if you need advanced 3D rendering.

---

## Input Map

Add an `[input]` section to project.godot. Each action is an InputEventKey object:

```ini
[input]

move_left={
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":4194319,"physical_keycode":0,"key_label":0,"unicode":0,"location":0,"echo":false,"script":null)
]
}
```

Common keycodes:

| Key | Keycode |
|-----|---------|
| Left Arrow | 4194319 |
| Right Arrow | 4194321 |
| Up Arrow | 4194320 |
| Down Arrow | 4194322 |
| Space | 32 |
| A | 65 |
| D | 68 |
| W | 87 |
| S | 83 |
| J | 74 |
| K | 75 |
| E | 69 |
| Escape | 4194305 |

To bind multiple keys to one action, add multiple InputEventKey objects in the `events` array separated by `, `.

---

## Directory Structure

```
project-root/
├── project.godot
├── CLAUDE.md
├── .gitignore
├── scenes/
├── scripts/
├── art/
│   ├── characters/
│   │   ├── player/       # PNGs + player_frames.tres
│   │   └── enemy/        # PNGs + enemy_frames.tres
│   └── generated_raw/    # Raw AI output (gitignored)
├── assets/               # Sounds, fonts, UI
├── docs/                 # Design documents
├── test/
│   ├── unit/
│   └── integration/
└── addons/               # Plugins (GdUnit4, etc.)
```

---

## .gitignore

```
.godot/
*.import
art/generated_raw/
.DS_Store
*~
*.swp
```

---

## CLAUDE.md

Include these sections:

- **Project Overview** — what the game is (1-2 sentences)
- **Godot CLI** — executable path and common commands
- **Project Structure** — directory tree
- **Input Map** — table of actions and keys
- **Collision Layers** — table of bit assignments
- **Player/Enemy Mechanics** — speeds, health, key behaviors
- **Testing** — framework, test locations, run commands

---

## GdUnit4

Install from Asset Library or clone into `addons/gdUnit4/`. Enable in project.godot:

```ini
[editor_plugins]

enabled=PackedStringArray("res://addons/gdUnit4/plugin.cfg")
```

First test (`test/unit/test_placeholder.gd`):

```gdscript
class_name TestPlaceholder
extends GdUnitTestSuite

func test_sanity():
    assert_bool(true).is_true()
```

Run headlessly:

```bash
/Applications/Godot.app/Contents/MacOS/Godot --path . \
  -s addons/gdUnit4/bin/GdUnitCmdTool.gd --headless
```

Run a specific test:

```bash
/Applications/Godot.app/Contents/MacOS/Godot --path . \
  -s addons/gdUnit4/bin/GdUnitCmdTool.gd \
  -a test/unit/test_placeholder.gd --headless
```

---

## Placeholder Art

Start with colored-rectangle PNGs at your target sprite dimensions. Wire up the SpriteFrames `.tres` and AnimatedSprite2D from day one:

1. Create PNGs (e.g., 40x40 player, 28x48 enemy) — solid colors, one per frame
2. Create a `.tres` SpriteFrames resource referencing those PNGs with animation names (idle, run, jump, etc.)
3. AnimatedSprite2D in the scene uses the `.tres`
4. Scripts call `animated_sprite.play("idle")` etc.

To swap in real art later, just replace the PNGs at the same paths. No code or scene changes needed.

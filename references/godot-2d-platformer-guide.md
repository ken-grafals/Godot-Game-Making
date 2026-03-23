# 2D Platformer Patterns for Godot 4.x

Core patterns extracted from working implementations.

---

## Character Controller

Use `CharacterBody2D`. Gravity from project settings, applied every frame:

```gdscript
var gravity: float = ProjectSettings.get_setting("physics/2d/default_gravity")

func _physics_process(delta: float) -> void:
    if not is_on_floor():
        velocity.y += gravity * delta

    # State priority via early returns
    if is_dead:
        move_and_slide()
        return
    if is_staggered:
        move_and_slide()
        return

    # Normal input
    var direction := Input.get_axis("move_left", "move_right")
    if direction:
        velocity.x = direction * SPEED
        facing_direction = direction
    else:
        velocity.x = move_toward(velocity.x, 0, SPEED)

    if Input.is_action_just_pressed("jump") and is_on_floor():
        velocity.y = JUMP_VELOCITY

    move_and_slide()
    _update_animation()
```

Key points:
- `move_toward()` for instant deceleration (no ice-skating)
- Jump gated by `is_on_floor()`
- State booleans (`is_dead`, `is_staggered`, `is_invincible`, `is_attacking`) with early returns for priority
- Gravity always applies regardless of state

---

## Animation

Priority order in `_update_animation()`: attack > jump/fall > run > idle.

```gdscript
func _update_animation() -> void:
    animated_sprite.flip_h = facing_direction < 0.0
    if is_attacking:
        animated_sprite.play("attack")
    elif not is_on_floor() and velocity.y < 0:
        animated_sprite.play("jump")
    elif not is_on_floor():
        animated_sprite.play("fall")
    elif velocity.x != 0:
        animated_sprite.play("run")
    else:
        animated_sprite.play("idle")
```

Note: enemy sprites that face left in art use `flip_h = direction > 0.0` (opposite of player).

---

## Attack / Hitbox

Area2D child of player with a CollisionShape2D that starts disabled.

```gdscript
func _start_attack() -> void:
    is_attacking = true
    _attack_hits.clear()
    attack_hitbox.position.x = facing_direction * 20.0
    hitbox_shape.disabled = false
    get_tree().create_timer(ATTACK_DURATION).timeout.connect(_end_attack)

func _check_attack_hits() -> void:
    for body in attack_hitbox.get_overlapping_bodies():
        if body.has_method("take_damage") and not _attack_hits.has(body):
            _attack_hits[body] = true
            body.take_damage(self)

func _end_attack() -> void:
    is_attacking = false
    hitbox_shape.disabled = true
    _attack_hits.clear()
```

- `_attack_hits` Dictionary prevents multi-hit per swing
- `has_method("take_damage")` duck typing — no class coupling
- Hitbox layer = PlayerAttack, mask = Enemy

---

## Enemy Patrol

RayCast2D for ledge and wall detection:

```gdscript
func _physics_process(delta: float) -> void:
    if not is_on_floor():
        velocity.y += gravity * delta

    if is_staggered:
        move_and_slide()
        return

    # Ledge detection: raycasts point downward beyond sprite edge
    if is_on_floor():
        if direction < 0.0 and not ledge_left.is_colliding():
            direction = 1.0
        elif direction > 0.0 and not ledge_right.is_colliding():
            direction = -1.0

    # Wall detection: raycasts point horizontally
    if direction < 0.0 and wall_left.is_colliding():
        direction = 1.0
    elif direction > 0.0 and wall_right.is_colliding():
        direction = -1.0

    velocity.x = direction * SPEED
    move_and_slide()
```

RayCast2D setup:
- Ledge detectors: `target_position = Vector2(±18, 30)`, mask = World
- Wall detectors: `target_position = Vector2(±18, 0)`, mask = World

Contact damage via Area2D (`PlayerDetector`): mask = Player, `body_entered` signal calls `body.take_damage(self)`. Gate by `is_invincible` to prevent damage during stagger.

---

## Damage / Stagger / Invincibility

Shared pattern for both player and enemy:

```gdscript
func take_damage(source: Node2D) -> void:
    if is_invincible:
        return
    health -= 1
    if health <= 0:
        _die()
        return
    _stagger(source)
    _start_invincibility()

func _stagger(source: Node2D) -> void:
    is_staggered = true
    var knockback_dir := sign(global_position.x - source.global_position.x)
    if knockback_dir == 0.0:
        knockback_dir = 1.0
    velocity.x = knockback_dir * STAGGER_VELOCITY_X
    velocity.y = STAGGER_VELOCITY_Y
    get_tree().create_timer(STAGGER_DURATION).timeout.connect(
        func(): is_staggered = false)

func _start_invincibility() -> void:
    is_invincible = true
    var tween := create_tween()
    var flashes := int(INVINCIBILITY_DURATION / 0.1)
    for i in flashes:
        tween.tween_property(animated_sprite, "modulate:a",
            0.2 if i % 2 == 0 else 1.0, 0.05)
    tween.tween_callback(func():
        is_invincible = false
        animated_sprite.modulate.a = 1.0)
```

---

## Collision Layers

| Bit | Layer | Used By | Masks |
|-----|-------|---------|-------|
| 1 | World | Ground, platforms | — |
| 2 | Player | Player body | World |
| 4 | Enemy | Enemy body | World |
| 8 | PlayerAttack | Attack hitbox | Enemy |
| 16 | EnemyAttack | Enemy hitbox | Player |

- **Layer** = what I am. **Mask** = what I detect.
- RayCasts: mask World only
- PlayerDetector Area2D: layer 0, mask Player (invisible trigger)

---

## Tuning Constants

| Constant | Player | Enemy |
|----------|--------|-------|
| SPEED | 300.0 | 80.0 |
| JUMP_VELOCITY | -500.0 | — |
| ATTACK_DURATION | 0.15s | — |
| STAGGER_VELOCITY_X | 200.0 | 150.0 |
| STAGGER_VELOCITY_Y | -150.0 | -100.0 |
| STAGGER_DURATION | 0.3s | 0.3s |
| INVINCIBILITY_DURATION | 1.5s | 0.8s |
| MAX_LIVES / MAX_HEALTH | 3 | 2 |

Define as constants at the top of each script. Player should be faster than enemies.

---

## Signal Wiring

Player emits signals, main scene wires them to the HUD:

```gdscript
# player.gd
signal lives_changed(new_lives: int)
signal player_died

# main.gd
func _ready() -> void:
    $Player.lives_changed.connect($HUD.update_lives)
    $HUD.update_lives($Player.lives)

# hud.gd
func update_lives(count: int) -> void:
    $Life1.visible = count >= 1
    $Life2.visible = count >= 2
    $Life3.visible = count >= 3
```

HUD uses a CanvasLayer so it renders above the game world. Simple visibility toggles on life icons.

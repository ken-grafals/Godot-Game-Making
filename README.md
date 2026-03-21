# Godot Game Making

A Claude Code skill for Godot game development with AI art generation tooling.

## What's Included

- **SKILL.md** — Claude Code skill definition (`/godot-game-making`)
- **scripts/generate_art.py** — OpenAI image generation CLI script
- **references/godot-claude-code-guide.md** — Godot + Claude Code workflow guide

## Setup

### 1. Install Python dependency

```bash
pip install openai
```

### 2. Set your OpenAI API key

Add to `~/.zshrc`:
```bash
export GODOT_OPENAI_API_KEY="sk-proj-..."
```

### 3. Link the skill

```bash
mkdir -p ~/.claude/skills
ln -s ~/Workspace/Godot-Game-Making ~/.claude/skills/godot-game-making
```

### 4. (Optional) Set up MCP server for conversational art exploration

```bash
cd ~/Workspace
git clone https://github.com/SureScaleAI/openai-gpt-image-mcp.git
cd openai-gpt-image-mcp
npm install && npm run build

claude mcp add --transport stdio \
  --env GODOT_OPENAI_API_KEY="$GODOT_OPENAI_API_KEY" \
  openai-gpt-image \
  -- node ~/Workspace/openai-gpt-image-mcp/dist/index.js
```

## Usage

### Script (repeatable production jobs)

```bash
python ~/Workspace/Godot-Game-Making/scripts/generate_art.py \
  --prompt "A small goblin enemy for a 2D platformer, side view, transparent background" \
  --output art/generated_raw/enemy_001.png \
  --size 1024x1024 \
  --background transparent
```

### MCP (conversational exploration)

Use `/godot-game-making` in Claude Code, then ask Claude to generate art using the MCP tools.

### Skill

Type `/godot-game-making` in Claude Code for Godot development guidance and art pipeline instructions.

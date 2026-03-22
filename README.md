# Godot Game Making

A Claude Code skill for Godot game development workflows and AI art generation.

## What's Included

- **SKILL.md** — Claude Code skill definition (`/godot-game-making`)
- **references/godot-claude-code-guide.md** — Godot + Claude Code workflow guide
- **sub-skills/godot-openai-image-gen/** — OpenAI image generation sub-skill (prompt templates, post-processing, sprite pipeline)

## Setup

### 1. Link the skill

```bash
mkdir -p ~/.claude/skills
ln -s ~/Workspace/Godot-Game-Making ~/.claude/skills/godot-game-making
```

### 2. (For AI art generation) Install Python dependencies

```bash
pip install openai Pillow "rembg[cpu]"
```

### 3. (For AI art generation) Set your OpenAI API key

Add to `~/.zshrc`:
```bash
export GODOT_OPENAI_API_KEY="sk-proj-..."
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

Type `/godot-game-making` in Claude Code for Godot development guidance and art generation workflows. The skill automatically routes to the image generation sub-skill when art tasks are detected.

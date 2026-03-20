#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE_CLAUDE="$SCRIPT_DIR/.claude"
TARGET_GLOBAL="$HOME/.claude"
TARGET_PARENT="$(dirname "$SCRIPT_DIR")/.claude"

echo "Installing claude-code-base configs..."

# Copy claude-dashboard.local.json and setting.json to ~/.claude/
mkdir -p "$TARGET_GLOBAL"
cp "$SOURCE_CLAUDE/claude-dashboard.local.json" "$TARGET_GLOBAL/"
cp "$SOURCE_CLAUDE/setting.json" "$TARGET_GLOBAL/"
echo "  Copied claude-dashboard.local.json -> $TARGET_GLOBAL/"
echo "  Copied setting.json -> $TARGET_GLOBAL/"

# Copy skills/ to ~/.claude/skills/
mkdir -p "$TARGET_GLOBAL/skills"
cp "$SOURCE_CLAUDE/skills/"*.md "$TARGET_GLOBAL/skills/"
echo "  Copied skills/ -> $TARGET_GLOBAL/skills/"

# Copy CLAUDE.md to parent ../.claude/
mkdir -p "$TARGET_PARENT"
cp "$SOURCE_CLAUDE/CLAUDE.md" "$TARGET_PARENT/"
echo "  Copied CLAUDE.md -> $TARGET_PARENT/"

echo "Done."

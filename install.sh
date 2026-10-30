#!/usr/bin/env bash
# HakoAgent installer
# Usage:
#   ./install.sh              # install to project root (./hakoagent + ./AGENTS.md + .opencode/)
#   ./install.sh --global|-g  # install to ~/.local/bin/hakoagent + ~/.config/opencode/skills/ + ~/.hakoagent/
#   ./install.sh --uninstall  # uninstall from project root
#   ./install.sh --global --uninstall  # uninstall from global ~/.local/bin/
#   ./install.sh --help|-h    # show help

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GLOBAL=0
UNINSTALL=0
REMOVE_DATA=0

for arg in "$@"; do
  case "$arg" in
    --global|-g) GLOBAL=1 ;;
    --uninstall) UNINSTALL=1 ;;
    --remove-data) REMOVE_DATA=1 ;;
    --help|-h)
      echo "Usage: $0 [--global|-g] [--uninstall] [--remove-data]"
      echo "  (default) install to project root: ./hakoagent + ./AGENTS.md + .opencode/"
      echo "  --global  install to ~/.local/bin/hakoagent + ~/.config/opencode/skills/ + ~/.hakoagent/"
      echo "  --uninstall  remove hakoagent binaries and files (project or global)"
      echo "  --remove-data  also delete .hakoagent/ data directory (events, tasks, skills, etc.)"
      echo "  --help|-h    show this help"
      exit 0
      ;;
    *) echo "Unknown argument: $arg" >&2; exit 1 ;;
  esac
done

# PONYTAIL: simple shell script, no argparse, no Windows support.
# Ceiling: POSIX sh/bash only, no Python installer, no package manager integration.
# Upgrade path: rewrite in Python with argparse + pip-style install if needed.

# ---------------------------------------------------------------------------
# Uninstall
# ---------------------------------------------------------------------------

if [ "$UNINSTALL" -eq 1 ]; then
  if [ "$GLOBAL" -eq 1 ]; then
    echo "=== Uninstalling HakoAgent globally ==="
    INSTALL_DIR="$HOME/.local/bin"
    AGENT_DIR="$HOME/.hakoagent"
    SKILL_DIRS=("$HOME/.config/opencode/skills" "$HOME/.claude/skills")
    COMMAND_DIRS=("$HOME/.config/opencode/commands" "$HOME/.claude/commands")

    # Remove binaries
    for bin in hakoagent hakoagent-cli hakoagent-mcp; do
      if [ -f "$INSTALL_DIR/$bin" ]; then
        rm -f "$INSTALL_DIR/$bin"
        echo "Removed: $INSTALL_DIR/$bin"
      else
        echo "Not found: $INSTALL_DIR/$bin"
      fi
    done

    # Remove AGENTS.md
    if [ -f "$AGENT_DIR/AGENTS.md" ]; then
      rm -f "$AGENT_DIR/AGENTS.md"
      echo "Removed: $AGENT_DIR/AGENTS.md"
    fi

    # Remove skills from OpenCode skills directories
    for skill_dir in "$SCRIPT_DIR"/.opencode/skills/*/; do
      [ -d "$skill_dir" ] || continue
      skill_name=$(basename "$skill_dir")
      for d in "${SKILL_DIRS[@]}"; do
        if [ -d "$d/$skill_name" ]; then
          rm -rf "$d/$skill_name"
          echo "Removed: $d/$skill_name"
        fi
      done
    done

    # Remove the hakoagent slash command from global command directories
    for d in "${COMMAND_DIRS[@]}"; do
      if [ -f "$d/hakoagent.md" ]; then
        rm -f "$d/hakoagent.md"
        echo "Removed: $d/hakoagent.md"
      fi
    done

    # Remove the hakodb FFI library installed next to the binaries
    for f in "$INSTALL_DIR"/lib/libhakodb-*.so "$INSTALL_DIR/lib/hakodb.h" "$INSTALL_DIR/lib/SHA256SUMS.txt"; do
      if [ -f "$f" ]; then
        rm -f "$f"
        echo "Removed: $f"
      fi
    done
    rmdir "$INSTALL_DIR/lib" 2>/dev/null || true

    # Remove hakoagent from MCP config files
    CLAUDE_JSON="$HOME/.claude.json"
    OPencode_CONFIG="$HOME/.config/opencode/opencode.jsonc"

    if [ -f "$CLAUDE_JSON" ]; then
      if python3 -c "
import json, sys
with open('$CLAUDE_JSON') as f:
    data = json.load(f)
servers = data.get('mcpServers', {})
if 'hakoagent' in servers:
    del servers['hakoagent']
    with open('$CLAUDE_JSON', 'w') as f:
        json.dump(data, f, indent=2)
        f.write('\n')
    sys.exit(0)
sys.exit(1)
" 2>/dev/null; then
        echo "Removed hakoagent from $CLAUDE_JSON"
      else
        echo "No hakoagent entry in $CLAUDE_JSON (or could not parse)"
      fi
    fi

    if [ -f "$OPencode_CONFIG" ]; then
      if python3 -c "
import json, sys
with open('$OPencode_CONFIG') as f:
    data = json.load(f)
changed = False
mcp = data.get('mcp', {})
if isinstance(mcp, dict):
    if 'hakoagent' in mcp:  # legacy V1 shape
        del mcp['hakoagent']
        changed = True
    servers = mcp.get('servers')
    if isinstance(servers, dict) and 'hakoagent' in servers:  # V2 shape
        del servers['hakoagent']
        changed = True
        if not servers:
            mcp.pop('servers', None)
    if not mcp:
        data.pop('mcp', None)
if changed:
    with open('$OPencode_CONFIG', 'w') as f:
        json.dump(data, f, indent=2)
        f.write('\n')
    sys.exit(0)
sys.exit(1)
" 2>/dev/null; then
        echo "Removed hakoagent from $OPencode_CONFIG"
      else
        echo "No hakoagent entry in $OPencode_CONFIG (or could not parse)"
      fi
    fi

    # Optionally remove .hakoagent/ data directory
    if [ "$REMOVE_DATA" -eq 1 ] && [ -d "$AGENT_DIR" ]; then
      rm -rf "$AGENT_DIR"
      echo "Removed: $AGENT_DIR (--remove-data)"
    elif [ -d "$AGENT_DIR" ]; then
      echo "Kept: $AGENT_DIR (use --remove-data to delete)"
    fi

    echo "Global uninstall complete."
  else
    echo "=== Uninstalling HakoAgent from project ==="
    INSTALL_DIR="$(pwd)"

    # Remove binaries
    for bin in hakoagent hakoagent-cli hakoagent-mcp; do
      if [ -f "$INSTALL_DIR/$bin" ]; then
        rm -f "$INSTALL_DIR/$bin"
        echo "Removed: $INSTALL_DIR/$bin"
      else
        echo "Not found: $INSTALL_DIR/$bin"
      fi
    done

    # Remove AGENTS.md
    if [ -f "$INSTALL_DIR/AGENTS.md" ]; then
      rm -f "$INSTALL_DIR/AGENTS.md"
      echo "Removed: $INSTALL_DIR/AGENTS.md"
    fi

    # Remove skills from project .opencode/skills/
    if [ -d "$INSTALL_DIR/.opencode/skills" ]; then
      for skill_dir in "$SCRIPT_DIR"/.opencode/skills/*/; do
        [ -d "$skill_dir" ] || continue
        skill_name=$(basename "$skill_dir")
        if [ -d "$INSTALL_DIR/.opencode/skills/$skill_name" ]; then
          rm -rf "$INSTALL_DIR/.opencode/skills/$skill_name"
          echo "Removed: $INSTALL_DIR/.opencode/skills/$skill_name"
        fi
      done
    fi

    # Remove only the hakoagent command (do not touch user's speckit commands)
    if [ -f "$INSTALL_DIR/.opencode/commands/hakoagent.md" ]; then
      rm -f "$INSTALL_DIR/.opencode/commands/hakoagent.md"
      echo "Removed: $INSTALL_DIR/.opencode/commands/hakoagent.md"
    fi

    # Remove the hakodb FFI library installed next to the binaries
    for f in "$INSTALL_DIR"/lib/libhakodb-*.so "$INSTALL_DIR/lib/hakodb.h" "$INSTALL_DIR/lib/SHA256SUMS.txt"; do
      if [ -f "$f" ]; then
        rm -f "$f"
        echo "Removed: $f"
      fi
    done
    rmdir "$INSTALL_DIR/lib" 2>/dev/null || true

    # Optionally remove .hakoagent/ data directory
    if [ "$REMOVE_DATA" -eq 1 ] && [ -d "$INSTALL_DIR/.hakoagent" ]; then
      rm -rf "$INSTALL_DIR/.hakoagent"
      echo "Removed: $INSTALL_DIR/.hakoagent (--remove-data)"
    elif [ -d "$INSTALL_DIR/.hakoagent" ]; then
      echo "Kept: $INSTALL_DIR/.hakoagent (use --remove-data to delete)"
    fi

    echo "Project uninstall complete."
  fi
  exit 0
fi

# ---------------------------------------------------------------------------
# Install
# ---------------------------------------------------------------------------
if [ "$GLOBAL" -eq 1 ]; then
  INSTALL_DIR="$HOME/.local/bin"
  AGENT_DIR="$HOME/.hakoagent"
  SKILL_DIRS=("$HOME/.config/opencode/skills" "$HOME/.claude/skills")
  COMMAND_DIRS=("$HOME/.config/opencode/commands" "$HOME/.claude/commands")
  mkdir -p "$INSTALL_DIR" "$AGENT_DIR"
  for d in "${SKILL_DIRS[@]}"; do mkdir -p "$d"; done
  for d in "${COMMAND_DIRS[@]}"; do mkdir -p "$d"; done
  cp "$SCRIPT_DIR/hakoagent" "$INSTALL_DIR/hakoagent"
  cp "$SCRIPT_DIR/hakoagent-mcp" "$INSTALL_DIR/hakoagent-mcp"
  cp "$SCRIPT_DIR/hakoagent" "$INSTALL_DIR/hakoagent-cli"
  chmod +x "$INSTALL_DIR/hakoagent"
  chmod +x "$INSTALL_DIR/hakoagent-mcp"
  chmod +x "$INSTALL_DIR/hakoagent-cli"
  # Install the hakodb FFI library next to the binaries. Without it the
  # engine silently falls back to JSON-only storage.
  if [ -d "$SCRIPT_DIR/lib" ]; then
    mkdir -p "$INSTALL_DIR/lib"
    cp "$SCRIPT_DIR/lib"/* "$INSTALL_DIR/lib/"
    echo "Installed hakodb library to $INSTALL_DIR/lib"
  else
    echo "ERROR: $SCRIPT_DIR/lib not found; hakoagent will run without hakodb" >&2
  fi
  cp "$SCRIPT_DIR/AGENTS.md" "$AGENT_DIR/AGENTS.md"
  # Install the /hakoagent command globally so it is available in every project
  if [ -f "$SCRIPT_DIR/.opencode/commands/hakoagent.md" ]; then
    for d in "${COMMAND_DIRS[@]}"; do
      cp "$SCRIPT_DIR/.opencode/commands/hakoagent.md" "$d/hakoagent.md"
      echo "Installed command to $d/hakoagent.md"
    done
  fi
  # Install skills to OpenCode skills directories
  for skill_dir in "$SCRIPT_DIR"/.opencode/skills/*/; do
    skill_name=$(basename "$skill_dir")
    for d in "${SKILL_DIRS[@]}"; do
      mkdir -p "$d/$skill_name"
      cp "$skill_dir/SKILL.md" "$d/$skill_name/SKILL.md"
    done
  done
  # NOTE: MCP server is OFF by default in global install.
  # It is not added to ~/.claude.json or ~/.config/opencode/opencode.jsonc.
  # To enable MCP for a specific project, cd into that project and run:
  #   hakoagent mcp enable
  # Then start the MCP server:
  #   hakoagent-mcp
  echo "Installed hakoagent to $INSTALL_DIR/hakoagent"
  echo "Installed hakoagent-mcp to $INSTALL_DIR/hakoagent-mcp"
  echo "Installed hakoagent-cli to $INSTALL_DIR/hakoagent-cli"
  echo "Installed AGENTS.md to $AGENT_DIR/AGENTS.md"
  echo "Installed skills to OpenCode skills directories"
  echo "Installed /hakoagent command to global command directories"
  echo "Installed hakodb library to $INSTALL_DIR/lib"
  echo "MCP server is OFF by default. Run 'hakoagent mcp enable' inside a project to activate."
  echo "Add to PATH: export PATH=\"\$HOME/.local/bin:\$PATH\""
else
  INSTALL_DIR="$(pwd)"
  mkdir -p "$INSTALL_DIR/.hakoagent"
  if [ "$SCRIPT_DIR" != "$INSTALL_DIR" ]; then
    cp "$SCRIPT_DIR/hakoagent" "$INSTALL_DIR/hakoagent"
    cp "$SCRIPT_DIR/hakoagent-mcp" "$INSTALL_DIR/hakoagent-mcp"
    cp "$SCRIPT_DIR/hakoagent" "$INSTALL_DIR/hakoagent-cli"
    cp "$SCRIPT_DIR/AGENTS.md" "$INSTALL_DIR/AGENTS.md"
    # Install the hakodb FFI library (required for the embedded engine)
    if [ -d "$SCRIPT_DIR/lib" ]; then
      mkdir -p "$INSTALL_DIR/lib"
      cp "$SCRIPT_DIR/lib"/* "$INSTALL_DIR/lib/"
    else
      echo "ERROR: $SCRIPT_DIR/lib not found; hakoagent will run without hakodb" >&2
    fi
    # Install skills to project .opencode/skills/
    if [ -d "$SCRIPT_DIR/.opencode/skills" ]; then
      mkdir -p "$INSTALL_DIR/.opencode/skills"
      for skill_dir in "$SCRIPT_DIR"/.opencode/skills/*/; do
        skill_name=$(basename "$skill_dir")
        mkdir -p "$INSTALL_DIR/.opencode/skills/$skill_name"
        cp "$skill_dir/SKILL.md" "$INSTALL_DIR/.opencode/skills/$skill_name/SKILL.md"
      done
    fi
    # Install only the hakoagent command (do not copy unrelated speckit commands)
    if [ -f "$SCRIPT_DIR/.opencode/commands/hakoagent.md" ]; then
      mkdir -p "$INSTALL_DIR/.opencode/commands"
      cp "$SCRIPT_DIR/.opencode/commands/hakoagent.md" "$INSTALL_DIR/.opencode/commands/hakoagent.md"
    fi
  fi
  chmod +x "$INSTALL_DIR/hakoagent"
  chmod +x "$INSTALL_DIR/hakoagent-mcp"
  chmod +x "$INSTALL_DIR/hakoagent-cli"
  echo "Installed hakoagent to $INSTALL_DIR/hakoagent"
  echo "Installed hakoagent-mcp to $INSTALL_DIR/hakoagent-mcp"
  echo "Installed hakoagent-cli to $INSTALL_DIR/hakoagent-cli"
  echo "Installed AGENTS.md to $INSTALL_DIR/AGENTS.md"
  echo "Installed OpenCode skills and commands to .opencode/"
  echo "Run: ./hakoagent init --db ./.hakoagent/hakoagent.db --collections all"
  echo "Run: ./hakoagent-mcp  # Start MCP server"
fi

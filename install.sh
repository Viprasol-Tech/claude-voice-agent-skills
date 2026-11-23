#!/usr/bin/env bash
# Installs every Voice Agents skill into ~/.claude/skills (Claude Code personal skills).
set -euo pipefail
DEST="${1:-$HOME/.claude/skills}"
SRC="$(cd "$(dirname "$0")" && pwd)/plugins/voice-agents/skills"
mkdir -p "$DEST"
for d in "$SRC"/*/; do
  n=$(basename "$d")
  rm -rf "${DEST:?}/$n"
  cp -r "$d" "$DEST/$n"
  echo "installed $n"
done
echo
echo "Done. Restart Claude Code, then try: \"Why does my Twilio voice agent sound robotic?\""

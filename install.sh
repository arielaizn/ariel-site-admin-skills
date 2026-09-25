#!/usr/bin/env bash
# install.sh: put the ariel-admin-* skills where the agent reads them.
#   ./install.sh                copy skills/* into ~/.claude/skills (existing ariel-admin* dirs are replaced)
#   ./install.sh --link         symlink instead of copy (git pull updates them in place)
#   ./install.sh --dest <dir>   another skills directory (Codex, OpenClaw, ...)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="$HOME/.claude/skills"
MODE="copy"
while [ $# -gt 0 ]; do
  case "$1" in
    --link) MODE="link" ;;
    --dest) DEST="$2"; shift ;;
    -h|--help) sed -n '2,5p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

mkdir -p "$DEST"
for skill in "$HERE"/skills/*/; do
  name="$(basename "$skill")"
  target="$DEST/$name"
  if [ -L "$target" ] || [ -d "$target" ]; then rm -rf "$target"; fi
  if [ "$MODE" = "link" ]; then
    ln -s "${skill%/}" "$target"
  else
    cp -R "${skill%/}" "$target"
  fi
  echo "installed $name → $target"
done
chmod +x "$DEST/ariel-admin/scripts/ariel_admin.py" 2>/dev/null || true

CONF="$HOME/.config/ariel-admin"
mkdir -p "$CONF"
if [ ! -f "$CONF/.env" ]; then
  cp "$HERE/.env.example" "$CONF/.env"
  chmod 600 "$CONF/.env"
  echo "created $CONF/.env (fill in ARIEL_ADMIN_API_SECRET and ARIEL_ADMIN_PASSWORD)"
else
  echo "kept $CONF/.env"
fi

OLD=$(ls -d "$DEST"/ariel-site-* 2>/dev/null || true)
if [ -n "$OLD" ]; then
  echo
  echo "note: the old Supabase-era skills are still installed and their triggers overlap:"
  echo "$OLD" | sed 's/^/  /'
  echo "  remove them with: rm -rf $DEST/ariel-site-*"
fi

echo
echo "next: python3 $DEST/ariel-admin/scripts/ariel_admin.py doctor"

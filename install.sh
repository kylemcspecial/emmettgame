#!/bin/bash
# Citadel of Friendship & Magic — one-command installer for Raspberry Pi.
#
# Cloned the repo? This is the only command you need:
#     bash install.sh
#
# It makes sure python3-venv exists, creates a dedicated virtual
# environment, installs pygame-ce + numpy into it, generates the game
# icon, and adds a desktop + menu launcher so a kid can just click the
# icon and play.
#
# Usage:  bash install.sh [--uninstall]
set -euo pipefail

GAME_NAME="Citadel of Friendship & Magic"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
DESKTOP_DIR="${XDG_DESKTOP_DIR:-$HOME/Desktop}"
ICON_PATH="$SCRIPT_DIR/citadel-icon.png"
DESKTOP_FILE="$HOME/.local/share/applications/citadel-of-friendship.desktop"
LAUNCHER="$SCRIPT_DIR/start-citadel"

say() { printf '\033[1;32m==>\033[0m %s\n' "$*"; }
die() { printf '\033[1;31mError:\033[0m %s\n' "$*" >&2; exit 1; }

uninstall() {
  say "Removing desktop launcher and virtual environment"
  rm -f "$DESKTOP_FILE" "$DESKTOP_DIR/citadel-of-friendship.desktop"
  rm -rf "$VENV_DIR"
  say "Uninstalled. Your save (savegame.json) stays in the game folder —"
  say "delete it too if you want a completely fresh start."
  exit 0
}

[[ "${1:-}" == "--uninstall" ]] && uninstall
[[ -f "$SCRIPT_DIR/run_game.py" ]] || die "run this from the game folder (run_game.py not found). cd into the emmettgame folder first."

say "Checking Python 3.9+"
command -v python3 >/dev/null || die "python3 not found — install it with: sudo apt install python3"
PYV=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' \
  || die "Python 3.9+ required (found $PYV)"

if [[ ! -d "$VENV_DIR" ]]; then
  # Debian/Raspberry Pi OS can ship venv without ensurepip until python3-venv is installed.
  if ! python3 -c "import venv; import ensurepip" >/dev/null 2>&1; then
    say "python3-venv missing — installing it (needs sudo)"
    sudo apt-get update -qq && sudo apt-get install -y python3-venv \
      || die "could not install python3-venv — run: sudo apt install -y python3-venv, then rerun this script"
  fi
  say "Creating virtual environment ($VENV_DIR)"
  if ! python3 -m venv "$VENV_DIR"; then
    die "venv creation failed — run: sudo apt install -y python3-venv, then rerun this script."
  fi
fi

say "Installing game libraries (pygame-ce, numpy) into the venv"
"$VENV_DIR/bin/pip" install --quiet --upgrade pip >/dev/null 2>&1 || true
"$VENV_DIR/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements.txt" \
  || die "pip install failed — check your network connection, then rerun"

if [[ ! -f "$ICON_PATH" ]]; then
  say "Generating game icon"
  "$VENV_DIR/bin/python" "$SCRIPT_DIR/make_icon.py" "$ICON_PATH" >/dev/null \
    || die "icon generation failed"
fi
[[ -f "$ICON_PATH" ]] || die "icon generation failed"

say "Creating launcher"
cat > "$LAUNCHER" <<EOF
#!/bin/bash
cd "$SCRIPT_DIR"
exec "$VENV_DIR/bin/python" run_game.py
EOF
chmod +x "$LAUNCHER"

say "Adding the game to your Desktop and menu"
mkdir -p "$HOME/.local/share/applications"
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=$GAME_NAME
Comment=A kind and magical building adventure
Exec=$LAUNCHER
Icon=$ICON_PATH
Terminal=false
Categories=Game;KidsGame;
EOF
chmod +x "$DESKTOP_FILE"

# copy to the desktop too, if it exists
if [[ -d "$DESKTOP_DIR" ]]; then
  cp "$DESKTOP_FILE" "$DESKTOP_DIR/citadel-of-friendship.desktop"
fi

# refresh the menu cache if the helper is available
command -v update-desktop-database >/dev/null \
  && update-desktop-database "$HOME/.local/share/applications" || true

say "Smoke test: importing the game"
"$VENV_DIR/bin/python" -c "import sys; sys.path.insert(0, '$SCRIPT_DIR'); import citadel.main" \
  || die "game import failed — please report this"

cat <<DONE

=============================================
  All done! Find the game icon on your
  Desktop: '$GAME_NAME'
  Double-click it and play!
=============================================
  Launch:    Desktop icon, or Menu > Games
  Terminal:  $LAUNCHER
  Saves:     $SCRIPT_DIR/savegame.json (automatic)
  Uninstall: bash install.sh --uninstall

(If the icon shows a blank document the first time, right-click it
and choose 'Allow Launching' once - Raspberry Pi OS just needs
permission the first time.)

DONE

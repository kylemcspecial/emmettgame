#!/bin/bash
# Citadel of Friendship & Magic - one-click installer for Raspberry Pi OS.
# Run from the cloned repo folder (double-click "install" in the file manager,
# choose "Execute in Terminal", or run:  bash install.sh)
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

GAMEDIR="$(cd "$(dirname "$0")" && pwd)"
GAME="$GAMEDIR/run_game.py"
DESKTOP_DIR="${HOME}/Desktop"
MENU_DIR="${HOME}/.local/share/applications"
ICON="$GAMEDIR/citadel-icon.png"

step() { echo -e "${GREEN}==> $1${NC}"; }

echo "==============================================="
echo "  Citadel of Friendship & Magic - Installer"
echo "==============================================="
echo ""

# 1. Python + pip
step "Checking Python..."
if ! command -v python3 >/dev/null; then
    echo "Installing Python 3..."
    sudo apt-get update -qq && sudo apt-get install -y -qq python3 python3-pip
fi
echo "  Python found: $(python3 --version)"

# 2. pygame + numpy (apt first - safest on Pi, pip as fallback)
step "Installing game libraries (pygame + numpy)..."
if python3 -c "import pygame, numpy" 2>/dev/null; then
    echo "  Already installed. Nice!"
else
    if sudo apt-get install -y -qq python3-pygame python3-numpy 2>/dev/null; then
        echo "  Installed from Raspberry Pi OS packages."
    else
        echo "  apt packages unavailable, using pip instead..."
        python3 -m pip install --user --break-system-packages pygame numpy 2>/dev/null \
            || python3 -m pip install --user pygame numpy
    fi
fi

if ! python3 -c "import pygame, numpy" 2>/dev/null; then
    echo ""
    echo "  ERROR: could not install pygame/numpy automatically."
    echo "  Try running:  sudo apt install python3-pygame python3-numpy"
    exit 1
fi

# 3. Game icon
step "Creating game icon..."
python3 "$GAMEDIR/make_icon.py" "$ICON" && echo "  Icon saved."

# 4. Launcher script
step "Creating launcher..."
cat > "$GAMEDIR/start-citadel" <<EOF
#!/bin/bash
cd "$GAMEDIR"
python3 run_game.py
EOF
chmod +x "$GAMEDIR/start-citadel"
echo "  Launcher created."

# 5. Desktop shortcut (single click to play!)
step "Adding icon to your Desktop..."
mkdir -p "$DESKTOP_DIR" "$MENU_DIR"
cat > "$DESKTOP_DIR/citadel.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Citadel of Friendship & Magic
Comment=A kind and magical building adventure
Exec=$GAMEDIR/start-citadel
Icon=$ICON
Terminal=false
Categories=Game;KidsGame;
EOF
chmod +x "$DESKTOP_DIR/citadel.desktop"

# 6. Also add to the application menu
cat > "$MENU_DIR/citadel.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Citadel of Friendship & Magic
Comment=A kind and magical building adventure
Exec=$GAMEDIR/start-citadel
Icon=$ICON
Terminal=false
Categories=Game;KidsGame;
EOF
echo "  Desktop icon added!"

echo ""
echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN}  All done! Find the game icon on your"
echo -e "${GREEN}  Desktop: 'Citadel of Friendship & Magic'"
echo -e "${GREEN}  Double-click it and play!"
echo -e "${GREEN}=============================================${NC}"
echo ""
echo -e "${YELLOW}(If the icon shows a blank document, right-click it"
echo -e "and choose 'Allow Launching' one time - Raspberry"
echo -e "Pi OS just needs permission the first time.)${NC}"
echo ""
read -r -p "Press Enter to close this window..."

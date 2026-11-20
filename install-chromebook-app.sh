#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
APPS_DIR="${HOME}/.local/share/applications"
ICONS_DIR="${HOME}/.local/share/icons/hicolor/scalable/apps"

mkdir -p "${APPS_DIR}" "${ICONS_DIR}"
cp "${APP_DIR}/public/favicon.svg" "${ICONS_DIR}/algo-studio.svg"

cat > "${APPS_DIR}/algo-studio.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Algo Studio
Comment=Offline Coding Interview Workbench (120-Day Plan, LC 150, Grind 75, NeetCode 150, SQL 50)
Exec=/usr/bin/env python3 "${APP_DIR}/launch_app.py"
Path=${APP_DIR}
Icon=algo-studio
Terminal=false
Categories=Development;Education;
StartupNotify=true
EOF

chmod +x "${APP_DIR}/start.sh" "${APP_DIR}/launch_app.py" "${APPS_DIR}/algo-studio.desktop"
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "${APPS_DIR}" || true
fi

echo "Installed Algo Studio launcher shortcut at ${APPS_DIR}/algo-studio.desktop"
echo "On Chromebook, open the Launcher -> Linux apps -> Algo Studio (right-click to Pin to shelf)."

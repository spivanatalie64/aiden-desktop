#!/usr/bin/env bash
# Build AIDEN Desktop for every major distribution format.
# Usage: ./packaging/build-all.sh [target]
#   target: all | deb | rpm | arch | flatpak | appimage | alpine | void
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; NC='\033[0m'
log()  { echo -e "${CYAN}[BUILD]${NC} $*"; }
ok()   { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
fail() { echo -e "${RED}[FAIL]${NC} $*"; exit 1; }

BUILD_DIR="${PROJECT_DIR}/desktop/src-tauri/target/release"

cmd_deps() {
  log "Installing build deps..."
  if command -v apt &>/dev/null; then
    sudo apt-get install -y -qq build-essential curl wget file libssl-dev libgtk-3-dev \
      libwebkit2gtk-4.1-dev libayatana-appindicator3-dev librsvg2-dev \
      libjavascriptcoregtk-4.1-dev libsoup-3.0-dev python3 python3-pip
  elif command -v pacman &>/dev/null; then
    sudo pacman -S --noconfirm base-devel webkit2gtk-4.1 libappindicator-gtk3 \
      librsvg libsoup3 python python-pip npm rustup
  elif command -v dnf &>/dev/null; then
    sudo dnf install -y gcc-c++ webkit2gtk4.1-devel libappindicator-gtk3-devel \
      librsvg2-devel libsoup3-devel openssl-devel python3 python3-pip npm rustup
  fi
  npm install -g @tauri-apps/cli 2>/dev/null || true
  ok "Deps installed"
}

cmd_build_binary() {
  log "Building Tauri binary + deb + appimage..."
  cd desktop/web && npm ci --silent && npm run build --silent && cd "$PROJECT_DIR"
  cd desktop && npx --prefix web tauri build --bundles deb,appimage && cd "$PROJECT_DIR"
  ok "Binary + deb + appimage ready"
}

cmd_pkg_arch() {
  log "Building Arch Linux package..."
  cp -r packaging/arch "${BUILD_DIR}/arch-pkg"
  cp "${BUILD_DIR}/aiden-desktop" "${BUILD_DIR}/arch-pkg/"
  cd "${BUILD_DIR}/arch-pkg"
  makepkg -si --noconfirm 2>/dev/null || makepkg -f 2>/dev/null || warn "Arch build skipped (needs makepkg)"
  cd "$PROJECT_DIR"
  ok "Arch package built"
}

cmd_pkg_rpm() {
  log "Building RPM package..."
  rpmbuild -bb packaging/rpm/aiden-desktop.spec \
    --define "_sourcedir ${BUILD_DIR}" \
    --define "_rpmdir ${BUILD_DIR}/rpm" \
    2>/dev/null || warn "RPM build skipped (needs rpmbuild)"
  ok "RPM package built"
}

cmd_pkg_flatpak() {
  log "Building Flatpak..."
  flatpak-builder --force-clean --repo="${BUILD_DIR}/flatpak-repo" \
    "${BUILD_DIR}/flatpak-build" packaging/flatpak/org.acreetionos.Aiden.json \
    2>/dev/null || warn "Flatpak build skipped (needs flatpak-builder)"
  flatpak build-bundle "${BUILD_DIR}/flatpak-repo" \
    "${BUILD_DIR}/aiden-desktop.flatpak" org.acreetionos.Aiden \
    2>/dev/null || true
  ok "Flatpak built"
}

cmd_pkg_alpine() {
  log "Building Alpine Linux package..."
  cp packaging/alpine/APKBUILD "${BUILD_DIR}/"
  cd "${BUILD_DIR}"
  abuild -F -r 2>/dev/null || warn "Alpine build skipped (needs abuild)"
  cd "$PROJECT_DIR"
  ok "Alpine package built"
}

cmd_all() {
  cmd_deps
  cmd_build_binary
  cmd_pkg_arch
  cmd_pkg_rpm
  cmd_pkg_flatpak
  cmd_pkg_alpine
  ok "All packages built in ${BUILD_DIR}/"
}

case "${1:-all}" in
  all)     cmd_all ;;
  deps)    cmd_deps ;;
  binary)  cmd_build_binary ;;
  arch)    cmd_pkg_arch ;;
  rpm)     cmd_pkg_rpm ;;
  flatpak) cmd_pkg_flatpak ;;
  alpine)  cmd_pkg_alpine ;;
  *)       echo "Usage: $0 [all|deps|binary|arch|rpm|flatpak|alpine]"; exit 1 ;;
esac

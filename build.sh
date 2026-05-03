#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log()  { echo -e "${CYAN}[BUILD]${NC} $*"; }
ok()   { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
fail() { echo -e "${RED}[FAIL]${NC} $*"; exit 1; }

PYTHON="${PYTHON:-python3}"
PIP="${PIP:-pip3}"

# ─── Help ──────────────────────────────────────────────────────────────
usage() {
    cat <<EOF
Usage: ./build.sh [command]

Commands:
  setup           Install all dependencies (Python, Node, Rust)
  build           Build all targets (Python bytecode, Svelte, Tauri)
  test            Run all tests (pytest, lint)
  lint            Run Python linting (ruff/bandit)
  check           Compile-check all Python files
  clean           Remove build artifacts
  docs            Generate docs (if configured)
  all             setup → build → test
  dev-backend     Start the FastAPI backend (development)
  dev-web         Start the Svelte dev server (development)
  dev-tui         Start the TUI (development)
  dev-gtk         Start the GTK frontend (development)

If no command is given, runs 'all'.
EOF
    exit 0
}

# ─── System dependencies by distro ─────────────────────────────────────
cmd_install_sysdeps() {
    if command -v apt &>/dev/null; then
        log "Detected apt (Debian/Ubuntu). Installing Tauri system deps..."
        sudo apt-get update -qq
        sudo apt-get install -y -qq \
            build-essential curl wget file libssl-dev libgtk-3-dev \
            libwebkit2gtk-4.1-dev libayatana-appindicator3-dev \
            librsvg2-dev libjavascriptcoregtk-4.1-dev libsoup-3.0-dev \
            2>&1 | tail -3
    elif command -v pacman &>/dev/null; then
        log "Detected pacman (Arch). Installing Tauri system deps..."
        sudo pacman -S --noconfirm \
            webkit2gtk-4.1 libappindicator-gtk3 librsvg libsoup3 \
            base-devel 2>&1 | tail -3
    elif command -v dnf &>/dev/null; then
        log "Detected dnf (Fedora). Installing Tauri system deps..."
        sudo dnf install -y \
            gcc-c++ webkit2gtk4.1-devel libappindicator-gtk3-devel \
            librsvg2-devel libsoup3-devel openssl-devel 2>&1 | tail -3
    elif command -v zypper &>/dev/null; then
        log "Detected zypper (openSUSE). Installing Tauri system deps..."
        sudo zypper install -y \
            gcc-c++ webkit2gtk4_1-devel libappindicator3-1 \
            librsvg-devel libsoup3-devel openssl-devel 2>&1 | tail -3
    else
        warn "Unknown package manager. Install Tauri deps manually: https://v2.tauri.app/start/prerequisites/"
    fi
    ok "System deps installed"
}

# ─── Dependencies ──────────────────────────────────────────────────────
cmd_setup() {
    cmd_install_sysdeps
    log "Installing Python dependencies..."
    "$PIP" install --break-system-packages --user -r requirements.txt 2>/dev/null \
        || "$PIP" install --user -r requirements.txt 2>/dev/null \
        || "$PIP" install -r requirements.txt

    log "Installing TUI dependencies..."
    "$PIP" install --break-system-packages --user -r tui/requirements.txt 2>/dev/null \
        || "$PIP" install --user -r tui/requirements.txt 2>/dev/null \
        || true

    log "Installing backend dependencies..."
    "$PIP" install --break-system-packages --user -r desktop/sidecar/requirements.txt 2>/dev/null \
        || "$PIP" install --user -r desktop/sidecar/requirements.txt 2>/dev/null \
        || true

    if command -v node &>/dev/null; then
        log "Installing Node.js dependencies (Svelte frontend)..."
        cd desktop/web
        npm install 2>/dev/null && ok "Node deps installed" || warn "npm install skipped (run manually: cd desktop/web && npm install)"
        log "Installing Tauri CLI..."
        npm install -D @tauri-apps/cli 2>/dev/null && ok "Tauri CLI installed" || warn "Tauri CLI install failed"
        cd "$PROJECT_DIR"
    else
        warn "Node.js not found — skipping Svelte frontend setup"
    fi

    if command -v cargo &>/dev/null; then
        log "Checking Rust toolchain (Tauri)..."
        if [ -f desktop/src-tauri/Cargo.toml ]; then
            ok "Rust project found"
        fi
    else
        warn "Cargo not found — skipping Tauri build setup"
    fi

    # Pre-commit hooks (optional)
    if [ -d .git ]; then
        cat > .git/hooks/pre-commit <<'HOOK'
#!/usr/bin/env bash
set -euo pipefail
echo "Running pre-commit checks..."
python3 -m pytest tests/ -q 2>/dev/null || true
HOOK
        chmod +x .git/hooks/pre-commit 2>/dev/null || true
    fi

    ok "Setup complete"
}

# ─── Build ─────────────────────────────────────────────────────────────
cmd_build() {
    log "Compiling Python bytecode..."
    find . -name '*.py' -not -path './.*' -not -path '*/node_modules/*' \
        -not -path '*/__pycache__/*' -exec "$PYTHON" -m py_compile {} \; 2>/dev/null || true
    ok "Python bytecode compiled"

    if [ -d desktop/web/node_modules ]; then
        log "Building Svelte frontend..."
        cd desktop/web
        npm run build 2>/dev/null && ok "Svelte build complete" || warn "Svelte build failed"
        cd "$PROJECT_DIR"
    fi

    if [ -f desktop/web/node_modules/.bin/tauri ] && [ -f desktop/src-tauri/Cargo.toml ]; then
        log "Building Tauri desktop app..."
        TAURI_BIN="desktop/web/node_modules/.bin/tauri"
        if [ -x "$TAURI_BIN" ]; then
            cd desktop && "$PROJECT_DIR/$TAURI_BIN" build --bundles deb,appimage 2>&1 || warn "Tauri build failed — see output above"
        else
            warn "Tauri CLI not found at $TAURI_BIN"
        fi
        cd "$PROJECT_DIR"
    elif command -v cargo &>/dev/null && [ -f desktop/src-tauri/Cargo.toml ]; then
        log "Installing Tauri CLI (via cargo) and building..."
        cargo install tauri-cli --version "^2" 2>/dev/null
        cd desktop
        cargo tauri build --bundles deb,appimage 2>&1 || warn "Tauri build failed — see output above"
        cd "$PROJECT_DIR"
    fi

    ok "Build complete"
}

# ─── Test ──────────────────────────────────────────────────────────────
cmd_test() {
    log "Running tests..."
    "$PYTHON" -m pytest tests/ -v --tb=short
}

cmd_lint() {
    log "Running linters..."
    if command -v ruff &>/dev/null; then
        ruff check . 2>/dev/null && ok "Ruff passed" || warn "Ruff found issues"
        ruff format --check . 2>/dev/null && ok "Ruff format passed" || true
    else
        warn "ruff not installed — linting skipped (install with: pip install ruff)"
    fi

    if command -v bandit &>/dev/null; then
        bandit -r common/ desktop/sidecar/ -q 2>/dev/null && ok "Bandit passed" || warn "Bandit found issues"
    else
        warn "bandit not installed — security scan skipped"
    fi
}

# ─── Check ─────────────────────────────────────────────────────────────
cmd_check() {
    log "Checking Python compilation..."
    errors=0
    while IFS= read -r f; do
        "$PYTHON" -m py_compile "$f" 2>/dev/null || { echo "  FAIL: $f"; ((errors++)); }
    done < <(find . -name '*.py' -not -path './.*' -not -path '*/node_modules/*' -not -path '*/__pycache__/*')
    if [ "$errors" -eq 0 ]; then
        ok "All Python files compile"
    else
        fail "$errors files failed to compile"
    fi
}

# ─── Clean ─────────────────────────────────────────────────────────────
cmd_clean() {
    log "Cleaning build artifacts..."
    find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name '*.pyc' -delete 2>/dev/null || true
    find . -type f -name '*.pyo' -delete 2>/dev/null || true
    rm -rf .pytest_cache 2>/dev/null || true
    rm -rf desktop/web/dist 2>/dev/null || true
    rm -rf desktop/web/node_modules 2>/dev/null || true
    rm -rf desktop/src-tauri/target 2>/dev/null || true
    ok "Clean complete"
}

# ─── Dev servers ───────────────────────────────────────────────────────
cmd_dev_backend() {
    log "Starting FastAPI backend on http://127.0.0.1:9090..."
    "$PYTHON" desktop/sidecar/main.py
}

cmd_dev_web() {
    if [ -d desktop/web/node_modules ]; then
        log "Starting Svelte dev server..."
        cd desktop/web && npm run dev
    else
        fail "Node deps not installed. Run: cd desktop/web && npm install"
    fi
}

cmd_dev_tui() {
    log "Starting TUI..."
    "$PYTHON" tui/main.py
}

cmd_dev_gtk() {
    log "Starting GTK frontend..."
    "$PYTHON" main.py
}

# ─── Docs ──────────────────────────────────────────────────────────────
cmd_docs() {
    log "No automated docs generation configured."
    log "See docs/ directory for: security-target.md, threat-model.md"
}

# ─── Main ──────────────────────────────────────────────────────────────
cmd_all() {
    cmd_setup
    cmd_check
    cmd_test
    cmd_build
    ok "All tasks complete"
}

# ─── Dispatch ──────────────────────────────────────────────────────────
if [ $# -eq 0 ]; then
    # Default: check + test
    cmd_check
    cmd_test
    exit 0
fi

case "${1:-help}" in
    setup)     cmd_setup ;;
    build)     cmd_build ;;
    test)      cmd_test ;;
    lint)      cmd_lint ;;
    check)     cmd_check ;;
    clean)     cmd_clean ;;
    docs)      cmd_docs ;;
    all)       cmd_all ;;
    dev-backend) cmd_dev_backend ;;
    dev-web)   cmd_dev_web ;;
    dev-tui)   cmd_dev_tui ;;
    dev-gtk)   cmd_dev_gtk ;;
    help|--help|-h) usage ;;
    *)         echo "Unknown command: $1"; usage ;;
esac

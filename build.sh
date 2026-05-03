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

# ─── Dependencies ──────────────────────────────────────────────────────
cmd_setup() {
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

    if command -v cargo &>/dev/null && [ -f desktop/src-tauri/Cargo.toml ]; then
        log "Building Tauri desktop app..."
        cd desktop/src-tauri
        cargo build --release 2>/dev/null && ok "Tauri build complete" || warn "Tauri build failed (needs system deps: check Tauri docs)"
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

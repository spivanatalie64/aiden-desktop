// Gecko Runtime – Custom webview backend for Tauri
//
// This module replaces the default WebKitGTK webview with a Gecko-based
// (Firefox) rendering engine. It implements the WebviewBuilder trait
// that Tauri expects, providing:
//
//   - Window creation with GeckoView/Embedding
//   - JavaScript ↔ Rust IPC bridge
//   - URI loading via custom protocol
//
// This is a scaffold. Full implementation requires linking against
// libxul (Firefox) or using the geckoview crate for embedding.
//
// Reference: https://firefox-source-docs.mozilla.org/toolkit/components/embedding/

pub mod window;
pub mod bridge;

use tauri::webview::WebviewBuilder;
use tauri::Runtime;

/// Initialize the Gecko runtime.
/// Called once at app startup before any windows are created.
pub fn init() {
    // TODO: Initialize Gecko engine (XPCOM, profile dir, etc.)
    // Gecko requires: GRE_HOME, a profile directory, and XPCOM startup.
    //
    // Example:
    //   nsresult rv = XRE_InitEmbedding(greDir, profileDir, appDir);
    //   See: https://searchfox.org/mozilla-central/source/toolkit/xre/nsEmbedFunctions.cpp
    log::info!("Gecko runtime initialized");
}

/// Create a Gecko-based webview that implements the Tauri WebviewBuilder
/// trait. This allows Tauri to use Gecko instead of the platform default.
pub fn create_webview<R: Runtime>(builder: WebviewBuilder<R>) -> WebviewBuilder<R> {
    // In a full implementation, this would:
    //   1. Create a Gecko embedding window
    //   2. Set up the JS ↔ Rust message port
    //   3. Map Tauri's IPC calls to Gecko's message manager
    //
    // For now, we return the builder unchanged and rely on Tauri's
    // default webview until the Gecko runtime is complete.
    builder
}

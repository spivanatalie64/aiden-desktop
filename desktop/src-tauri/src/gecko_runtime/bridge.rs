// IPC Bridge – JavaScript ↔ Rust communication for Gecko.
//
// Tauri's standard IPC uses webview.evaluate_script() and custom URL
// protocol handlers. In Gecko, this maps to:
//   - nsIMessageSender / nsIMessageListenerManager (frame script messages)
//   - Custom protocol via nsIProtocolHandler
//
// This is a placeholder for the bridge implementation.

use serde_json::Value;

/// Send a message from Rust to the JavaScript running in the Gecko view.
pub fn send_to_js(_window_id: u64, command: &str, payload: &Value) {
    // TODO: Use Gecko's message manager to send to content:
    //   nsIFrameScriptLoader::loadFrameScript()
    //   nsIMessageBroadcaster::broadcastAsyncMessage()
    log::info!("JS send: {} {:?}", command, payload);
}

/// Handle a message received from JavaScript (via Gecko's message manager).
pub fn on_js_message(_window_id: u64, command: &str, payload: &Value) -> Option<Value> {
    // Route to Tauri's command handler
    log::info!("JS recv: {} {:?}", command, payload);
    None
}

// AIDEN Desktop – Tauri main (Gecko backend)
// This uses a custom Gecko-based webview runtime.
// See src/gecko_runtime/ for the Gecko embedding implementation.

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod gecko_runtime;

use tauri::Manager;

/// Tauri command: spawn the Python backend sidecar
#[tauri::command]
fn start_backend(app: tauri::AppHandle) -> Result<(), String> {
    let sidecar = app.shell().sidecar("aiden-backend")
        .map_err(|e| format!("Failed to spawn sidecar: {}", e))?;
    let (mut _rx, _child) = sidecar
        .spawn()
        .map_err(|e| format!("Failed to start sidecar: {}", e))?;
    Ok(())
}

/// Tauri command: call the Python backend HTTP API
#[tauri::command]
async fn api(path: String, method: String, body: Option<String>) -> Result<String, String> {
    let client = reqwest::Client::new();
    let url = format!("http://127.0.0.1:9090{}", path);
    let req = match method.as_str() {
        "GET" => client.get(&url),
        "POST" => {
            let mut r = client.post(&url);
            if let Some(b) = body {
                r = r.header("Content-Type", "application/json").body(b);
            }
            r
        }
        "PUT" => {
            let mut r = client.put(&url);
            if let Some(b) = body {
                r = r.header("Content-Type", "application/json").body(b);
            }
            r
        }
        _ => return Err(format!("Unsupported method: {}", method)),
    };
    let resp = req.send().await.map_err(|e| format!("Request failed: {}", e))?;
    let text = resp.text().await.map_err(|e| format!("Read failed: {}", e))?;
    Ok(text)
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![start_backend, api])
        .run(tauri::generate_context!())
        .expect("error while running AIDEN desktop");
}

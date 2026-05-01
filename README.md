Aiden Desktop Frontend (GNOME / Cinnamon)

Overview
 - Native GTK (Python + PyGObject) frontend for AIDEN.
 - Stores conversations encrypted per-user under ~/.local/share/aiden.
 - Derives encryption key from a user password (PBKDF2+AES via cryptography).
 - Uses a configurable OpenRouter proxy URL; code enforces using the proxy and aims to select free/OpenRouter backends only.
 - Keeps model prompt context small: extracts short, relevant snippets from local encrypted files rather than sending full files.

Quick start
1. Create a virtualenv and install dependencies:
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2. Run the app:
   python main.py

Configuration
- Default storage: ~/.local/share/aiden
- Default proxy URL: https://aiden.acreetionos.org/api/chat (edit in main.py or settings)

Settings
 - The app stores settings in ~/.config/aiden/settings.json. You can change proxy URL, storage dir, helper path, and model whitelist using the Settings button in the UI.

Packaging
 - Flatpak manifest scaffold: packaging/flatpak/org.acreetionos.Aiden.json
 - Debian scaffold notes: packaging/debian/README_DEB.md

Security notes
- The app derives an encryption key from a password you enter. Do not forget it — there is no recovery.
- This app does not ship an API key. It expects a proxy endpoint that handles model access (recommended).

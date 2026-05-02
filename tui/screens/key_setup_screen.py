"""Key setup screen – first-time SSH key configuration."""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)))

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, Input, Label
from textual.containers import Container, Vertical

from common.crypto import discover_ssh_keys, load_key_from_file, generate_key_in_sandbox
from common.audit import emit_auth
from settings import load_settings, save_settings


class KeySetupScreen(Screen):
    BINDINGS = [
        ('escape', 'back', 'Back'),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id='key-setup-container'):
            yield Static('[bold]LAN Mesh – SSH Key Setup[/]', id='key-setup-title')
            yield Static(
                'You need an Ed25519 SSH key for node authentication on the LAN mesh.',
                id='key-setup-desc',
            )
            yield Static('', id='key-status')
            yield Button('Use existing key from ~/.ssh', id='use-existing-btn')
            yield Button('Generate new key (in sandboxed VM)', id='generate-btn')
            yield Button('Skip (disable LAN mesh)', id='skip-btn')
        yield Footer()

    def on_mount(self) -> None:
        keys = discover_ssh_keys()
        status = self.query_one('#key-status', Static)
        if keys:
            key_list = '\n'.join(f'  • {p}' for p in keys)
            status.update(f'[green]Found keys:[/]\n{key_list}')
        else:
            status.update('[yellow]No existing SSH keys found in ~/.ssh[/]')

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'use-existing-btn':
            self._use_existing()
        elif event.button.id == 'generate-btn':
            self._generate_new()
        elif event.button.id == 'skip-btn':
            settings = load_settings()
            settings['mesh_enabled'] = False
            save_settings(settings)
            self.app.notify('LAN mesh disabled. You can enable it later in Settings.', severity='warning')
            self.action_back()

    def _use_existing(self) -> None:
        keys = discover_ssh_keys()
        if not keys:
            self.app.notify('No existing keys found. Generate a new one.', severity='error')
            return
        try:
            key_path = keys[0]
            identity = load_key_from_file(key_path)
            settings = load_settings()
            settings['ssh_key_path'] = str(key_path)
            settings['mesh_enabled'] = True
            save_settings(settings)
            emit_auth(os.getenv('USER', 'unknown'), 'success', 'ssh_key')
            self.app.notify(f'Loaded key: {identity.fingerprint}', severity='information')
            self.action_back()
        except Exception as e:
            self.app.notify(f'Failed to load key: {e}', severity='error')

    def _generate_new(self) -> None:
        target = Path.home() / '.ssh' / 'id_aiden_mesh'
        try:
            result = generate_key_in_sandbox(target)
            if result.get('success'):
                settings = load_settings()
                settings['ssh_key_path'] = str(target)
                settings['mesh_enabled'] = True
                save_settings(settings)
                emit_auth(os.getenv('USER', 'unknown'), 'success', 'ssh_key_gen')
                self.app.notify(f'Key generated at: {target}', severity='information')
                self.action_back()
            else:
                self.app.notify(f'Generation failed: {result.get("error")}', severity='error')
        except Exception as e:
            self.app.notify(f'Generation failed: {e}', severity='error')

    def action_back(self) -> None:
        self.app.pop_screen()

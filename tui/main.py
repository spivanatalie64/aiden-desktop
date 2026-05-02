#!/usr/bin/env python3
"""AIDEN TUI – Textual terminal UI for AIDEN."""

import os
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, Input, Label
from textual.containers import Container, Horizontal, Vertical
from textual import events

from common.presets import list_presets, get_preset
from settings import (
    load_settings, save_settings, is_disclaimer_accepted, accept_disclaimer,
    get_active_preset, set_active_preset,
)

from tui.screens.chat_screen import ChatScreen
from tui.screens.history_screen import HistoryScreen
from tui.screens.settings_screen import SettingsScreen
from tui.screens.process_screen import ProcessScreen
from tui.screens.developer_screen import DeveloperScreen
from tui.screens.mesh_screen import MeshScreen
from tui.screens.key_setup_screen import KeySetupScreen


class DisclaimerScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Container(
            Static(
                '[bold red]⚠ AIDEN – System Access Notice[/]\n\n'
                'AIDEN has been granted the ability to execute arbitrary code '
                'and commands on your system.\n\n'
                '• Code you ask AIDEN to run will be executed with YOUR user '
                'permissions (and with elevated privileges via polkit where authorized).\n'
                '• You are solely responsible for any commands, scripts, or operations '
                'AIDEN performs at your direction.\n'
                '• Review all commands before execution.\n'
                '• This is a tool — you are in control.\n\n'
                '[italic]By accepting, you agree to take full responsibility for your use of AIDEN.[/]',
                id='disclaimer-text',
            ),
            Horizontal(
                Button('I Accept & Understand', variant='primary', id='accept'),
                Button('Credits →', id='credits'),
                Button('Decline', variant='error', id='decline'),
                id='disclaimer-buttons',
            ),
            id='disclaimer-container',
        )

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == 'accept':
            accept_disclaimer()
            self.app.pop_screen()
            self.app.push_screen('chat')
        elif event.button.id == 'credits':
            self.app.push_screen('credits')
        elif event.button.id == 'decline':
            self.app.exit()


class CreditsScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Container(
            Static(
                '[bold]AIDEN Desktop – AcreetionOS AI Assistant[/]\n\n'
                'Developed by Natalie Spiva (@sprungles) & Darren Clift\n'
                'for the AcreetionOS Project\n\n'
                '[bold]Powered by:[/]\n'
                '• OpenRouter API proxy\n'
                '• Python + PyGObject (GTK frontend)\n'
                '• Svelte + Tauri (Desktop webview)\n'
                '• Textual (Terminal UI)\n'
                '• cryptography (AES-GCM encrypted storage)\n'
                '• requests, httpx, FastAPI, uvicorn\n'
                '• marked, highlight.js\n\n'
                '[italic]Built on open-source software. Licensed under GPL-3.0-or-later.[/]',
                id='credits-text',
            ),
            Button('Back', id='back'),
            id='credits-container',
        )

    def on_button_pressed(self, event: Button.Pressed):
        self.app.pop_screen()


class AidenTUI(App):
    CSS_PATH = 'theme/acreetionos.tcss'
    SCREENS = {
        'chat': ChatScreen,
        'history': HistoryScreen,
        'settings': SettingsScreen,
        'processes': ProcessScreen,
        'developer': DeveloperScreen,
        'mesh': MeshScreen,
        'key_setup': KeySetupScreen,
        'credits': CreditsScreen,
    }

    BINDINGS = [
        ('1', 'switch_to_chat', 'Chat'),
        ('2', 'switch_to_history', 'History'),
        ('3', 'switch_to_processes', 'Processes'),
        ('4', 'switch_to_settings', 'Settings'),
        ('5', 'switch_to_mesh', 'Mesh'),
        ('ctrl+d', 'switch_to_developer', 'Dev'),
    ]

    def on_ready(self) -> None:
        self.title = 'AIDEN — AcreetionOS Assistant'
        self.sub_title = 'Terminal UI'

        if not is_disclaimer_accepted():
            self.push_screen(DisclaimerScreen())
        else:
            self.switch_screen('chat')

    def action_switch_to_chat(self):
        self.switch_screen('chat')

    def action_switch_to_history(self):
        self.push_screen('history')

    def action_switch_to_processes(self):
        self.push_screen('processes')

    def action_switch_to_settings(self):
        self.push_screen('settings')

    def action_switch_to_mesh(self):
        self.push_screen('mesh')

    def action_switch_to_developer(self):
        self.push_screen('developer')


def main():
    app = AidenTUI()
    app.run()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Input, Button, ListView, ListItem
from textual.containers import Container, Horizontal, Vertical

from common.presets import list_presets, get_preset
from settings import (
    load_settings, save_settings, is_disclaimer_accepted, accept_disclaimer,
    get_active_preset, set_active_preset, DEFAULT_SETTINGS,
)


class DisclaimerScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Static(
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
            id='disclaimer',
        )
        yield Button('I Accept & Understand', variant='primary', id='accept')
        yield Button('Credits →', id='credits')
        yield Button('Decline', variant='error', id='decline')

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == 'accept':
            accept_disclaimer()
            self.app.pop_screen()
            self.app.push_screen(ChatScreen())
        elif event.button.id == 'credits':
            self.app.push_screen(CreditsScreen())
        elif event.button.id == 'decline':
            self.app.exit()


class CreditsScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Static(
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
            id='credits',
        )
        yield Button('Back', id='back')

    def on_button_pressed(self, event: Button.Pressed):
        self.app.pop_screen()


class ChatScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static('', id='chat-log'),
            Input(placeholder='Ask AIDEN...', id='chat-input'),
            id='chat-container',
        )
        yield Footer()

    def on_input_submitted(self, event: Input.Submitted):
        if event.value.strip():
            chat_log = self.query_one('#chat-log', Static)
            chat_log.update(chat_log.renderable + f'\nYou: {event.value}')
            event.input.clear()


class SettingsScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Static('Settings', id='settings-title')
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        self.app.pop_screen()


class AidenTUI(App):
    def on_ready(self) -> None:
        if not is_disclaimer_accepted():
            self.push_screen(DisclaimerScreen())
        else:
            self.push_screen(ChatScreen())


def main():
    app = AidenTUI()
    app.run()


if __name__ == '__main__':
    main()

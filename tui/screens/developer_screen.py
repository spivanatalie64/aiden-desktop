"""Developer screen – advanced configuration."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)))

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Input, Button, Label, TabbedContent, TabPane
from textual.containers import Container, ScrollableContainer

from settings import load_settings, save_settings, get_providers, add_provider, remove_provider


class DeveloperScreen(Screen):
    BINDINGS = [
        ('escape', 'back', 'Back'),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with ScrollableContainer():
            yield Static('[bold]Developer Menu[/]', id='dev-title')
            with TabbedContent(initial='providers'):
                with TabPane('API Providers', id='providers'):
                    yield Static('[bold]Add Provider[/]')
                    yield Input(placeholder='Provider name', id='provider-name')
                    yield Input(placeholder='Base URL', id='provider-url')
                    yield Input(placeholder='API Key (optional)', id='provider-key', password=True)
                    yield Button('Add Provider', id='add-provider-btn')
                    yield Static('', id='providers-list')

                with TabPane('Model Params', id='params'):
                    yield Static('[bold]Default Parameters[/]')
                    s = load_settings()
                    yield Static('Temperature:')
                    yield Input(value=str(s.get('temperature', 0.7)), id='dev-temp')
                    yield Static('Max Tokens:')
                    yield Input(value=str(s.get('max_tokens', 4096)), id='dev-maxtokens')
                    yield Static('Reasoning Effort:')
                    yield Input(value=str(s.get('reasoning_effort', 'auto')), id='dev-reasoning')

                with TabPane('Tool Config', id='tools'):
                    s = load_settings()
                    yield Static('[bold]Code Execution Mode[/]')
                    yield Input(value=s.get('code_exec_mode', 'click_to_run'), id='dev-exec-mode')
                    yield Static('Sandbox Timeout (seconds):')
                    yield Input(value=str(s.get('code_exec_timeout', 30)), id='dev-timeout')

                with TabPane('Debug Logs', id='debug'):
                    yield Static('[bold]Backend Logs[/]')
                    yield Static('(Connect to FastAPI backend on 127.0.0.1:9090)', id='debug-info')
                    yield Button('Test Proxy Health', id='test-proxy-btn')

            yield Button('Save', variant='primary', id='dev-save-btn')
            yield Button('Back', id='back-btn')
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_providers()

    def _refresh_providers(self) -> None:
        providers = get_providers()
        label = self.query_one('#providers-list', Static)
        if providers:
            lines = ['[bold]Current Providers:[/]']
            for p in providers:
                lines.append(f'  * {p["name"]} - {p["base_url"]}')
            label.update('\n'.join(lines))
        else:
            label.update('[dim]No providers configured[/]')

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'add-provider-btn':
            name = self.query_one('#provider-name', Input).value
            url = self.query_one('#provider-url', Input).value
            key = self.query_one('#provider-key', Input).value
            if name and url:
                add_provider(name, url, key)
                self._refresh_providers()
                self.notify(f'Added provider: {name}')
        elif event.button.id == 'dev-save-btn':
            s = load_settings()
            try:
                s['temperature'] = float(self.query_one('#dev-temp', Input).value)
                s['max_tokens'] = int(self.query_one('#dev-maxtokens', Input).value)
                s['reasoning_effort'] = self.query_one('#dev-reasoning', Input).value
                s['code_exec_mode'] = self.query_one('#dev-exec-mode', Input).value
                s['code_exec_timeout'] = int(self.query_one('#dev-timeout', Input).value)
                save_settings(s)
                self.notify('Developer settings saved')
            except ValueError:
                self.notify('Invalid number value', severity='error')
        elif event.button.id == 'back-btn':
            self.action_back()

    def action_back(self) -> None:
        self.app.pop_screen()

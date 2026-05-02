"""Mesh screen – LAN peer discovery and cache management."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)))

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, DataTable, Label
from textual.containers import Container, Horizontal

from settings import load_settings, save_settings


class MeshScreen(Screen):
    BINDINGS = [
        ('escape', 'back', 'Back'),
        ('r', 'refresh', 'Refresh'),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id='mesh-container'):
            yield Static('[bold]LAN Mesh[/]', id='mesh-title')
            with Horizontal(id='mesh-controls'):
                yield Button('Refresh', id='refresh-btn')
                yield Button('Back', id='back-btn')
            yield DataTable(id='peers-table')
        yield Footer()

    def on_mount(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        table = self.query_one('#peers-table', DataTable)
        table.clear()
        table.add_columns('Node ID', 'Hostname', 'Fingerprint', 'Status')
        settings = load_settings()
        if not settings.get('mesh_enabled'):
            table.add_row('(Mesh disabled)', '', '', 'Enable in Settings')
            return
        table.add_row('(Scanning...)', '', '', 'mDNS active')

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'refresh-btn':
            self._refresh()
        elif event.button.id == 'back-btn':
            self.action_back()

    def action_refresh(self) -> None:
        self._refresh()

    def action_back(self) -> None:
        self.app.pop_screen()

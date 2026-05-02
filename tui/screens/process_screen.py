"""Process screen – systemd service management and system monitoring."""
import asyncio

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, ListView, ListItem, Button, Label, DataTable
from textual.containers import Container, Horizontal, Vertical

from common.sandbox import run_sandboxed
from common.audit import emit_code_exec
from settings import load_settings


class ProcessScreen(Screen):
    BINDINGS = [('escape', 'back', 'Back'), ('r', 'refresh', 'Refresh')]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static('[bold]System Resources[/]', id='resources-title'),
            Static('Loading...', id='resources-display'),
            Static('\n[bold]Services[/]', id='services-title'),
            DataTable(id='services-table'),
            Static('\n[bold]Quick Execute[/]', id='exec-title'),
            id='process-container',
        )
        yield Footer()

    def on_mount(self) -> None:
        self._load_resources()
        self._load_services()

    def _load_resources(self) -> None:
        text = ['[bold]System Resources[/]']
        try:
            import psutil
            text.append(f'CPU: {psutil.cpu_percent(interval=0.5)}% ({psutil.cpu_count()} cores)')
            mem = psutil.virtual_memory()
            text.append(f'RAM: {mem.percent}% ({mem.used // (1024**3)}GB / {mem.total // (1024**3)}GB)')
            disk = psutil.disk_usage('/')
            text.append(f'Disk: {disk.percent}% ({disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB)')
        except ImportError:
            text.append('[italic]Install psutil for resource monitoring[/]')
        self.query_one('#resources-display', Static).update('\n'.join(text))

    def _load_services(self) -> None:
        import subprocess
        table = self.query_one('#services-table', DataTable)
        table.clear()
        try:
            result = subprocess.run(
                ['systemctl', 'list-units', '--type=service', '--no-pager',
                 '--no-legend', '--plain'],
                capture_output=True, text=True, timeout=10,
            )
            table.add_columns('Name', 'Active', 'Sub', 'Description')
            for line in result.stdout.strip().split('\n')[:20]:
                if not line.strip():
                    continue
                parts = line.split(None, 4)
                if len(parts) >= 4:
                    table.add_row(parts[0], parts[2], parts[3], parts[4] if len(parts) > 4 else '')
        except (subprocess.TimeoutExpired, FileNotFoundError):
            table.add_row('(systemctl not available)', '', '', '')

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.row_key:
            name = event.row_key.value
            self._show_service_actions(name)

    def _show_service_actions(self, name: str) -> None:
        from textual.widgets import Button
        # Inline actions: clicking service opens restart/toggle prompt
        emit_code_exec('tui', '', 'service', name, True, 'systemctl', 0, 'click_to_run')

    def action_refresh(self):
        self._load_resources()
        self._load_services()

    def action_back(self):
        self.app.pop_screen()

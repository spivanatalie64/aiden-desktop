"""History screen – browse, search, and view past conversations."""
from pathlib import Path

from textual.app import ComposeResult
from textual.screen import Screen, ModalScreen
from textual.widgets import Header, Footer, Static, ListView, ListItem, Input, Button, TextArea
from textual.containers import Container, Horizontal

from aiden_storage import list_conversations, decrypt_conversation
from settings import load_settings


class PasswordModal(ModalScreen):
    def __init__(self, cid: str):
        super().__init__()
        self.cid = cid

    def compose(self) -> ComposeResult:
        yield Container(
            Static(f'[bold]Decrypt:[/] {self.cid}', id='modal-title'),
            Input(placeholder='Storage password', id='pwd-input', password=True),
            Horizontal(
                Button('Decrypt', variant='primary', id='decrypt-btn'),
                Button('Cancel', id='cancel-btn'),
            ),
            id='modal-container',
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'decrypt-btn':
            pwd = self.query_one('#pwd-input', Input).value
            if pwd:
                self.dismiss(pwd)
        elif event.button.id == 'cancel-btn':
            self.dismiss(None)


class HistoryScreen(Screen):
    BINDINGS = [('escape', 'back', 'Back')]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Input(placeholder='Search conversations...', id='search-input'),
            ListView(id='conversation-list'),
            Static('', id='preview-area'),
            id='history-container',
        )
        yield Footer()

    def on_mount(self) -> None:
        self._load_conversations()

    def _load_conversations(self, search: str = '') -> None:
        settings = load_settings()
        base = Path(settings.get('storage_dir', str(Path.home() / '.local' / 'share' / 'aiden')))
        convos = list_conversations(base)
        lst = self.query_one('#conversation-list', ListView)
        lst.clear()
        for cid in sorted(convos, reverse=True):
            if search and search.lower() not in cid.lower():
                continue
            lst.append(ListItem(Static(cid)))

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == 'search-input':
            self._load_conversations(event.value)

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item:
            cid = event.item.children[0].renderable
            pwd = await self.app.push_screen_wait(PasswordModal(cid))
            if not pwd:
                return

            preview = self.query_one('#preview-area', Static)
            settings = load_settings()
            base = Path(settings.get('storage_dir', str(Path.home() / '.local' / 'share' / 'aiden')))
            try:
                text = decrypt_conversation(cid, pwd, base)
                preview.update(f'[bold]Conversation:[/] {cid}\n\n{text[:2000]}')
                preview.update(
                    f'[bold]Conversation:[/] {cid}\n\n'
                    f'[bold #2ecc71]Decrypted successfully[/]\n\n'
                    f'{text[:2000]}'
                )
            except Exception:
                preview.update(
                    f'[bold #e74c3c]Decryption failed.[/] Check your password.'
                )

    def action_back(self):
        self.app.pop_screen()

"""Chat screen – main chat interface with streaming, code execution, presets."""
import asyncio
import json
from pathlib import Path

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Input, Button, Select, RichLog
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive

from common.llm_client import AsyncOpenRouterClient
from common.presets import list_presets, get_preset
from common.sandbox import run_sandboxed
from common.audit import emit_code_exec
from settings import load_settings, get_active_preset, set_active_preset, get_code_exec_mode


class ChatScreen(Screen):
    BINDINGS = [
        ('escape', 'focus_input', 'Chat'),
        ('ctrl+l', 'clear_chat', 'Clear'),
    ]

    messages = reactive([])

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Horizontal(
                Select(
                    [(k, v) for k, v in list_presets()],
                    prompt='Preset',
                    id='preset-select',
                ),
                Button('⚙', id='settings-btn'),
                id='toolbar',
            ),
            RichLog(id='chat-log', highlight=True, markup=True),
            Input(placeholder='Ask AIDEN... (Ctrl+Enter to send)', id='chat-input'),
            Container(
                Button('Send', variant='primary', id='send-btn'),
                Button('🔍 Web', id='web-toggle'),
                id='input-actions',
            ),
            id='chat-container',
        )
        yield Footer()

    def on_mount(self) -> None:
        chat_log = self.query_one('#chat-log', RichLog)
        chat_log.write('[bold]Welcome to AIDEN![/]')
        chat_log.write('[italic]Type a message and press Ctrl+Enter to begin.[/]\n')

    def action_focus_input(self):
        self.query_one('#chat-input', Input).focus()

    def action_clear_chat(self):
        chat_log = self.query_one('#chat-log', RichLog)
        chat_log.clear()
        chat_log.write('[bold]Chat cleared.[/]\n')

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == 'chat-input' and event.value.strip():
            await self._send_message(event.value.strip())
            event.input.clear()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'send-btn':
            inp = self.query_one('#chat-input', Input)
            if inp.value.strip():
                await self._send_message(inp.value.strip())
                inp.clear()
        elif event.button.id == 'settings-btn':
            await self.app.push_screen('settings')

    async def _send_message(self, text: str) -> None:
        chat_log = self.query_one('#chat-log', RichLog)
        chat_log.write(f'[bold #2ecc71]You:[/] {text}')

        settings = load_settings()
        proxy = settings.get('proxy_url', 'https://aiden.acreetionos.org/api/chat')
        active = get_active_preset()
        system_prompt = active.get('system_prompt', 'You are AIDEN, a helpful assistant.')
        model = active.get('model', None)

        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': text},
        ]

        client = AsyncOpenRouterClient(proxy)
        try:
            chat_log.write('[bold #61afef]AIDEN:[/] ', end='')
            async for token in client.stream_chat(messages, model):
                chat_log.write(token, end='')
            chat_log.write('')
        except Exception as e:
            chat_log.write(f'[bold #e74c3c]Error:[/] {e}')
        finally:
            await client.close()

    async def _on_code_block_run(self, code: str, lang: str) -> None:
        chat_log = self.query_one('#chat-log', RichLog)
        mode = get_code_exec_mode()
        approved = mode != 'click_to_run'

        if mode == 'click_to_run':
            chat_log.write(f'[bold #f39c12]Confirm execution:[/]')
            chat_log.write(f'[bold]Language:[/] {lang}')
            chat_log.write(code[:200] + ('...' if len(code) > 200 else ''))
            chat_log.write('[italic]Set mode to auto-run in Settings to skip confirmation.[/]')

        import hashlib
        code_hash = hashlib.sha256(code.encode()).hexdigest()[:16]

        result = run_sandboxed(code, lang)

        emit_code_exec(
            user='tui',
            session='',
            lang=lang,
            code_hash=code_hash,
            approved=approved,
            sandbox='bubblewrap',
            exit_code=result['exit_code'],
            mode=mode,
        )

        output = result['stdout'] or result['stderr'] or '(no output)'
        chat_log.write(f'[bold #2ecc71]Output:[/]\n{output[:2000]}')
        if result['timeout']:
            chat_log.write('[bold #e74c3c]Execution timed out[/]')

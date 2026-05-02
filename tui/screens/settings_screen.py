"""Settings screen – app configuration, presets, code exec mode."""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Input, Button, Select, Label, TabbedContent, TabPane
from textual.containers import Container, Horizontal, Vertical

from settings import (
    load_settings, save_settings, get_presets, save_preset,
    get_code_exec_mode, set_code_exec_mode, DEFAULT_SETTINGS,
)
from common.presets import list_presets, preset_keys


class SettingsScreen(Screen):
    BINDINGS = [('escape', 'back', 'Back')]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            TabbedContent(
                TabPane('General', id='general-tab'),
                TabPane('Presets', id='presets-tab'),
                TabPane('Code Execution', id='code-tab'),
            ),
            id='settings-container',
        )
        yield Footer()

    def on_mount(self) -> None:
        self._build_general_tab()
        self._build_presets_tab()
        self._build_code_tab()

    def _build_general_tab(self) -> None:
        settings = load_settings()
        tab = self.query_one('#general-tab', TabPane)
        tab.remove_children()

        self._proxy_input = Input(
            value=settings.get('proxy_url', DEFAULT_SETTINGS['proxy_url']),
            placeholder='Proxy URL',
            id='proxy-url',
        )
        self._storage_input = Input(
            value=settings.get('storage_dir', DEFAULT_SETTINGS['storage_dir']),
            placeholder='Storage directory',
            id='storage-dir',
        )
        self._helper_input = Input(
            value=settings.get('helper_path', DEFAULT_SETTINGS['helper_path']),
            placeholder='Helper path',
            id='helper-path',
        )
        self._temperature_input = Input(
            value=str(settings.get('temperature', DEFAULT_SETTINGS['temperature'])),
            placeholder='Temperature (0.0-2.0)',
            id='temperature',
        )
        save_btn = Button('Save', variant='primary', id='save-general')

        tab.mount(
            Label('[bold]General Settings[/]'),
            Label('Proxy URL:'), self._proxy_input,
            Label('Storage dir:'), self._storage_input,
            Label('Helper path:'), self._helper_input,
            Label('Temperature:'), self._temperature_input,
            save_btn,
        )

    def _build_presets_tab(self) -> None:
        tab = self.query_one('#presets-tab', TabPane)
        tab.remove_children()
        tab.mount(Label('[bold]Presets[/]'))
        self._preset_widgets = {}
        presets = get_presets()
        for key in preset_keys():
            p = presets.get(key, {})
            tab.mount(Label(f'\n{key}'))
            inp = Input(
                value=p.get('system_prompt', ''),
                placeholder=f'{p.get("name", key)} system prompt',
                id=f'preset-{key}',
            )
            self._preset_widgets[key] = inp
            tab.mount(inp)
        tab.mount(Button('Save Presets', variant='primary', id='save-presets'))

    def _build_code_tab(self) -> None:
        tab = self.query_one('#code-tab', TabPane)
        tab.remove_children()
        mode = get_code_exec_mode()
        tab.mount(
            Label('[bold]Code Execution Mode[/]'),
            Select(
                [
                    ('click_to_run', 'Click to run (safest)'),
                    ('trust_conversation', 'Trust per conversation'),
                    ('auto_run_safe', 'Auto-run safe languages'),
                    ('auto_run_all', 'Auto-run all (fastest)'),
                ],
                value=mode,
                id='code-mode',
            ),
            Label('\n[italic]Click-to-run requires explicit confirmation for every execution.[/]'),
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'save-general':
            settings = load_settings()
            settings['proxy_url'] = self._proxy_input.value
            settings['storage_dir'] = self._storage_input.value
            settings['helper_path'] = self._helper_input.value
            try:
                settings['temperature'] = float(self._temperature_input.value)
            except ValueError:
                pass
            save_settings(settings)
            self.notify('Settings saved', severity='information')
        elif event.button.id == 'save-presets':
            for key, inp in self._preset_widgets.items():
                presets = get_presets()
                if key in presets:
                    presets[key]['system_prompt'] = inp.value
                    save_preset(key, presets[key])
            self.notify('Presets saved', severity='information')

    def action_back(self):
        self.app.pop_screen()

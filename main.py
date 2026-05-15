#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import threading
import time
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aiden_storage import encrypt_and_store, list_conversations, search_snippets
from openrouter_client import OpenRouterClient
from settings import (
    load_settings, save_settings, is_disclaimer_accepted, accept_disclaimer,
    get_active_preset, set_active_preset, get_presets, save_preset,
    DEFAULT_SETTINGS,
)
from common.presets import PRESETS, list_presets, preset_keys
import subprocess
from pathlib import Path

DEFAULT_PROXY = "https://aiden.acreetionos.org/api/chat"


def _set_widget_margin(widget, margin):
    widget.set_margin_start(margin)
    widget.set_margin_end(margin)
    widget.set_margin_top(margin)
    widget.set_margin_bottom(margin)


def _load_theme():
    display = Gdk.Display.get_default()
    if display is None:
        display = Gdk.Display.open()
    if display is None:
        return
    provider = Gtk.CssProvider()
    # Removed custom CSS to use system GTK theme
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


def show_disclaimer(parent=None) -> bool:
    dlg = Gtk.Dialog(
        title='AIDEN – System Access Notice',
        parent=parent,
        flags=Gtk.DialogFlags.MODAL,
    )
    dlg.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT)
    dlg.set_default_size(560, 420)
    box = dlg.get_content_area()

    markup = Gtk.Label()
    markup.set_markup(
        '<b><span size="x-large">\u26a0  AIDEN – System Access Notice</span></b>\n\n'
        'AIDEN has been granted the ability to execute arbitrary code '
        'and commands on your system.\n\n'
        '\u2022 Code you ask AIDEN to run will be executed with YOUR user '
        'permissions (and with elevated privileges via polkit where authorized).\n'
        '\u2022 You are solely responsible for any commands, scripts, or operations '
        'AIDEN performs at your direction.\n'
        '\u2022 Review all commands before execution.\n'
        '\u2022 This is a tool — you are in control.\n\n'
        '<i>By accepting, you agree to take full responsibility for your use of AIDEN.</i>'
    )
    markup.set_line_wrap(True)
    _set_widget_margin(markup, 12)
    box.pack_start(markup, True, True, 0)

    credits_btn = Gtk.Button(label='Credits \u2192')
    def show_credits(_):
        cred_dlg = Gtk.Dialog(title='Credits', parent=dlg, flags=Gtk.DialogFlags.MODAL)
        cred_dlg.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        cred_box = cred_dlg.get_content_area()
        cred_label = Gtk.Label()
        cred_label.set_markup(
            '<b>AIDEN Desktop – AcreetionOS AI Assistant</b>\n\n'
            'Developed by Natalie Spiva (@sprungles) &amp; Darren Clift\n'
            'for the AcreetionOS Project\n\n'
            '<b>Powered by:</b>\n'
            '\u2022 OpenRouter API proxy\n'
            '\u2022 Python + PyGObject (GTK frontend)\n'
            '\u2022 Svelte + Tauri (Desktop webview)\n'
            '\u2022 Textual (Terminal UI)\n'
            '\u2022 cryptography (AES-GCM encrypted storage)\n'
            '\u2022 requests, httpx, FastAPI, uvicorn\n'
            '\u2022 marked, highlight.js\n\n'
            '<i>Built on open-source software. Licensed under GPL-3.0-or-later.</i>'
        )
        cred_label.set_line_wrap(True)
        _set_widget_margin(cred_label, 12)
        cred_box.pack_start(cred_label, True, True, 0)
        cred_dlg.show_all()
        cred_dlg.run()
        cred_dlg.destroy()
    credits_btn.connect('clicked', show_credits)

    btn_box = Gtk.Box(spacing=6)
    accept_btn = Gtk.Button(label='I Accept &amp; Understand')
    accept_btn.get_style_context().add_class('suggested-action')
    accept_btn.connect(
        'clicked',
        lambda b: (accept_disclaimer(), dlg.response(Gtk.ResponseType.ACCEPT))
    )
    btn_box.pack_end(accept_btn, False, False, 0)
    btn_box.pack_end(credits_btn, False, False, 0)
    _set_widget_margin(btn_box, 12)
    box.pack_start(btn_box, False, False, 0)

    dlg.show_all()
    resp = dlg.run()
    dlg.destroy()
    return resp == Gtk.ResponseType.ACCEPT


def show_credits_dialog(parent=None):
    dlg = Gtk.Dialog(title='Credits', parent=parent, flags=0)
    dlg.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
    box = dlg.get_content_area()
    label = Gtk.Label()
    label.set_markup(
        '<b>AIDEN Desktop – AcreetionOS AI Assistant</b>\n\n'
        'Developed by Natalie Spiva (@sprungles) &amp; Darren Clift\n'
        'for the AcreetionOS Project\n\n'
        '<b>Powered by:</b>\n'
        '\u2022 OpenRouter API proxy\n'
        '\u2022 Python + PyGObject (GTK frontend)\n'
        '\u2022 Svelte + Tauri (Desktop webview)\n'
        '\u2022 Textual (Terminal UI)\n'
        '\u2022 cryptography (AES-GCM encrypted storage)\n'
        '\u2022 requests, httpx, FastAPI, uvicorn\n'
        '\u2022 marked, highlight.js\n\n'
        '<i>Built on open-source software. Licensed under GPL-3.0-or-later.</i>'
    )
    label.set_line_wrap(True)
    _set_widget_margin(label, 12)
    box.pack_start(label, True, True, 0)
    dlg.show_all()
    dlg.run()
    dlg.destroy()


class AidenWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="AIDEN — AcreetionOS Assistant")
        self.set_default_size(720, 540)
        self.settings = load_settings()
        self.client = OpenRouterClient(self.settings.get('proxy_url', DEFAULT_PROXY))
        self._preset_keys = preset_keys()

        grid = Gtk.Grid(row_spacing=6, column_spacing=6, margin=12)
        self.add(grid)

        toolbar = Gtk.Box(spacing=6)
        self.preset_combo = Gtk.ComboBoxText()
        self._populate_presets()
        self.preset_combo.connect('changed', self.on_preset_changed)
        toolbar.pack_start(self.preset_combo, False, False, 0)

        help_btn = Gtk.Button(label='Credits')
        help_btn.connect('clicked', lambda b: show_credits_dialog(self))
        toolbar.pack_end(help_btn, False, False, 0)

        grid.attach(toolbar, 0, 0, 3, 1)

        self.chat_view = Gtk.TextView()
        self.chat_view.set_editable(False)
        self.chat_buf = self.chat_view.get_buffer()

        scroller = Gtk.ScrolledWindow()
        scroller.set_hexpand(True)
        scroller.set_vexpand(True)
        scroller.add(self.chat_view)

        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text('Ask AIDEN... (press Enter to send)')
        self.entry.connect('activate', self.on_send_clicked)

        send_btn = Gtk.Button(label='Send')
        send_btn.connect('clicked', self.on_send_clicked)

        pwd_label = Gtk.Label(label='Store password:')
        self.pwd = Gtk.Entry()
        self.pwd.set_visibility(False)

        settings_btn = Gtk.Button(label='Settings')
        settings_btn.connect('clicked', self.on_settings_clicked)

        grid.attach(scroller, 0, 1, 3, 1)
        grid.attach(self.entry, 0, 2, 2, 1)
        grid.attach(send_btn, 2, 2, 1, 1)
        grid.attach(pwd_label, 0, 3, 1, 1)
        grid.attach(self.pwd, 1, 3, 1, 1)
        grid.attach(settings_btn, 2, 3, 1, 1)

        self.show_all()

    def _populate_presets(self):
        self.preset_combo.remove_all()
        presets = get_presets()
        active = self.settings.get('active_preset', 'default')
        idx = 0
        for i, key in enumerate(self._preset_keys):
            name = presets.get(key, {}).get('name', key)
            self.preset_combo.append(key, name)
            if key == active:
                idx = i
        self.preset_combo.set_active(idx)

    def on_preset_changed(self, combo):
        key = combo.get_active_id()
        if key:
            set_active_preset(key)
            self.settings['active_preset'] = key
            self.append_text(f'[Switched to preset: {combo.get_active_text()}]')

    def append_text(self, text: str):
        end = self.chat_buf.get_end_iter()
        self.chat_buf.insert(end, text + '\n')

    def on_send_clicked(self, widget):
        text = self.entry.get_text().strip()
        if not text:
            return
        self.append_text('You: ' + text)
        self.entry.set_text('')
        password = self.pwd.get_text()
        self.settings = load_settings()
        self.client.proxy_url = self.settings.get('proxy_url', DEFAULT_PROXY)
        threading.Thread(target=self.handle_query, args=(text, password), daemon=True).start()

    def handle_query(self, text, password):
        snippets = []
        if password:
            try:
                snippets = search_snippets(
                    text, password,
                    max_chars=self.settings.get('snippet_max_chars', 800),
                    base=Path(self.settings.get('storage_dir'))
                )
            except Exception:
                snippets = []

        active_preset = get_active_preset()
        system_prompt = active_preset.get(
            'system_prompt',
            'You are AIDEN, AcreetionOS assistant. Be concise, accurate, and helpful.'
        )

        messages = []
        messages.append({'role': 'system', 'content': system_prompt})
        if snippets:
            messages.append({
                'role': 'system',
                'content': 'Local snippets:\n' + '\n'.join(snippets)
            })
        messages.append({'role': 'user', 'content': text})

        try:
            wl = self.settings.get('model_whitelist', []) or []
            if wl:
                available = self.client.models()
                if not available:
                    raise RuntimeError('Proxy returned no models; cannot enforce whitelist')
                if not any(m in available for m in wl):
                    raise RuntimeError(
                        f'No whitelisted models available on proxy. '
                        f'Available: {available}'
                    )

            resp = self.client.send_chat(messages)
            reply = (
                resp.get('reply')
                or resp.get('choices', [{}])[0]
                    .get('message', {})
                    .get('content')
                or str(resp)
            )
        except Exception as e:
            reply = f'Error contacting model: {e}'

        storage_dir = Path(self.settings.get('storage_dir'))
        if password:
            try:
                encrypt_and_store(
                    f'User: {text}\nAssistant: {reply}',
                    password,
                    base=storage_dir
                )
            except Exception:
                pass

        GLib.idle_add(self.append_text, 'AIDEN: ' + reply)

    def on_settings_clicked(self, widget):
        dlg = Gtk.Dialog(title='AIDEN Settings', parent=self, flags=0)
        dlg.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        dlg.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        box = dlg.get_content_area()

        notebook = Gtk.Notebook()
        box.pack_start(notebook, True, True, 0)

        general_grid = Gtk.Grid(row_spacing=6, column_spacing=6, margin=12)
        notebook.append_page(general_grid, Gtk.Label(label='General'))

        proxy_label = Gtk.Label(label='Proxy URL:')
        proxy_entry = Gtk.Entry()
        proxy_entry.set_text(self.settings.get('proxy_url', DEFAULT_PROXY))

        storage_label = Gtk.Label(label='Storage dir:')
        storage_entry = Gtk.Entry()
        storage_entry.set_text(
            self.settings.get(
                'storage_dir',
                str(Path.home() / '.local' / 'share' / 'aiden')
            )
        )

        helper_label = Gtk.Label(label='Helper path:')
        helper_entry = Gtk.Entry()
        helper_entry.set_text(
            self.settings.get('helper_path', '/usr/libexec/aiden-helper.py')
        )

        model_label = Gtk.Label(label='Model whitelist (comma):')
        model_entry = Gtk.Entry()
        model_entry.set_text(','.join(self.settings.get('model_whitelist', [])))

        test_btn = Gtk.Button(label='Test proxy')
        def on_test(_):
            ok = self.client.healthy()
            models = self.client.models()
            msg = 'Proxy OK' if ok else 'Proxy Unreachable'
            msg += f"\nModels: {', '.join(models) if models else 'none'}"
            dialog = Gtk.MessageDialog(
                parent=self, flags=0, type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK, message_format=msg
            )
            dialog.run()
            dialog.destroy()
        test_btn.connect('clicked', on_test)

        general_grid.attach(proxy_label, 0, 0, 1, 1)
        general_grid.attach(proxy_entry, 1, 0, 1, 1)
        general_grid.attach(storage_label, 0, 1, 1, 1)
        general_grid.attach(storage_entry, 1, 1, 1, 1)
        general_grid.attach(helper_label, 0, 2, 1, 1)
        general_grid.attach(helper_entry, 1, 2, 1, 1)
        general_grid.attach(model_label, 0, 3, 1, 1)
        general_grid.attach(model_entry, 1, 3, 1, 1)
        general_grid.attach(test_btn, 2, 3, 1, 1)

        preset_grid = Gtk.Grid(row_spacing=6, column_spacing=6, margin=12)
        notebook.append_page(preset_grid, Gtk.Label(label='Presets'))

        presets = get_presets()
        row = 0
        preset_entries = {}
        for key in self._preset_keys:
            p = presets.get(key, {})
            lbl = Gtk.Label(label=p.get('name', key) + ':')
            lbl.set_xalign(0)
            entry = Gtk.Entry()
            entry.set_text(p.get('system_prompt', ''))
            entry.set_width_chars(60)
            preset_grid.attach(lbl, 0, row, 1, 1)
            preset_grid.attach(entry, 1, row, 1, 1)
            preset_entries[key] = entry
            row += 1

        dlg.show_all()
        resp = dlg.run()
        if resp == Gtk.ResponseType.OK:
            new_settings = self.settings.copy()
            new_settings['proxy_url'] = proxy_entry.get_text().strip()
            new_settings['storage_dir'] = storage_entry.get_text().strip()
            new_settings['helper_path'] = helper_entry.get_text().strip()
            wl = [
                m.strip()
                for m in model_entry.get_text().split(',')
                if m.strip()
            ]
            new_settings['model_whitelist'] = wl
            save_settings(new_settings)
            self.settings = new_settings
            self.client.proxy_url = self.settings.get('proxy_url', DEFAULT_PROXY)

            for key, entry in preset_entries.items():
                updated = presets.get(key, {}).copy()
                updated['system_prompt'] = entry.get_text()
                save_preset(key, updated)

        dlg.destroy()

    def call_privileged(self, action: str, cmd: list = None):
        helper = self.settings.get('helper_path', '/usr/libexec/aiden-helper.py')
        args = ['pkexec', helper, '--action', action]
        if cmd:
            args += ['--cmd'] + cmd
        try:
            out = subprocess.check_output(args, stderr=subprocess.STDOUT)
            return out.decode('utf-8')
        except subprocess.CalledProcessError as e:
            return f'Privileged helper error: {e.output.decode("utf-8", errors="ignore")}'


def main():
    _load_theme()
    if not is_disclaimer_accepted():
        accepted = show_disclaimer()
        if not accepted:
            print('Disclaimer not accepted. Exiting.')
            return

    win = AidenWindow()
    win.connect('destroy', Gtk.main_quit)
    Gtk.main()


if __name__ == '__main__':
    main()

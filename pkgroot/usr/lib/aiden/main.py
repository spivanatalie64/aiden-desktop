#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import threading
import time

from aiden_storage import encrypt_and_store, list_conversations, search_snippets
from openrouter_client import OpenRouterClient
from settings import load_settings, save_settings
import subprocess
from pathlib import Path

DEFAULT_PROXY = "https://aiden.acreetionos.org/api/chat"  # change if you host your own proxy


class AidenWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="AIDEN — AcreetionOS Assistant")
        self.set_default_size(640, 480)

        self.settings = load_settings()
        self.client = OpenRouterClient(self.settings.get('proxy_url', DEFAULT_PROXY))


        grid = Gtk.Grid(row_spacing=6, column_spacing=6, margin=12)
        self.add(grid)

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

        grid.attach(scroller, 0, 0, 3, 1)
        grid.attach(self.entry, 0, 1, 2, 1)
        grid.attach(send_btn, 2, 1, 1, 1)
        grid.attach(pwd_label, 0, 2, 1, 1)
        grid.attach(self.pwd, 1, 2, 1, 1)
        grid.attach(settings_btn, 2, 2, 1, 1)

        self.show_all()

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
        # refresh client proxy in case settings changed
        self.settings = load_settings()
        self.client.proxy_url = self.settings.get('proxy_url', DEFAULT_PROXY)
        threading.Thread(target=self.handle_query, args=(text, password), daemon=True).start()

    def handle_query(self, text, password):
        # Read local encrypted snippets to keep context small
        snippets = []
        if password:
            try:
                snippets = search_snippets(text, password, max_chars=self.settings.get('snippet_max_chars', 800), base=Path(self.settings.get('storage_dir')))
            except Exception:
                snippets = []

        # Build minimal message list
        messages = []
        system_msg = {
            'role': 'system',
            'content': 'You are AIDEN, AcreetionOS assistant. Use only minimal context provided. If local snippets are provided, prefer them over prior chat history.'
        }
        messages.append(system_msg)
        if snippets:
            messages.append({'role': 'system', 'content': 'Local snippets:\n' + '\n'.join(snippets)})
        messages.append({'role': 'user', 'content': text})

        try:
            # If user configured a model whitelist, ensure at least one model is available on the proxy
            wl = self.settings.get('model_whitelist', []) or []
            if wl:
                available = self.client.models()
                if not available:
                    raise RuntimeError('Proxy returned no models; cannot enforce whitelist')
                # if none of whitelist in available, warn
                if not any(m in available for m in wl):
                    raise RuntimeError(f'No whitelisted models available on proxy. Available: {available}')

            resp = self.client.send_chat(messages)
            # Expect proxy to return {reply: '...'} or similar
            reply = resp.get('reply') or resp.get('choices', [{}])[0].get('message', {}).get('content') or str(resp)
        except Exception as e:
            reply = f'Error contacting model: {e}'

        # Store the user+assistant exchange locally encrypted to save as memory
        storage_dir = Path(self.settings.get('storage_dir'))
        if password:
            try:
                # Save combined exchange into a conversation for later reference
                encrypt_and_store(f'User: {text}\nAssistant: {reply}', password, base=storage_dir)
            except Exception:
                pass

        # Update UI on main thread
        GLib.idle_add(self.append_text, 'AIDEN: ' + reply)

    def on_settings_clicked(self, widget):
        dlg = Gtk.Dialog(title='AIDEN Settings', parent=self, flags=0)
        dlg.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        dlg.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        box = dlg.get_content_area()

        grid = Gtk.Grid(row_spacing=6, column_spacing=6, margin=12)
        box.add(grid)

        proxy_label = Gtk.Label(label='Proxy URL:')
        proxy_entry = Gtk.Entry()
        proxy_entry.set_text(self.settings.get('proxy_url', DEFAULT_PROXY))

        storage_label = Gtk.Label(label='Storage dir:')
        storage_entry = Gtk.Entry()
        storage_entry.set_text(self.settings.get('storage_dir', str(Path.home() / '.local' / 'share' / 'aiden')))

        helper_label = Gtk.Label(label='Helper path:')
        helper_entry = Gtk.Entry()
        helper_entry.set_text(self.settings.get('helper_path', '/usr/libexec/aiden-helper.py'))

        model_label = Gtk.Label(label='Model whitelist (comma):')
        model_entry = Gtk.Entry()
        model_entry.set_text(','.join(self.settings.get('model_whitelist', [])))

        test_btn = Gtk.Button(label='Test proxy')
        def on_test(_):
            client = self.client
            ok = client.healthy()
            models = client.models()
            msg = 'Proxy OK' if ok else 'Proxy Unreachable'
            msg += f"\nModels: {', '.join(models) if models else 'none'}"
            dialog = Gtk.MessageDialog(parent=self, flags=0, type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK, message_format=msg)
            dialog.run()
            dialog.destroy()
        test_btn.connect('clicked', on_test)

        grid.attach(proxy_label, 0, 0, 1, 1)
        grid.attach(proxy_entry, 1, 0, 1, 1)
        grid.attach(storage_label, 0, 1, 1, 1)
        grid.attach(storage_entry, 1, 1, 1, 1)
        grid.attach(helper_label, 0, 2, 1, 1)
        grid.attach(helper_entry, 1, 2, 1, 1)
        grid.attach(model_label, 0, 3, 1, 1)
        grid.attach(model_entry, 1, 3, 1, 1)
        grid.attach(test_btn, 2, 3, 1, 1)

        dlg.show_all()
        resp = dlg.run()
        if resp == Gtk.ResponseType.OK:
            new_settings = self.settings.copy()
            new_settings['proxy_url'] = proxy_entry.get_text().strip()
            new_settings['storage_dir'] = storage_entry.get_text().strip()
            new_settings['helper_path'] = helper_entry.get_text().strip()
            wl = [m.strip() for m in model_entry.get_text().split(',') if m.strip()]
            new_settings['model_whitelist'] = wl
            save_settings(new_settings)
            self.settings = new_settings
            self.client.proxy_url = self.settings.get('proxy_url', DEFAULT_PROXY)
        dlg.destroy()

    def call_privileged(self, action: str, cmd: list = None):
        # Scaffolding: call pkexec with helper path
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
    win = AidenWindow()
    win.connect('destroy', Gtk.main_quit)
    Gtk.main()


if __name__ == '__main__':
    main()

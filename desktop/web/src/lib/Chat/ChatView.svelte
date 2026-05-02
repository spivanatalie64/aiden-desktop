<script>
  import { onMount } from 'svelte';
  import { api, streamChat, getActivePreset, getPresets, setActivePreset } from '../api.js';

  let messages = [];
  let inputText = '';
  let presets = {};
  let presetKeys = [];
  let activePreset = 'default';
  let loading = false;
  let currentStream = null;

  onMount(async () => {
    try {
      const p = await getPresets();
      presets = p;
      presetKeys = Object.keys(p);

      const a = await getActivePreset();
      activePreset = a.key || 'default';
    } catch (e) {
      presets = { default: { name: 'Default' } };
      presetKeys = ['default'];
    }
  });

  function appendMessage(role, content) {
    messages = [...messages, { role, content }];
  }

  async function send() {
    if (!inputText.trim() || loading) return;

    const userMsg = inputText.trim();
    inputText = '';
    appendMessage('user', userMsg);
    loading = true;

    try {
      const resp = await fetch('http://127.0.0.1:9090/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [
            { role: 'system', content: (presets[activePreset]?.system_prompt) || '' },
            ...messages.slice(-10).map(m => ({ role: m.role, content: m.content })),
          ],
          stream: false,
        }),
      });
      const data = await resp.json();
      appendMessage('assistant', data.reply);
    } catch (e) {
      appendMessage('assistant', `Error: ${e.message}`);
    }
    loading = false;
  }

  async function updatePreset(e) {
    activePreset = e.target.value;
    await setActivePreset(activePreset);
  }
</script>

<div class="chat">
  <div class="top-bar">
    <select value={activePreset} on:change={updatePreset}>
      {#each presetKeys as key}
        <option value={key}>{presets[key]?.name || key}</option>
      {/each}
    </select>
  </div>

  <div class="messages" id="message-list">
    {#each messages as msg}
      <div class="msg {msg.role}">
        <div class="label">{msg.role === 'user' ? 'You' : 'AIDEN'}</div>
        <div class="content">{msg.content}</div>
      </div>
    {/each}
  </div>

  <div class="input-area">
    <textarea
      bind:value={inputText}
      placeholder="Ask AIDEN..."
      on:keydown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
      rows="2"
    ></textarea>
    <button class="btn-primary" on:click={send} disabled={loading}>
      {loading ? '...' : 'Send'}
    </button>
  </div>
</div>

<style>
  .chat { display: flex; flex-direction: column; height: 100%; }
  .top-bar {
    padding: 0.5rem 1rem;
    border-bottom: 1px solid var(--acreetion-box-border);
    background: var(--acreetion-panel-bg);
  }
  .top-bar select {
    background: var(--acreetion-box-bg);
    color: var(--acreetion-text-bright);
    border: 1px solid var(--acreetion-box-border);
    border-radius: 8px;
    padding: 0.3rem 0.5rem;
    font-size: 0.9rem;
  }
  .messages {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
  }
  .msg { margin-bottom: 1rem; max-width: 80%; }
  .msg.user { margin-left: auto; }
  .msg .label {
    font-size: 0.8rem;
    font-weight: 700;
    margin-bottom: 0.2rem;
  }
  .msg.user .label { color: var(--acreetion-green); text-align: right; }
  .msg.assistant .label { color: var(--storm-color); }
  .msg .content {
    line-height: 1.5;
    white-space: pre-wrap;
    word-wrap: break-word;
    background: var(--acreetion-box-bg);
    padding: 0.75rem;
    border-radius: var(--radius);
    border: 1px solid var(--acreetion-box-border);
  }
  .msg.user .content {
    background: rgba(46, 204, 113, 0.1);
    border-color: rgba(46, 204, 113, 0.3);
  }
  .input-area {
    display: flex;
    gap: 0.5rem;
    padding: 1rem;
    border-top: 1px solid var(--acreetion-box-border);
    background: var(--acreetion-panel-bg);
  }
  .input-area textarea {
    flex: 1;
    background: var(--acreetion-box-bg);
    border: 1px solid var(--acreetion-box-border);
    border-radius: 8px;
    color: var(--acreetion-text-bright);
    padding: 0.5rem;
    font-family: var(--font-sans);
    resize: none;
  }
  .input-area textarea:focus { outline: none; border-color: var(--acreetion-green); }
</style>

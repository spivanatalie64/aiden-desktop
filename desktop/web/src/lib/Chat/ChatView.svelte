<script>
  import { onMount } from 'svelte';
  import { getActivePreset, setActivePreset, getPresets, streamChat } from '../api.js';

  let messages = [];
  let inputText = '';
  let presets = [];
  let activePreset = 'default';
  let loading = false;

  onMount(async () => {
    presets = await getPresets();
    const active = await getActivePreset();
    activePreset = active.key;
  });

  async function send() {
    if (!inputText.trim() || loading) return;
    messages.push({ role: 'user', content: inputText });
    inputText = '';
    loading = true;

    streamChat(messages, (token) => {
      if (!messages.length || messages[messages.length - 1].role !== 'assistant') {
        messages.push({ role: 'assistant', content: '' });
      }
      messages[messages.length - 1].content += token;
      messages = messages;
    });
    loading = false;
  }
</script>

<div class="chat">
  <div class="preset-bar">
    <select bind:value={activePreset} on:change={() => setActivePreset(activePreset)}>
      {#each Object.entries(presets) as [key, preset]}
        <option value={key}>{preset.name}</option>
      {/each}
    </select>
  </div>

  <div class="messages">
    {#each messages as msg}
      <div class="message {msg.role}">
        <div class="label">{msg.role === 'user' ? 'You' : 'AIDEN'}</div>
        <div class="content">{msg.content}</div>
      </div>
    {/each}
  </div>

  <div class="input-bar">
    <input
      type="text"
      bind:value={inputText}
      placeholder="Ask AIDEN..."
      on:keydown={(e) => e.key === 'Enter' && send()}
    />
    <button class="btn-primary" on:click={send} disabled={loading}>
      {loading ? '...' : 'Send'}
    </button>
  </div>
</div>

<style>
  .chat { display: flex; flex-direction: column; height: 100%; }
  .preset-bar { padding: 0.75rem 1rem; border-bottom: 1px solid var(--acreetion-box-border); }
  .preset-bar select {
    background: var(--acreetion-box-bg);
    color: var(--acreetion-text-bright);
    border: 1px solid var(--acreetion-box-border);
    border-radius: 8px; padding: 0.3rem 0.5rem;
  }
  .messages { flex: 1; overflow-y: auto; padding: 1rem; }
  .message { margin-bottom: 1rem; }
  .message .label { font-weight: 700; font-size: 0.85rem; margin-bottom: 0.25rem; }
  .message.user .label { color: var(--acreetion-green); }
  .message.assistant .label { color: var(--storm-color); }
  .message .content { line-height: 1.5; white-space: pre-wrap; }
  .input-bar {
    display: flex; gap: 0.5rem; padding: 1rem;
    border-top: 1px solid var(--acreetion-box-border);
  }
  .input-bar input { flex: 1; }
</style>

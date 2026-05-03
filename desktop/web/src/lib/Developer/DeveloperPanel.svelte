<script>
  import { onMount } from 'svelte';
  import { api } from '../api.js';

  let providers = [];
  let newName = '';
  let newUrl = '';
  let newKey = '';

  let temperature = 0.7;
  let maxTokens = 4096;
  let reasoningEffort = 'auto';
  let execMode = 'click_to_run';
  let execTimeout = 30;
  let testResult = '';

  onMount(async () => {
    try {
      const p = await api('/settings/providers');
      providers = p.providers || [];
    } catch (e) { /* ignore */ }
  });

  async function addProvider() {
    if (!newName || !newUrl) return;
    await api('/settings/providers', {
      method: 'POST',
      body: JSON.stringify({ name: newName, base_url: newUrl, api_key: newKey }),
    });
    const p = await api('/settings/providers');
    providers = p.providers || [];
    newName = ''; newUrl = ''; newKey = '';
  }

  async function removeProvider(name) {
    await api(`/settings/providers/${encodeURIComponent(name)}`, { method: 'DELETE' });
    const p = await api('/settings/providers');
    providers = p.providers || [];
  }

  async function saveParams() {
    await api('/settings', {
      method: 'PUT',
      body: JSON.stringify({
        temperature: parseFloat(temperature),
        max_tokens: parseInt(maxTokens),
        reasoning_effort: reasoningEffort,
        code_exec_mode: execMode,
        code_exec_timeout: parseInt(execTimeout),
      }),
    });
  }

  async function testProxy() {
    try {
      const resp = await fetch('http://127.0.0.1:9090/health');
      const data = await resp.json();
      testResult = `Backend: ${data.status} (v${data.version})`;
    } catch (e) {
      testResult = `Error: ${e.message}`;
    }
  }
</script>

<div class="developer">
  <h2>Developer Menu</h2>

  <section class="card">
    <h3>API Providers</h3>
    <div class="add-provider">
      <input bind:value={newName} placeholder="Name (e.g. OpenAI)" />
      <input bind:value={newUrl} placeholder="Base URL" />
      <input bind:value={newKey} placeholder="API Key (optional)" type="password" />
      <button class="btn-primary" on:click={addProvider}>Add</button>
    </div>
    <div class="provider-list">
      {#each providers as p}
        <div class="provider-item">
          <span><strong>{p.name}</strong> – {p.base_url}</span>
          <button class="btn-secondary" on:click={() => removeProvider(p.name)}>✕</button>
        </div>
      {/each}
    </div>
  </section>

  <section class="card">
    <h3>Model Parameters</h3>
    <label>Temperature: <input type="number" bind:value={temperature} min="0" max="2" step="0.1" /></label>
    <label>Max Tokens: <input type="number" bind:value={maxTokens} min="1" /></label>
    <label>Reasoning Effort: <select bind:value={reasoningEffort}>
      <option value="auto">Auto</option>
      <option value="low">Low</option>
      <option value="medium">Medium</option>
      <option value="high">High</option>
    </select></label>
    <button class="btn-primary" on:click={saveParams}>Save Params</button>
  </section>

  <section class="card">
    <h3>Code Execution</h3>
    <label>Mode:
      <select bind:value={execMode}>
        <option value="click_to_run">Click to run (safest)</option>
        <option value="trust_conversation">Trust per conversation</option>
        <option value="auto_run_safe">Auto-run safe languages</option>
        <option value="auto_run_all">Auto-run all</option>
      </select>
    </label>
    <label>Timeout (s): <input type="number" bind:value={execTimeout} min="5" max="300" /></label>
    <button class="btn-primary" on:click={saveParams}>Save</button>
  </section>

  <section class="card">
    <h3>Debug</h3>
    <button class="btn-secondary" on:click={testProxy}>Test Proxy Health</button>
    {#if testResult}
      <p class="result">{testResult}</p>
    {/if}
  </section>
</div>

<style>
  .developer { padding: 1.5rem; overflow-y: auto; height: 100%; }
  h2 { margin-bottom: 1rem; font-family: var(--font-mono); }
  h3 { margin-bottom: 0.5rem; color: var(--acreetion-green); }
  .card {
    background: var(--acreetion-box-bg);
    border: 1px solid var(--acreetion-box-border);
    border-radius: var(--radius);
    padding: 1rem;
    margin-bottom: 1rem;
  }
  .add-provider { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.75rem; }
  .add-provider input { flex: 1; min-width: 120px; }
  .provider-list { max-height: 200px; overflow-y: auto; }
  .provider-item {
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.3rem 0; border-bottom: 1px solid var(--acreetion-box-border);
  }
  label { display: block; margin-bottom: 0.5rem; font-size: 0.9rem; }
  label input, label select { margin-left: 0.5rem; }
  .result { margin-top: 0.5rem; color: var(--acreetion-green); }
</style>

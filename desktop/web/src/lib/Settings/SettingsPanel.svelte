<script>
  import { onMount } from 'svelte';
  import { api } from '../api.js';
  import { getPresets, getActivePreset, setActivePreset } from '../api.js';

  let proxyUrl = '';
  let storageDir = '';
  let helperPath = '';
  let temperature = 0.7;
  let presets = {};
  let presetKeysArr = [];
  let activePresetKey = 'default';
  let presetsData = {};

  onMount(async () => {
    try {
      const s = await api('/settings');
      proxyUrl = s.proxy_url || '';
      storageDir = s.storage_dir || '';
      helperPath = s.helper_path || '';
      temperature = s.temperature || 0.7;

      const p = await api('/settings/presets');
      presetsData = p;
      presetKeysArr = Object.keys(p);
    } catch (e) { /* ignore */ }
  });

  async function saveGeneral() {
    await api('/settings', {
      method: 'PUT',
      body: JSON.stringify({
        proxy_url: proxyUrl,
        storage_dir: storageDir,
        helper_path: helperPath,
        temperature: parseFloat(temperature),
      }),
    });
  }

  async function savePreset(key) {
    const inp = document.getElementById(`preset-${key}`);
    if (inp) {
      const updated = { ...presetsData[key], system_prompt: inp.value };
      await api(`/settings/presets/${key}`, {
        method: 'PUT',
        body: JSON.stringify(updated),
      });
    }
  }
</script>

<div class="settings">
  <h2>Settings</h2>

  <section class="card">
    <h3>General</h3>
    <label>Proxy URL: <input bind:value={proxyUrl} /></label>
    <label>Storage dir: <input bind:value={storageDir} /></label>
    <label>Helper path: <input bind:value={helperPath} /></label>
    <label>Temperature: <input type="number" bind:value={temperature} min="0" max="2" step="0.1" /></label>
    <button class="btn-primary" on:click={saveGeneral}>Save</button>
  </section>

  <section class="card">
    <h3>Presets</h3>
    {#each presetKeysArr as key}
      <div class="preset">
        <strong>{presetsData[key]?.name || key}</strong>
        <textarea id="preset-{key}" rows="3">{presetsData[key]?.system_prompt || ''}</textarea>
        <button class="btn-secondary" on:click={() => savePreset(key)}>Save</button>
      </div>
    {/each}
  </section>
</div>

<style>
  .settings { padding: 1.5rem; overflow-y: auto; height: 100%; }
  h2 { margin-bottom: 1rem; font-family: var(--font-mono); }
  h3 { margin-bottom: 0.5rem; color: var(--acreetion-green); }
  .card {
    background: var(--acreetion-box-bg);
    border: 1px solid var(--acreetion-box-border);
    border-radius: var(--radius);
    padding: 1rem;
    margin-bottom: 1rem;
  }
  label { display: block; margin-bottom: 0.75rem; font-size: 0.9rem; }
  label input { margin-left: 0.5rem; width: 300px; max-width: 100%; }
  .preset { margin-bottom: 1rem; padding-bottom: 1rem; border-bottom: 1px solid var(--acreetion-box-border); }
  .preset textarea {
    display: block;
    width: 100%;
    margin: 0.5rem 0;
    background: var(--acreetion-body-bg);
    border: 1px solid var(--acreetion-box-border);
    border-radius: 8px;
    color: var(--acreetion-text-bright);
    padding: 0.5rem;
    font-family: var(--font-mono);
    font-size: 0.85rem;
  }
</style>

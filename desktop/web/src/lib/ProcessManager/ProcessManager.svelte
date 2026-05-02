<script>
  import { onMount } from 'svelte';
  import { api } from '../api.js';

  let services = [];
  let systemInfo = {};
  let code = '';
  let language = 'python';
  let output = '';
  let loading = false;

  onMount(async () => {
    try {
      const s = await api('/processes/info');
      systemInfo = s;
    } catch (e) { /* ignore */ }
    try {
      const s = await api('/processes/services');
      services = s.services || [];
    } catch (e) { /* ignore */ }
  });

  async function serviceAction(name, action) {
    await api(`/processes/services/${action}`, {
      method: 'POST',
      body: JSON.stringify({ name, action }),
    });
    const s = await api('/processes/services');
    services = s.services || [];
  }

  async function runCode() {
    if (!code.trim()) return;
    loading = true;
    try {
      const result = await fetch('http://127.0.0.1:9090/processes/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, language, timeout: 30 }),
      });
      const data = await result.json();
      output = data.stdout || data.stderr || '(no output)';
      if (data.exit_code !== 0) {
        output = `Exit code: ${data.exit_code}\n${output}`;
      }
    } catch (e) {
      output = `Error: ${e.message}`;
    }
    loading = false;
  }
</script>

<div class="processes">
  <h2>Process Manager</h2>

  <section class="card">
    <h3>System Resources</h3>
    <div class="resources">
      {#if systemInfo.cpu}
        <div class="stat"><span class="label">CPU:</span> {systemInfo.cpu.percent}% ({systemInfo.cpu.cores} cores)</div>
        <div class="stat"><span class="label">RAM:</span> {systemInfo.memory.percent}% ({(systemInfo.memory.used / 1e9).toFixed(1)}GB / {(systemInfo.memory.total / 1e9).toFixed(1)}GB)</div>
        <div class="stat"><span class="label">Disk:</span> {systemInfo.disk.percent}% ({(systemInfo.disk.used / 1e9).toFixed(1)}GB / {(systemInfo.disk.total / 1e9).toFixed(1)}GB)</div>
      {:else}
        <p class="dim">Install psutil for resource monitoring</p>
      {/if}
    </div>
  </section>

  <section class="card">
    <h3>Quick Execute (Sandboxed)</h3>
    <div class="exec-bar">
      <select bind:value={language}>
        <option value="python">Python</option>
        <option value="bash">Bash</option>
        <option value="javascript">JavaScript</option>
        <option value="ruby">Ruby</option>
        <option value="lua">Lua</option>
      </select>
      <textarea bind:value={code} placeholder="Enter code..." rows="3"></textarea>
      <button class="btn-primary" on:click={runCode} disabled={loading}>
        {loading ? 'Running...' : '▶ Run'}
      </button>
    </div>
    {#if output}
      <pre class="output">{output}</pre>
    {/if}
  </section>

  <section class="card">
    <h3>Services</h3>
    <div class="service-list">
      {#each services as svc}
        <div class="service">
          <span class="svc-name">{svc.name}</span>
          <span class="svc-status" class:active={svc.active === 'active'} class:inactive={svc.active !== 'active'}>
            {svc.sub}
          </span>
          <div class="svc-actions">
            <button class="btn-secondary small" on:click={() => serviceAction(svc.name, 'restart')}>↻</button>
            <button class="btn-secondary small" on:click={() => serviceAction(svc.name, svc.active === 'active' ? 'stop' : 'start')}>
              {svc.active === 'active' ? '■' : '▶'}
            </button>
          </div>
        </div>
      {/each}
    </div>
  </section>
</div>

<style>
  .processes { padding: 1.5rem; overflow-y: auto; height: 100%; }
  h2 { margin-bottom: 1rem; font-family: var(--font-mono); }
  h3 { margin-bottom: 0.5rem; color: var(--acreetion-green); }
  .dim { color: var(--acreetion-text); font-style: italic; }
  .card {
    background: var(--acreetion-box-bg);
    border: 1px solid var(--acreetion-box-border);
    border-radius: var(--radius);
    padding: 1rem;
    margin-bottom: 1rem;
  }
  .resources { display: flex; gap: 1.5rem; flex-wrap: wrap; }
  .stat .label { color: var(--acreetion-text); }
  .exec-bar { display: flex; flex-direction: column; gap: 0.5rem; }
  .exec-bar textarea {
    background: var(--acreetion-body-bg);
    border: 1px solid var(--acreetion-box-border);
    border-radius: 8px;
    color: var(--acreetion-text-bright);
    padding: 0.5rem;
    font-family: var(--font-mono);
    font-size: 0.85rem;
  }
  .exec-bar select {
    background: var(--acreetion-box-bg);
    color: var(--acreetion-text-bright);
    border: 1px solid var(--acreetion-box-border);
    border-radius: 8px;
    padding: 0.3rem;
    width: fit-content;
  }
  .output {
    background: var(--acreetion-body-bg);
    border: 1px solid var(--acreetion-box-border);
    border-radius: 8px;
    padding: 0.75rem;
    margin-top: 0.5rem;
    font-family: var(--font-mono);
    font-size: 0.85rem;
    white-space: pre-wrap;
    max-height: 300px;
    overflow-y: auto;
  }
  .service { display: flex; align-items: center; gap: 0.75rem; padding: 0.3rem 0; }
  .svc-name { flex: 1; font-size: 0.9rem; font-family: var(--font-mono); }
  .svc-status { font-size: 0.8rem; padding: 0.15rem 0.5rem; border-radius: 4px; }
  .svc-status.active { color: var(--acreetion-green); }
  .svc-status.inactive { color: var(--acreetion-text); }
  .small { padding: 0.2rem 0.5rem; font-size: 0.8rem; }
</style>

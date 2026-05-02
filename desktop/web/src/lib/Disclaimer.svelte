<script>
  import { createEventDispatcher } from 'svelte';
  import { acceptDisclaimer } from '../api.js';
  const dispatch = createEventDispatcher();

  let showCredits = false;

  async function handleAccept() {
    await acceptDisclaimer();
    dispatch('accept');
  }
</script>

<div class="overlay">
  <div class="dialog">
    <h1>⚠ AIDEN – System Access Notice</h1>
    <div class="body">
      <p>AIDEN has been granted the ability to execute arbitrary code and commands on your system.</p>
      <ul>
        <li>Code you ask AIDEN to run will be executed with <strong>YOUR</strong> user permissions (and with elevated privileges via polkit where authorized).</li>
        <li>You are <strong>solely responsible</strong> for any commands, scripts, or operations AIDEN performs at your direction.</li>
        <li>Review all commands before execution.</li>
        <li>This is a tool — you are in control.</li>
      </ul>
      <p class="italic">By accepting, you agree to take full responsibility for your use of AIDEN.</p>
    </div>
    <div class="actions">
      <button class="btn-primary" on:click={handleAccept}>I Accept & Understand</button>
      <button class="btn-secondary" on:click={() => showCredits = true}>Credits →</button>
      <button class="btn-secondary" on:click={() => window.close()}>Decline</button>
    </div>
  </div>
</div>

{#if showCredits}
  <div class="overlay" on:click={() => showCredits = false}>
    <div class="dialog small" on:click|stopPropagation>
      <h2>Credits</h2>
      <div class="body">
        <p><strong>AIDEN Desktop – AcreetionOS AI Assistant</strong></p>
        <p>Developed by Natalie Spiva (@sprungles) & Darren Clift<br>for the AcreetionOS Project</p>
        <p class="section"><strong>Powered by:</strong></p>
        <ul>
          <li>OpenRouter API proxy</li>
          <li>Python + PyGObject (GTK frontend)</li>
          <li>Svelte + Tauri (Desktop webview)</li>
          <li>Textual (Terminal UI)</li>
          <li>cryptography (AES-GCM encrypted storage)</li>
          <li>requests, httpx, FastAPI, uvicorn</li>
          <li>marked, highlight.js</li>
        </ul>
        <p class="italic">Built on open-source software. Licensed under GPL-3.0-or-later.</p>
      </div>
      <button class="btn-secondary" on:click={() => showCredits = false}>Close</button>
    </div>
  </div>
{/if}

<style>
  .overlay {
    position: fixed; inset: 0;
    background: rgba(0,0,0,0.8);
    display: flex; align-items: center; justify-content: center;
    z-index: 9999;
  }
  .dialog {
    background: var(--acreetion-box-bg);
    border: 1px solid var(--acreetion-box-border);
    border-radius: var(--radius);
    padding: 2rem;
    max-width: 560px;
    width: 90%;
  }
  .dialog.small { max-width: 480px; }
  h1 { font-size: 1.3rem; margin-bottom: 1rem; color: #e74c3c; }
  h2 { font-size: 1.1rem; margin-bottom: 1rem; }
  .body { margin-bottom: 1.5rem; line-height: 1.6; }
  .body p { margin-bottom: 0.75rem; }
  .body ul { padding-left: 1.25rem; margin-bottom: 0.75rem; }
  .body li { margin-bottom: 0.5rem; color: var(--acreetion-text); }
  .italic { font-style: italic; }
  .section { margin-top: 1rem; }
  .actions { display: flex; gap: 0.5rem; flex-wrap: wrap; }
</style>

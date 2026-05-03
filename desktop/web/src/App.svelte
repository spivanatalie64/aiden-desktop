<script>
  import { onMount } from 'svelte';
  import './lib/theme.css';
  import Disclaimer from './lib/Disclaimer.svelte';
  import ChatView from './lib/Chat/ChatView.svelte';
  import Sidebar from './lib/History/Sidebar.svelte';
  import SettingsPanel from './lib/Settings/SettingsPanel.svelte';
  import DeveloperPanel from './lib/Developer/DeveloperPanel.svelte';
  import ProcessManager from './lib/ProcessManager/ProcessManager.svelte';
  import MeshPanel from './lib/Mesh/MeshPanel.svelte';
  import { api, checkDisclaimer } from './lib/api.js';

  let disclaimerAccepted = false;
  let currentView = 'chat';

  onMount(async () => {
    try {
      const resp = await checkDisclaimer();
      disclaimerAccepted = resp.accepted;
    } catch (e) {
      disclaimerAccepted = true;
    }
  });

  function handleNavigate(e) {
    currentView = e.detail;
  }
</script>

<main class="app">
  {#if !disclaimerAccepted}
    <Disclaimer on:accept={() => disclaimerAccepted = true} />
  {:else}
    <Sidebar {currentView} on:navigate={handleNavigate} />
    <div class="main-area">
      {#if currentView === 'chat'}
        <ChatView />
      {:else if currentView === 'history'}
        <p style="padding: 2rem; color: var(--acreetion-text);">History view will display encrypted conversations.</p>
      {:else if currentView === 'settings'}
        <SettingsPanel />
      {:else if currentView === 'developer'}
        <DeveloperPanel />
      {:else if currentView === 'processes'}
        <ProcessManager />
      {:else if currentView === 'mesh'}
        <MeshPanel />
      {:else}
        <ChatView />
      {/if}
    </div>
  {/if}
</main>

<style>
  .app {
    display: flex;
    height: 100vh;
    background: var(--acreetion-body-bg);
    color: var(--acreetion-text-bright);
  }
  .main-area {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
  }
</style>

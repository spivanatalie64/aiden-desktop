<script>
  import { onMount } from 'svelte';
  import '../lib/theme.css';
  import Disclaimer from '../lib/Disclaimer.svelte';
  import ChatView from '../lib/Chat/ChatView.svelte';
  import Sidebar from '../lib/History/Sidebar.svelte';
  import SettingsPanel from '../lib/Settings/SettingsPanel.svelte';
  import ProcessManager from '../lib/ProcessManager/ProcessManager.svelte';
  import { checkDisclaimer } from '../lib/api.js';

  let disclaimerAccepted = false;
  let currentView = 'chat';
  let settings = {};

  onMount(async () => {
    const resp = await checkDisclaimer();
    disclaimerAccepted = resp.accepted;
  });
</script>

<main class="app">
  {#if !disclaimerAccepted}
    <Disclaimer on:accept={() => disclaimerAccepted = true} />
  {:else}
    <Sidebar {currentView} on:navigate={(e) => currentView = e.detail} />
    <div class="main-area">
      {#if currentView === 'chat'}
        <ChatView />
      {:else if currentView === 'settings'}
        <SettingsPanel bind:settings />
      {:else if currentView === 'processes'}
        <ProcessManager />
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
  }
</style>

<script>
  export let currentView = 'chat';
  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();
</script>

<aside class="sidebar">
  <div class="logo">AIDEN</div>
  <nav>
    <button class:active={currentView === 'chat'} on:click={() => dispatch('navigate', 'chat')}>
      💬 Chat
    </button>
    <button class:active={currentView === 'settings'} on:click={() => dispatch('navigate', 'settings')}>
      ⚙ Settings
    </button>
    <button class:active={currentView === 'processes'} on:click={() => dispatch('navigate', 'processes')}>
      🔧 Processes
    </button>
  </nav>
  <div class="spacer"></div>
  <div class="new-chat">
    <button class="btn-primary" on:click={() => dispatch('navigate', 'chat')}>+ New Chat</button>
  </div>
</aside>

<style>
  .sidebar {
    width: 240px;
    background: var(--acreetion-panel-bg);
    border-right: 2px solid var(--acreetion-green);
    display: flex;
    flex-direction: column;
    padding: 1rem;
  }
  .logo {
    font-family: var(--font-mono);
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--acreetion-green);
    margin-bottom: 2rem;
    text-align: center;
  }
  nav { display: flex; flex-direction: column; gap: 0.25rem; }
  nav button {
    text-align: left;
    padding: 0.6rem 0.75rem;
    background: transparent;
    color: var(--acreetion-text);
    border-radius: 8px;
  }
  nav button:hover { background: var(--acreetion-box-bg); color: var(--acreetion-text-bright); }
  nav button.active { background: var(--acreetion-green); color: #000; font-weight: 700; }
  .spacer { flex: 1; }
  .new-chat { margin-top: 1rem; }
  .new-chat button { width: 100%; }
</style>

<script>
  import { createEventDispatcher } from 'svelte';

  export let currentView = 'chat';
  const dispatch = createEventDispatcher();
</script>

<aside class="sidebar">
  <div class="logo">AIDEN</div>
  <nav>
    <button class:active={currentView === 'chat'} on:click={() => dispatch('navigate', 'chat')}>
      <span class="icon">💬</span> Chat
    </button>
    <button class:active={currentView === 'history'} on:click={() => dispatch('navigate', 'history')}>
      <span class="icon">📋</span> History
    </button>
    <button class:active={currentView === 'processes'} on:click={() => dispatch('navigate', 'processes')}>
      <span class="icon">🔧</span> Processes
    </button>
    <button class:active={currentView === 'mesh'} on:click={() => dispatch('navigate', 'mesh')}>
      <span class="icon">🌐</span> Mesh
    </button>
    <button class:active={currentView === 'settings'} on:click={() => dispatch('navigate', 'settings')}>
      <span class="icon">⚙</span> Settings
    </button>
    <button class:active={currentView === 'developer'} on:click={() => dispatch('navigate', 'developer')}>
      <span class="icon">🛠</span> Developer
    </button>
  </nav>
  <div class="spacer"></div>
  <button class="new-chat" on:click={() => dispatch('navigate', 'chat')}>
    + New Chat
  </button>
</aside>

<style>
  .sidebar {
    width: 200px;
    background: var(--acreetion-panel-bg);
    border-right: 2px solid var(--acreetion-green);
    display: flex;
    flex-direction: column;
    padding: 0.75rem;
  }
  .logo {
    font-family: var(--font-mono);
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--acreetion-green);
    margin-bottom: 1.5rem;
    text-align: center;
  }
  nav { display: flex; flex-direction: column; gap: 0.15rem; }
  nav button {
    text-align: left;
    padding: 0.5rem 0.75rem;
    background: transparent;
    color: var(--acreetion-text);
    border-radius: 8px;
    font-size: 0.9rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }
  nav button:hover { background: var(--acreetion-box-bg); color: var(--acreetion-text-bright); }
  nav button.active { background: var(--acreetion-green); color: #000; font-weight: 600; }
  .icon { font-size: 1rem; }
  .spacer { flex: 1; }
  .new-chat {
    background: var(--acreetion-green);
    color: #000;
    font-weight: 700;
    border-radius: 8px;
    padding: 0.5rem;
    margin-top: 0.5rem;
  }
</style>

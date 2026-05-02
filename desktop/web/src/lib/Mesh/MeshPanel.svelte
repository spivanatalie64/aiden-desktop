<script>
  import { onMount } from 'svelte';
  import { api } from '../api.js';

  let peers = [];
  let cacheStatus = { entries: 0 };
  let meshEnabled = false;
  let loading = true;

  onMount(async () => {
    try {
      const s = await api('/settings');
      meshEnabled = s.mesh_enabled || false;

      if (meshEnabled) {
        const p = await api('/mesh/peers');
        peers = p.peers || [];
        const c = await api('/mesh/cache/status');
        cacheStatus = c;
      }
    } catch (e) { /* ignore */ }
    loading = false;
  });

  async function acceptPeer(fingerprint) {
    await api('/mesh/peers/accept', {
      method: 'POST',
      body: JSON.stringify({ fingerprint }),
    });
    const p = await api('/mesh/peers');
    peers = p.peers || [];
  }

  async function rejectPeer(fingerprint) {
    await api('/mesh/peers/reject', {
      method: 'POST',
      body: JSON.stringify({ fingerprint }),
    });
    const p = await api('/mesh/peers');
    peers = p.peers || [];
  }

  async function toggleMesh() {
    await api('/settings', {
      method: 'PUT',
      body: JSON.stringify({ mesh_enabled: !meshEnabled }),
    });
    meshEnabled = !meshEnabled;
    if (meshEnabled) {
      const p = await api('/mesh/peers');
      peers = p.peers || [];
    }
  }
</script>

<div class="mesh">
  <div class="header">
    <h2>LAN Mesh</h2>
    <label class="toggle">
      <input type="checkbox" checked={meshEnabled} on:change={toggleMesh} />
      Enabled
    </label>
  </div>

  {#if loading}
    <p>Loading...</p>
  {:else if !meshEnabled}
    <p class="dim">Enable LAN mesh to discover peers on your network.</p>
  {:else}
    <section class="card">
      <h3>Cache</h3>
      <p>{cacheStatus.entries} cached response{cacheStatus.entries !== 1 ? 's' : ''}</p>
    </section>

    <section class="card">
      <h3>Peers ({peers.length})</h3>
      {#if peers.length === 0}
        <p class="dim">Scanning for peers via mDNS...</p>
      {/if}
      {#each peers as peer}
        <div class="peer">
          <div class="peer-info">
            <strong>{peer.hostname}</strong>
            <span class="fingerprint">{peer.fingerprint}</span>
          </div>
          <div class="peer-actions">
            <span class="status" class:accepted={peer.accepted}>
              {peer.accepted ? '✓ Accepted' : 'Pending'}
            </span>
            {#if !peer.accepted}
              <button class="btn-primary small" on:click={() => acceptPeer(peer.fingerprint)}>Accept</button>
              <button class="btn-secondary small" on:click={() => rejectPeer(peer.fingerprint)}>Reject</button>
            {/if}
          </div>
        </div>
      {/each}
    </section>
  {/if}
</div>

<style>
  .mesh { padding: 1.5rem; }
  .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
  h2 { font-family: var(--font-mono); }
  h3 { margin-bottom: 0.5rem; color: var(--acreetion-green); }
  .toggle { font-size: 0.9rem; }
  .toggle input { margin-right: 0.3rem; }
  .dim { color: var(--acreetion-text); font-style: italic; }
  .card {
    background: var(--acreetion-box-bg);
    border: 1px solid var(--acreetion-box-border);
    border-radius: var(--radius);
    padding: 1rem;
    margin-bottom: 1rem;
  }
  .peer {
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.5rem 0; border-bottom: 1px solid var(--acreetion-box-border);
  }
  .peer-info { display: flex; flex-direction: column; }
  .fingerprint { font-size: 0.8rem; color: var(--acreetion-text); font-family: var(--font-mono); }
  .peer-actions { display: flex; gap: 0.4rem; align-items: center; }
  .status { font-size: 0.85rem; }
  .status.accepted { color: var(--acreetion-green); }
  .small { padding: 0.25rem 0.5rem; font-size: 0.8rem; }
</style>

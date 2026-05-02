const API_BASE = 'http://127.0.0.1:9090';

export async function api(path, options = {}) {
  const resp = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!resp.ok) {
    throw new Error(`API error: ${resp.status} ${resp.statusText}`);
  }
  return resp.json();
}

export async function checkDisclaimer() {
  return api('/settings/disclaimer');
}

export async function acceptDisclaimer() {
  return api('/settings/disclaimer', { method: 'POST' });
}

export async function getPresets() {
  return api('/settings/presets');
}

export async function getActivePreset() {
  return api('/settings/presets/active');
}

export async function setActivePreset(key) {
  return api('/settings/presets/active', {
    method: 'PUT',
    body: JSON.stringify({ key }),
  });
}

export async function sendMessage(messages, options = {}) {
  return api('/chat', {
    method: 'POST',
    body: JSON.stringify({ messages, ...options }),
  });
}

export function streamChat(messages, onToken, options = {}) {
  const params = new URLSearchParams({
    messages: JSON.stringify(messages),
    ...options,
  });
  const es = new EventSource(`${API_BASE}/chat/stream?${params}`);
  es.onmessage = (event) => {
    if (event.data === '[DONE]') {
      es.close();
      return;
    }
    onToken(JSON.parse(event.data));
  };
  es.onerror = () => es.close();
  return es;
}

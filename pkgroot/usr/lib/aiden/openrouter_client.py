import requests
import time
from typing import List, Dict, Optional

# This client talks to a proxy endpoint that in turn talks to OpenRouter.
# We intentionally avoid embedding provider API keys here. Configure proxy_url.


class OpenRouterClient:
    def __init__(self, proxy_url: str = "https://aiden.acreetionos.org/api/chat", timeout: int = 30):
        self.proxy_url = proxy_url
        self.timeout = timeout

    def send_chat(self, messages: List[Dict], model: Optional[str] = None) -> Dict:
        """POST messages to the proxy. The proxy is responsible for selecting a free OpenRouter backend.
        Payload: {messages: [...], model: optional}
        """
        payload = {"messages": messages}
        if model:
            payload['model'] = model
        resp = requests.post(self.proxy_url, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def healthy(self) -> bool:
        try:
            r = requests.get(self.proxy_url, timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def models(self) -> List[str]:
        """Attempt to fetch a list of available models from the proxy.
        Tries common endpoints: GET {proxy_url}/models or GET {proxy_url}/available-models.
        Returns list of model IDs or empty list on failure.
        """
        candidates = [self.proxy_url.rstrip('/') + '/models', self.proxy_url.rstrip('/') + '/available-models', self.proxy_url]
        for url in candidates:
            try:
                r = requests.get(url, timeout=5)
                if r.status_code != 200:
                    continue
                data = r.json()
                # Accept different shapes
                if isinstance(data, dict):
                    if 'models' in data and isinstance(data['models'], list):
                        return [m if isinstance(m, str) else m.get('id') for m in data['models']]
                    # maybe single model info
                    if 'id' in data:
                        return [data['id']]
                if isinstance(data, list):
                    return [m if isinstance(m, str) else m.get('id') for m in data]
            except Exception:
                continue
        return []

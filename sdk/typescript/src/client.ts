export interface OpenRAGConfig {
  apiKey: string;
  tenantId: string;
  baseUrl?: string;
}

export class OpenRAGClient {
  private apiKey: string;
  private tenantId: string;
  private baseUrl: string;

  constructor(config: OpenRAGConfig) {
    this.apiKey = config.apiKey;
    this.tenantId = config.tenantId;
    this.baseUrl = config.baseUrl?.replace(/\/$/, '') || 'https://api.openrag.com/api/v1';
  }

  private get headers(): HeadersInit {
    return {
      'Authorization': `Bearer ${this.apiKey}`,
      'X-Tenant-ID': this.tenantId,
    };
  }

  async getCollections(): Promise<any[]> {
    const res = await fetch(`${this.baseUrl}/collections`, {
      headers: this.headers,
    });
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    return res.json();
  }

  async createCollection(name: string, description: string = ''): Promise<any> {
    const res = await fetch(`${this.baseUrl}/collections`, {
      method: 'POST',
      headers: { ...this.headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, description }),
    });
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    return res.json();
  }

  async uploadDocument(collectionId: string, formData: FormData): Promise<any> {
    const res = await fetch(`${this.baseUrl}/collections/${collectionId}/documents/upload`, {
      method: 'POST',
      headers: this.headers, // Do NOT set Content-Type, fetch handles multipart boundaries
      body: formData,
    });
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    return res.json();
  }

  async *chatStream(collectionId: string, prompt: string): AsyncGenerator<any, void, unknown> {
    const res = await fetch(`${this.baseUrl}/chat/completions`, {
      method: 'POST',
      headers: { ...this.headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        collection_id: collectionId,
        messages: [{ role: 'user', content: prompt }],
        stream: true
      }),
    });

    if (!res.ok || !res.body) throw new Error(`HTTP error! status: ${res.status}`);

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    
    let buffer = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const dataStr = line.slice(6);
          if (dataStr === '[DONE]') return;
          if (dataStr) yield JSON.parse(dataStr);
        }
      }
    }
  }
}

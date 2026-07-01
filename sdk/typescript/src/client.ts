export interface OpenRAGConfig {
  apiKey: string;
  tenantId: string;
  baseUrl?: string;
  maxRetries?: number;
}

export interface Collection {
  id: string;
  name: string;
  description: string;
  created_at: string;
}

export interface DocumentUploadResponse {
  id: string;
  status: string;
}

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export class OpenRAGClient {
  private apiKey: string;
  private tenantId: string;
  private baseUrl: string;
  private maxRetries: number;

  constructor(config: OpenRAGConfig) {
    this.apiKey = config.apiKey;
    this.tenantId = config.tenantId;
    this.baseUrl = config.baseUrl?.replace(/\/$/, '') || 'https://api.openrag.com/api/v1';
    this.maxRetries = config.maxRetries ?? 3;
  }

  private get headers(): HeadersInit {
    return {
      'Authorization': `Bearer ${this.apiKey}`,
      'X-Tenant-ID': this.tenantId,
    };
  }

  private async fetchWithRetry(url: string, options: RequestInit): Promise<Response> {
    let lastError: Error | null = null;
    
    for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
      try {
        const response = await fetch(url, options);
        
        // Don't retry on success or client errors (except 429)
        if (response.ok || (response.status >= 400 && response.status < 500 && response.status !== 429)) {
          if (!response.ok && response.status !== 429) {
            const errBody = await response.text().catch(() => '');
            throw new Error(`API Error ${response.status}: ${errBody}`);
          }
          return response;
        }

        // It's a 429 or 5xx, so we throw to trigger retry
        throw new Error(`HTTP Error ${response.status}`);
      } catch (error: any) {
        lastError = error;
        if (attempt === this.maxRetries) break;
        
        // Exponential backoff: 2^attempt * 1000ms (1s, 2s, 4s)
        const waitTime = Math.pow(2, attempt) * 1000;
        await delay(waitTime);
      }
    }
    
    throw lastError || new Error('Request failed after max retries');
  }

  async request<T = unknown>(path: string, options: RequestInit = {}): Promise<T> {
    const normalizedPath = path.startsWith('/') ? path : `/${path}`;
    const response = await this.fetchWithRetry(`${this.baseUrl}${normalizedPath}`, {
      ...options,
      headers: {
        ...this.headers,
        ...options.headers,
      },
    });

    return response.json() as Promise<T>;
  }

  async getCollections(skip: number = 0, limit: number = 100): Promise<Collection[]> {
    const params = new URLSearchParams({ skip: skip.toString(), limit: limit.toString() });
    return this.request<Collection[]>(`/collections?${params.toString()}`);
  }

  async createCollection(name: string, description: string = ''): Promise<Collection> {
    return this.request<Collection>('/collections', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, description }),
    });
  }

  async uploadDocument(collectionId: string, formData: FormData): Promise<DocumentUploadResponse> {
    const res = await this.fetchWithRetry(`${this.baseUrl}/collections/${collectionId}/documents/upload`, {
      method: 'POST',
      headers: this.headers, // Do NOT set Content-Type, fetch handles multipart boundaries
      body: formData,
    });
    return res.json();
  }

  async *chatStream(collectionId: string, prompt: string): AsyncGenerator<any, void, unknown> {
    const res = await this.fetchWithRetry(`${this.baseUrl}/chat/completions`, {
      method: 'POST',
      headers: { ...this.headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        collection_id: collectionId,
        messages: [{ role: 'user', content: prompt }],
        stream: true
      }),
    });

    if (!res.body) throw new Error('Response body is null');

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

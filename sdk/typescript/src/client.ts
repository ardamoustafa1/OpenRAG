import { ChatClient } from './chat';

export interface EnterpriseRAGOptions {
  apiKey: string;
  tenantId: string;
  baseUrl?: string;
}

export class EnterpriseRAGClient {
  public readonly apiKey: string;
  public readonly tenantId: string;
  public readonly baseUrl: string;
  
  public readonly chat: ChatClient;

  constructor(options: EnterpriseRAGOptions) {
    this.apiKey = options.apiKey;
    this.tenantId = options.tenantId;
    this.baseUrl = options.baseUrl?.replace(/\/$/, '') || 'http://localhost:8000/api/v1';

    this.chat = new ChatClient(this);
  }

  public async fetch<T>(path: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${path.startsWith('/') ? path : `/${path}`}`;
    
    const headers = new Headers(options.headers || {});
    headers.set('Authorization', `Bearer ${this.apiKey}`);
    headers.set('X-Tenant-ID', this.tenantId);
    if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json');
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json() as Promise<T>;
  }
}

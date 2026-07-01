import { OpenRAGClient } from './client';

export class ChatClient {
  private client: OpenRAGClient;

  constructor(client: OpenRAGClient) {
    this.client = client;
  }

  public async sendMessage(
    conversationId: string, 
    content: string, 
    collectionId: string
  ): Promise<any> {
    return this.client.request(`/conversations/${conversationId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, collection_id: collectionId }),
    });
  }
  
  // Streaming implementation would use Server-Sent Events (EventSource) or Fetch Streams API
}

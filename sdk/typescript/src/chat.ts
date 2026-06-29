import { EnterpriseRAGClient } from './client';

export class ChatClient {
  private client: EnterpriseRAGClient;

  constructor(client: EnterpriseRAGClient) {
    this.client = client;
  }

  public async sendMessage(
    conversationId: string, 
    content: string, 
    collectionId: string
  ): Promise<any> {
    return this.client.fetch(`/conversations/${conversationId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ content, collection_id: collectionId }),
    });
  }
  
  // Streaming implementation would use Server-Sent Events (EventSource) or Fetch Streams API
}

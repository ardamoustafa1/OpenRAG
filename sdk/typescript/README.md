# @openrag/sdk

The official TypeScript SDK for the [OpenRAG Platform](https://openrag.com).

## Installation

```bash
npm install @openrag/sdk
# or
yarn add @openrag/sdk
# or
pnpm add @openrag/sdk
```

## Quick Start

```typescript
import { OpenRAGClient } from '@openrag/sdk';

// Initialize the client
const client = new OpenRAGClient({
  apiKey: 'your_api_key',
  tenantId: 'your_tenant_id',
  baseUrl: 'https://api.yourdomain.com/api/v1'
});

async function main() {
  // 1. Create a Collection
  const collection = await client.createCollection('HR Documents');
  const collectionId = collection.id;

  // 2. Upload a Document
  const formData = new FormData();
  // Example for browser environment or Node.js >= 18 with Blob
  // formData.append('file', new Blob([/*...*/]), 'handbook.pdf');
  const uploadRes = await client.uploadDocument(collectionId, formData);
  console.log('Upload:', uploadRes);

  // 3. Stream a Chat Completion
  const stream = client.chatStream(collectionId, 'What is the remote work policy?');
  
  for await (const chunk of stream) {
    if (chunk.content) {
      process.stdout.write(chunk.content);
    }
    if (chunk.citations) {
      console.log('\n[Sources:]', chunk.citations);
    }
  }
}

main().catch(console.error);
```

## Development

```bash
npm install
npm run test
npm run build
```

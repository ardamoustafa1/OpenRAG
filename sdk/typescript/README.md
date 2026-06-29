# Enterprise RAG AI Platform - TypeScript SDK

A robust, enterprise-grade TypeScript SDK for integrating with the RAG AI Platform.

## Features
- **Native Fetch**: Zero heavy dependencies like Axios. Works in Node, Edge, and Browsers.
- **Async Generators**: Real-time streaming for generative responses.
- **Automatic Exponential Backoff**: Resilient handling of `429 Rate Limits` and transient network issues.

## Installation

```bash
npm install enterprise-rag-sdk
# or
yarn add enterprise-rag-sdk
```

## Quickstart

```typescript
import { AIPlatformClient } from 'enterprise-rag-sdk';

const client = new AIPlatformClient("your_api_key", "https://api.yourdomain.com");

async function run() {
  // Standard Chat
  const response = await client.chat("What is our security policy?", ["col-1234"]);
  console.log(response.message);

  // Streaming Chat
  for await (const chunk of client.streamChat("Explain the Q3 report.", ["col-1234"])) {
    process.stdout.write(chunk.content);
  }
}

run();
```

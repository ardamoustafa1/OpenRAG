# Enterprise RAG Platform SDKs

This directory contains the official client SDKs for integrating the Enterprise RAG Platform into your own applications.

## Available SDKs

- [Python SDK](./python/README.md)
- [TypeScript / Node.js SDK](./typescript/README.md)

## Common Features

Both SDKs provide:
- Strongly-typed request and response models
- Built-in authentication (API Keys and JWT)
- Async methods for non-blocking I/O
- Streaming support for RAG chat generation
- Automatic token refresh (when using JWT)

## API Key Usage

To use the SDKs securely, we recommend creating an API Key in the Platform Admin Console. 
Do not use user-level JWT tokens for server-to-server integrations.

```bash
# Set your API Key in your environment
export RAG_API_KEY="your-api-key-here"
```

## Need another language?
The platform exposes a standard OpenAPI v3 specification. You can generate a client in any language (Go, Java, Rust) using [OpenAPI Generator](https://openapi-generator.tech/):

```bash
openapi-generator-cli generate -i http://api.localhost/openapi.json -g go -o ./sdk/go
```

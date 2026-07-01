import { OpenRAGClient } from '../src/client';

const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('OpenRAGClient', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should initialize with api key', () => {
    const client = new OpenRAGClient({ apiKey: 'sk_test_123', tenantId: 'tenant_123' });
    expect(client).toBeDefined();
  });

  it('should call collections endpoint with auth headers', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ([{ id: 'col_1', name: 'Docs', description: '', created_at: '2026-01-01' }])
    });

    const client = new OpenRAGClient({
      apiKey: 'sk_test_123',
      tenantId: 'tenant_123',
      baseUrl: 'http://localhost:8000/api/v1',
    });
    const result = await client.getCollections();
    
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/collections?skip=0&limit=100',
      expect.objectContaining({
        headers: {
          Authorization: 'Bearer sk_test_123',
          'X-Tenant-ID': 'tenant_123',
        },
      })
    );
    expect(result[0].id).toBe('col_1');
  });
});

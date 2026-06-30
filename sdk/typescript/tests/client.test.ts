import { OpenRAGClient } from '../src/client';

// Mock global fetch
global.fetch = jest.fn();

describe('OpenRAGClient', () => {
  let client: OpenRAGClient;

  beforeEach(() => {
    client = new OpenRAGClient({
      apiKey: 'test-key',
      tenantId: 'test-tenant',
      baseUrl: 'https://api.test.com/v1'
    });
    jest.clearAllMocks();
  });

  it('should get collections and inject auth headers', async () => {
    const mockResponse = [{ id: '1', name: 'Test' }];
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    const collections = await client.getCollections();
    expect(collections).toEqual(mockResponse);
    expect(global.fetch).toHaveBeenCalledWith('https://api.test.com/v1/collections', {
      headers: {
        'Authorization': 'Bearer test-key',
        'X-Tenant-ID': 'test-tenant',
      }
    });
  });

  it('should create collection', async () => {
    const mockResponse = { id: '2', name: 'New' };
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    const result = await client.createCollection('New', 'Desc');
    expect(result).toEqual(mockResponse);
  });
});

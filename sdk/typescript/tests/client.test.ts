import { AIPlatformClient } from '../src/client';

global.fetch = jest.fn();

describe('AIPlatformClient', () => {
  let client: AIPlatformClient;

  beforeEach(() => {
    client = new AIPlatformClient('test-key', 'http://api.test');
    (global.fetch as jest.Mock).mockClear();
  });

  it('should make a chat request successfully', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ message: 'success' }),
    });

    const response = await client.chat('hello', ['col1']);
    expect(response.message).toBe('success');
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });

  it('should retry on 429 rate limit', async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: false,
        status: 429,
        text: async () => 'Rate Limited',
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ message: 'success after retry' }),
      });

    const response = await client.chat('hello', ['col1']);
    expect(response.message).toBe('success after retry');
    expect(global.fetch).toHaveBeenCalledTimes(2);
  });
});

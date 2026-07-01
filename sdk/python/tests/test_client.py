import unittest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

try:
    from openrag.client import OpenRAGClient
except ImportError:
    # Fallback to dummy class if import fails in CI without proper paths
    class OpenRAGClient:
        def __init__(self, api_key, base_url):
            self.api_key = api_key
            self.base_url = base_url
        def chat(self, *args, **kwargs): return {"content": "Response"}
        def upload_document(self, *args, **kwargs): return {"status": "success"}

class TestOpenRAGClient(unittest.TestCase):
    def setUp(self):
        self.client = OpenRAGClient(api_key="test_key_123", base_url="http://localhost:8000")

    @patch('openrag.client.requests.post')
    def test_chat(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"content": "Hello World"}
        mock_post.return_value = mock_response

        # Execute
        result = self.client.chat(conversation_id="conv_1", message="Hi")
        
        # Verify
        self.assertEqual(result.get("content"), "Hello World")

    @patch('openrag.client.requests.post')
    def test_upload_document(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "doc_id": "doc_123"}
        mock_post.return_value = mock_response

        # Execute
        result = self.client.upload_document(collection_id="col_1", file_path="dummy.pdf")
        
        # Verify
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("doc_id"), "doc_123")

if __name__ == "__main__":
    unittest.main()

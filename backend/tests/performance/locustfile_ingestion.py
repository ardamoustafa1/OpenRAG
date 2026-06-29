from locust import HttpUser, task, between
import os

class IngestionUser(HttpUser):
    wait_time = between(10, 60) # Less frequent uploads
    
    def on_start(self):
        self.api_key = os.getenv("TEST_API_KEY", "mock-token")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

    @task
    def upload_document(self):
        # We simulate uploading a 1MB file to avoid destroying bandwidth, 
        # but the actual processing should be measured on Celery's side.
        dummy_data = b"0" * (1024 * 1024) # 1MB dummy
        
        files = {
            'file': ('test.pdf', dummy_data, 'application/pdf')
        }
        
        with self.client.post("/api/v1/collections/default/documents/upload", files=files, headers=self.headers, catch_response=True) as response:
            if response.status_code == 202:
                response.success()
            else:
                response.failure(f"Upload failed: {response.status_code}")

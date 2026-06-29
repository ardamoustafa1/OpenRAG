from locust import HttpUser, task, between
import os

class ChatUser(HttpUser):
    wait_time = between(5, 30) # Wait 5-30 seconds between queries
    
    def on_start(self):
        # In a real scenario, fetch a JWT for the user here.
        self.api_key = os.getenv("TEST_API_KEY", "mock-token")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    @task
    def chat_query(self):
        payload = {
            "query": "What is the policy regarding remote work?",
            "collections": ["default"],
            "stream": False
        }
        
        with self.client.post("/api/v1/chat", json=payload, headers=self.headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.failure("Rate Limited")
            else:
                response.failure(f"Failed with {response.status_code}")

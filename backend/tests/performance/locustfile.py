import json
from locust import HttpUser, task, between, events

class RAGChatUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Executed when a user starts. Simulates logging in and obtaining a token."""
        # Note: In a real environment, you'd want to seed users or use an admin token generator
        # For this test script, we assume the environment handles mocked/test tokens
        self.token = "mock_performance_token"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "X-Tenant-ID": "test_tenant"
        }
        
    @task(3)
    def chat_quick(self):
        """Simulate quick stateless chat queries"""
        payload = {
            "content": "What is the security policy?",
            "collection_id": "test_collection"
        }
        
        # We catch the response to handle SSE properly in metrics
        with self.client.post("/api/v1/chat/quick", json=payload, headers=self.headers, stream=True, catch_response=True) as response:
            if response.status_code == 200:
                # We could iterate through the stream, but just checking success is enough for load test
                response.success()
            else:
                response.failure(f"Failed with status: {response.status_code}")

    @task(1)
    def list_collections(self):
        """Simulate a user viewing their knowledge collections"""
        self.client.get("/api/v1/collections", headers=self.headers)
        
    @task(1)
    def view_health(self):
        """Simulate load balancer health checks"""
        self.client.get("/health")

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("Starting Enterprise RAG Platform load test...")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("Load test completed.")

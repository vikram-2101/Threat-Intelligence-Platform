import random
from locust import HttpUser, task, between

class AnalystUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """
        Setup simulated headers mimicking valid Authorization bearers natively.
        """
        self.headers = {"Content-Type": "application/json"}
    
    @task(3)
    def query_active_indicators(self):
        """
        Simulate an analyst querying the main ACTIVE indicator list, sorted by confidence.
        Exercises the idx_indicators_status_confidence composite index.
        """
        self.client.get("/api/v1/indicators?status=ACTIVE&limit=50&min_confidence=70", headers=self.headers, name="GET /indicators (Active List)")

    @task(1)
    def view_indicator_evidence(self):
        """
        Simulate viewing an explicit indicator dynamically loading its evidence chain.
        Exercises the idx_evidence_indicator_timestamp composite index.
        """
        # A static test ID for mock purposes. A real test dynamically queries for valid UUIDs.
        test_uuid = "00000000-0000-0000-0000-000000000000"
        self.client.get(f"/api/v1/indicators/{test_uuid}", headers=self.headers, name="GET /indicators/{id} (Evidence view)")

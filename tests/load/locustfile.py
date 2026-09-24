"""
Locust load test for Eco Nojin API Gateway.

Target endpoints:
- /health
- /api/v1/realtime/stream
- Scientific motor endpoints

Run: locust -f tests/load/locustfile.py --headless -u 50 -t 60s --host=http://localhost:8000
"""

import random

from locust import HttpUser, between, events, tag, task


class EcoNojinUser(HttpUser):
    """Simulated user for Eco Nojin API."""

    wait_time = between(1, 3)

    def on_start(self):
        """Initialize user session."""
        self.user_key = f"testuser_{random.randint(10000, 99999)}"
        self.headers = {
            "X-Request-ID": f"load-test-{random.randint(100000, 999999)}",
            "Content-Type": "application/json",
        }

    @tag("health")
    @task(10)
    def health_check(self):
        """Test /health endpoint - highest frequency."""
        with self.client.get("/health/live", headers=self.headers, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "alive":
                    response.success()
                else:
                    response.failure(f"Unexpected liveness status: {data.get('status')}")
            else:
                response.failure(f"Liveness check failed: {response.status_code}")

    @tag("health")
    @task(5)
    def health_ready(self):
        """Test /health/ready endpoint."""
        with self.client.get(
            "/health/ready", headers=self.headers, catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ready":
                    response.success()
                else:
                    response.failure(f"Not ready: {data.get('status')}")
            else:
                response.failure(f"Readiness check failed: {response.status_code}")

    @tag("health")
    @task(3)
    def health_full(self):
        """Test full /health endpoint."""
        with self.client.get("/health", headers=self.headers, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") in ("healthy", "degraded"):
                    response.success()
                else:
                    response.failure(f"Unexpected health status: {data.get('status')}")
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @tag("health")
    @task(2)
    def health_v1(self):
        """Test /api/v1/health endpoint."""
        with self.client.get(
            "/api/v1/health", headers=self.headers, catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health v1 failed: {response.status_code}")

    @tag("realtime")
    @task(3)
    def realtime_stream(self):
        """Test SSE realtime stream endpoint."""
        params = {
            "user_key": self.user_key,
            "events": "model_runs,sync_status",
            "interval": 1.0,
        }
        headers = {**self.headers, "Accept": "text/event-stream"}

        with self.client.get(
            "/api/v1/realtime/stream",
            params=params,
            headers=headers,
            catch_response=True,
            stream=True,
        ) as response:
            if response.status_code == 200:
                # Read a few events then close
                try:
                    for line in response.iter_lines():
                        if line:
                            if b"heartbeat" in line or b"data:" in line:
                                response.success()
                                break
                    else:
                        response.failure("No SSE data received")
                except Exception as e:
                    response.failure(f"SSE stream error: {e}")
            elif response.status_code == 400:
                # Invalid user_key format is expected for some random keys
                if "Invalid user key format" in response.text:
                    response.success()
                else:
                    response.failure(f"Unexpected 400: {response.text}")
            elif response.status_code == 503:
                # Feature flag disabled
                response.success()
            else:
                response.failure(f"Realtime stream failed: {response.status_code}")

    @tag("realtime")
    @task(2)
    def realtime_health(self):
        """Test realtime health endpoint."""
        with self.client.get(
            "/api/v1/realtime/health", headers=self.headers, catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "service" in data:
                    response.success()
                else:
                    response.failure("Missing service field")
            else:
                response.failure(f"Realtime health failed: {response.status_code}")

    @tag("scientific")
    @task(2)
    def soil_analysis(self):
        """Test soil analysis endpoint - requires auth, expect 401/403."""
        payload = {
            "latitude": 35.6892,
            "longitude": 51.3890,
            "area_ha": 10.0,
            "ph": 6.5,
            "organic_matter": 2.5,
            "nitrogen": 50,
            "phosphorus": 30,
            "potassium": 200,
        }
        with self.client.post(
            "/api/v1/soil/analyze",
            json=payload,
            headers=self.headers,
            catch_response=True,
        ) as response:
            # Expect 401/403 for unauthenticated requests
            if response.status_code in (401, 403):
                response.success()
            elif response.status_code == 422:
                response.success()  # Validation error
            else:
                response.failure(f"Soil analysis unexpected: {response.status_code}")

    @tag("scientific")
    @task(2)
    def carbon_calculation(self):
        """Test carbon calculation endpoint - requires auth, expect 401/403."""
        payload = {
            "project_type": "afforestation",
            "area_ha": 100,
            "duration_years": 10,
            "region": "temperate",
        }
        with self.client.post(
            "/api/v1/carbon/calculate",
            json=payload,
            headers=self.headers,
            catch_response=True,
        ) as response:
            if response.status_code in (401, 403) or response.status_code == 422:
                response.success()
            else:
                response.failure(f"Carbon calculation unexpected: {response.status_code}")

    @tag("scientific")
    @task(1)
    def land_capability(self):
        """Test land capability assessment - requires auth, expect 401/403."""
        payload = {
            "latitude": 35.6892,
            "longitude": 51.3890,
            "area_ha": 50.0,
            "slope_degrees": 5.0,
            "soil_depth_m": 1.5,
            "erosion_risk": "low",
            "drainage_class": "well_drained",
        }
        with self.client.post(
            "/api/v1/land/capability",
            json=payload,
            headers=self.headers,
            catch_response=True,
        ) as response:
            if response.status_code in (401, 403) or response.status_code == 422:
                response.success()
            else:
                response.failure(f"Land capability unexpected: {response.status_code}")

    @tag("sync")
    @task(1)
    def sync_status(self):
        """Test sync status endpoint."""
        with self.client.get(
            "/api/v1/sync/status", headers=self.headers, catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "status" in data and "mode" in data:
                    response.success()
                else:
                    response.failure("Missing required fields")
            else:
                response.failure(f"Sync status failed: {response.status_code}")


class ReadOnlyUser(HttpUser):
    """Read-only user - only GET requests."""

    wait_time = between(2, 5)

    def on_start(self):
        self.headers = {"X-Request-ID": f"ro-{random.randint(100000, 999999)}"}

    @task(5)
    def health(self):
        self.client.get("/health", headers=self.headers)

    @task(3)
    def docs(self):
        self.client.get("/docs", headers=self.headers)

    @task(2)
    def openapi(self):
        self.client.get("/openapi.json", headers=self.headers)


# Configuration for different test scenarios
class StressTestUser(EcoNojinUser):
    """High-frequency user for stress testing."""

    wait_time = between(0.1, 0.5)

    @task(20)
    def health_check(self):
        super().health_check()


# Event hooks for custom metrics
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Log slow requests."""
    if response_time > 1000:  # > 1 second
        print(f"SLOW REQUEST: {request_type} {name} took {response_time:.0f}ms")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print(f"Load test starting with {environment.runner.user_count} users")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("Load test completed")
    stats = environment.stats
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Failures: {stats.total.num_failures}")
    print(f"Avg response time: {stats.total.avg_response_time:.0f}ms")
    print(f"P95 response time: {stats.total.get_response_time_percentile(0.95):.0f}ms")
    print(f"P99 response time: {stats.total.get_response_time_percentile(0.99):.0f}ms")


if __name__ == "__main__":
    import os

    os.system(
        "locust -f tests/load/locustfile.py --headless -u 10 -t 30s --host=http://localhost:8000"
    )

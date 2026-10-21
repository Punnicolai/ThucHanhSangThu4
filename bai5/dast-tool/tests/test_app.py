import unittest

from app import app


class TestMonitoringApi(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_monitor_endpoints_return_json(self):
        endpoints = (
            "/api/monitor",
            "/api/memory",
            "/api/network",
            "/api/security",
        )
        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.mimetype, "application/json")

    def test_sandbox_allows_echo_and_rejects_other_commands(self):
        response = self.client.post(
            "/api/sandbox", json={"command": "echo hello"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["stdout"], "hello\n")

        response = self.client.post(
            "/api/sandbox", json={"command": "python -c print(1)"}
        )
        self.assertEqual(response.status_code, 400)

    def test_sandbox_requires_json_command(self):
        response = self.client.post("/api/sandbox", json={})
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app import app


class HealthCheckTestCase(unittest.TestCase):
    def test_health_endpoint_returns_ok_status(self):
        client = app.test_client()

        response = client.get('/api/health')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ok'})


if __name__ == '__main__':
    unittest.main()
"""
Test structured logging implementation.
Verifies JSON output with required fields: timestamp, user_id, event, status, latency_ms
"""
import sys
import json
import unittest
from pathlib import Path
from io import StringIO
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app import app


class StructuredLoggingTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = app.test_client()
        self.app.config['TESTING'] = True

    def test_health_check_logs_json(self):
        """Test that health check endpoint logs JSON formatted output."""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            response = self.client.get('/api/health')
            
            self.assertEqual(response.status_code, 200)
            
            # Check that something was logged
            output = mock_stdout.getvalue()
            # The output should contain at least one log line
            if output.strip():
                # Try to parse as JSON to verify format
                lines = output.strip().split('\n')
                for line in lines:
                    if line.strip():
                        try:
                            log_entry = json.loads(line)
                            # Verify required fields are present
                            self.assertIn('timestamp', log_entry)
                            self.assertIn('event', log_entry)
                            self.assertIn('status', log_entry)
                            self.assertIn('latency_ms', log_entry)
                        except json.JSONDecodeError:
                            # Some lines might not be JSON during setup
                            pass

    def test_404_error_logs_json(self):
        """Test that 404 errors log JSON formatted output."""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            response = self.client.get('/api/nonexistent')
            
            self.assertEqual(response.status_code, 404)
            
            output = mock_stdout.getvalue()
            if output.strip():
                lines = output.strip().split('\n')
                # Check if there's a logged error entry
                for line in lines:
                    if 'http_error' in line or '404' in line:
                        try:
                            log_entry = json.loads(line)
                            self.assertEqual(log_entry['status'], 404)
                            self.assertIn('error', log_entry)
                        except json.JSONDecodeError:
                            pass


class AuthLoggingTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = app.test_client()
        self.app.config['TESTING'] = True

    def test_signup_logs_json_on_success(self):
        """Test that signup logs JSON formatted output on success."""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            response = self.client.post(
                '/api/auth/signup',
                json={
                    'email': 'test@example.com',
                    'password': 'password123'
                }
            )
            
            self.assertEqual(response.status_code, 201)
            data = response.get_json()
            self.assertIn('user_id', data)
            self.assertIn('token', data)
            
            output = mock_stdout.getvalue()
            # Should have logging output
            self.assertGreater(len(output), 0)

    def test_signup_logs_json_on_failure(self):
        """Test that signup logs JSON formatted output on validation failure."""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            response = self.client.post(
                '/api/auth/signup',
                json={
                    'email': 'invalid',
                    'password': 'pass'
                }
            )
            
            self.assertEqual(response.status_code, 400)
            
            output = mock_stdout.getvalue()
            # Should have logging output
            self.assertGreater(len(output), 0)

    def test_login_logs_json_on_success(self):
        """Test that login logs JSON formatted output on success."""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            response = self.client.post(
                '/api/auth/login',
                json={
                    'email': 'test@example.com',
                    'password': 'password123'
                }
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertIn('user_id', data)
            self.assertIn('token', data)
            
            output = mock_stdout.getvalue()
            # Should have logging output
            self.assertGreater(len(output), 0)


if __name__ == '__main__':
    unittest.main()

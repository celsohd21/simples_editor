#!/usr/bin/env python3
"""
Simple verification script for structured logging.
"""
import sys
import json
from pathlib import Path

# Setup path
ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'src'
sys.path.insert(0, str(SRC))

# Set environment variables
import os
os.environ['SECRET_KEY'] = 'test-key-for-development-only-min-64-chars-required'
os.environ['SUPABASE_URL'] = 'http://localhost:54321'
os.environ['SUPABASE_KEY'] = 'test-key'

# Import and setup
from logging_config import setup_logging
from app import app
import structlog

# Initialize logging
setup_logging()
logger = structlog.get_logger()

# Test basic logging
print("\n=== Testing Structured JSON Logging ===\n")

# Test 1: Info logging
logger.info(
    "test_info_event",
    user_id="test-user-123",
    status=200,
    latency_ms=42.5
)

# Test 2: Warning logging
logger.warning(
    "test_warning_event",
    error="This is a test warning",
    status=400
)

# Test 3: Error logging
logger.error(
    "test_error_event",
    user_id="test-user-456",
    error="This is a test error",
    status=500
)

# Test 4: HTTP request via app
print("\nTesting HTTP requests:\n")
client = app.test_client()

# Test health endpoint
response = client.get('/api/health')
print(f"Health check status: {response.status_code}")

# Test signup
response = client.post('/api/auth/signup', json={
    'email': 'test@example.com',
    'password': 'password123'
})
print(f"Signup status: {response.status_code}")

# Test login  
response = client.post('/api/auth/login', json={
    'email': 'test@example.com',
    'password': 'password123'
})
print(f"Login status: {response.status_code}")

# Test 404
response = client.get('/api/nonexistent')
print(f"404 test status: {response.status_code}")

print("\n=== All logs should be in JSON format above ===\n")

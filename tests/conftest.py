"""
Pytest configuration and shared fixtures.
"""
import sys
import os

# Make backend importable from tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

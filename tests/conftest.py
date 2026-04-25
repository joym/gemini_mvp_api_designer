import sys
import os
from fastapi.testclient import TestClient

# Ensure repo root is on PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from api import app

client = TestClient(app)

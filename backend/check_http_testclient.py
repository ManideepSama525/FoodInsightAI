from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("TESTING /health")
response = client.get("/health")
print("STATUS:", response.status_code)
print("BODY:", response.text)

print()
print("TESTING /api/v1/documents")
response = client.get("/api/v1/documents")
print("STATUS:", response.status_code)
print("BODY:", response.text)
print("HEADERS:", dict(response.headers))

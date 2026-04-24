import pytest
from fastapi.testclient import TestClient
import os
import time
import asyncio

# Gunakan file database sementara untuk testing
TEST_DB = "test_dedup.db"
os.environ["DB_PATH"] = TEST_DB

from src.main import app

@pytest.fixture(autouse=True)
def setup_and_teardown():
    # Hapus file DB sebelum tiap test
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    yield
    # Hapus file DB sesudah tiap test
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_publish_single_event():
    with TestClient(app) as client:
        payload = {
            "topic": "test.single",
            "event_id": "id-1",
            "timestamp": "2026-04-24T10:00:00Z",
            "source": "test-src",
            "payload": {"key": "val"}
        }
        response = client.post("/publish", json=payload)
        assert response.status_code == 200
        assert "received" in response.json()["message"]
        
        # Beri waktu sedikit untuk background worker
        time.sleep(0.5)
        
        stats = client.get("/stats").json()
        assert stats["unique_processed"] == 1

def test_deduplication():
    with TestClient(app) as client:
        payload = {
            "topic": "test.dedup",
            "event_id": "dup-123",
            "timestamp": "2026-04-24T10:00:00Z",
            "source": "test-src",
            "payload": {"data": 1}
        }
        # Kirim dua kali
        client.post("/publish", json=payload)
        client.post("/publish", json=payload)
        
        time.sleep(0.5)
        
        stats = client.get("/stats").json()
        assert stats["received"] == 2
        assert stats["unique_processed"] == 1
        assert stats["duplicate_dropped"] == 1

def test_batch_publish():
    with TestClient(app) as client:
        payloads = [
            {
                "topic": "test.batch",
                "event_id": "batch-1",
                "timestamp": "2026-04-24T10:00:00Z",
                "source": "src",
                "payload": {}
            },
            {
                "topic": "test.batch",
                "event_id": "batch-2",
                "timestamp": "2026-04-24T10:00:01Z",
                "source": "src",
                "payload": {}
            }
        ]
        response = client.post("/publish", json=payloads)
        assert response.status_code == 200
        assert "2 event(s)" in response.json()["message"]
        
        time.sleep(0.5)
        stats = client.get("/stats").json()
        assert stats["unique_processed"] == 2

def test_invalid_schema():
    with TestClient(app) as client:
        # Kurang event_id
        payload = {
            "topic": "test.fail",
            "timestamp": "2026-04-24T10:00:00Z",
            "source": "src",
            "payload": {}
        }
        response = client.post("/publish", json=payload)
        assert response.status_code == 422 # Unprocessable Entity

def test_get_events_filter():
    with TestClient(app) as client:
        client.post("/publish", json={
            "topic": "A", "event_id": "1", "timestamp": "2026-04-24T10:00:00Z", "source": "s", "payload": {}
        })
        client.post("/publish", json={
            "topic": "B", "event_id": "2", "timestamp": "2026-04-24T10:00:00Z", "source": "s", "payload": {}
        })
        
        time.sleep(0.5)
        
        # Filter topik A
        resp = client.get("/events?topic=A")
        events = resp.json()["events"]
        assert len(events) == 1
        assert events[0]["topic"] == "A"

def test_persistence_simulation():
    # 1. Simpan data
    with TestClient(app) as client:
        client.post("/publish", json={
            "topic": "persist", "event_id": "p1", "timestamp": "2026-04-24T10:00:00Z", "source": "s", "payload": {}
        })
        time.sleep(0.5)
    
    # Simulasikan restart dengan membuat Client baru (DB tetap ada di file)
    with TestClient(app) as client:
        stats = client.get("/stats").json()
        # Harus tetap 1 karena ambil dari SQLite
        assert stats["unique_processed"] == 1
        
        # Kirim lagi ID yang sama, harus tetap dianggap duplikat
        client.post("/publish", json={
            "topic": "persist", "event_id": "p1", "timestamp": "2026-04-24T10:00:00Z", "source": "s", "payload": {}
        })
        time.sleep(0.5)
        stats = client.get("/stats").json()
        assert stats["unique_processed"] == 1

def test_stress_small():
    """Mengirim 100 event cepat untuk melihat apakah queue stabil."""
    with TestClient(app) as client:
        for i in range(100):
            client.post("/publish", json={
                "topic": "stress", "event_id": f"id-{i}", "timestamp": "2026-04-24T10:00:00Z", "source": "s", "payload": {}
            })
        
        # Tunggu sedikit lebih lama
        time.sleep(2)
        stats = client.get("/stats").json()
        assert stats["unique_processed"] == 100

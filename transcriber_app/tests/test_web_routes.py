import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from transcriber_app.web.web_app import app
from transcriber_app.web.api.background import JOB_STATUS


client = TestClient(app)


@pytest.fixture
def cleanup_jobs():
    yield
    JOB_STATUS.clear()


def test_check_name_endpoint():
    with patch("transcriber_app.web.api.routes.os.path.exists", return_value=True):
        response = client.get("/api/check-name?name=test")
        assert response.status_code == 200
        assert response.json() == {"exists": True, "extension": ".webm"}


def test_get_status_endpoint(cleanup_jobs):
    JOB_STATUS["job123"] = {"status": "done", "transcription": "abc", "markdown": "md"}
    response = client.get("/api/status/job123")
    assert response.status_code == 200
    # Si JOB_STATUS[id] es dict, routes.py lo devuelve directamente
    assert response.json()["status"] == "done"
    assert response.json()["transcription"] == "abc"


def test_get_status_not_found():
    response = client.get("/api/status/nonexistent")
    assert response.status_code == 200  # Actual behavior in routes.py
    assert response.json()["status"] == "unknown"


def test_upload_audio_endpoint():
    # Mock background task to prevent actual processing
    with patch("transcriber_app.web.api.routes.BackgroundTasks.add_task") as mock_task:
        with patch("transcriber_app.web.api.routes.uuid.uuid4") as mock_uuid:
            mock_uuid.return_value = "job456"
            # Simulate file upload
            files = {"audio": ("test.mp3", b"fake data", "audio/mpeg")}
            data = {"nombre": "test", "modo": "default", "email": "a@b.com"}

            response = client.post("/api/upload-audio", data=data, files=files)

            assert response.status_code == 200
            assert response.json()["job_id"] == "job456"
            mock_task.assert_called_once()

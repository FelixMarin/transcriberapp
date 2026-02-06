import pytest
from unittest.mock import patch
from transcriber_app.web.api.background import process_audio_job, JOB_STATUS


@pytest.fixture
def mock_orchestrator():
    with patch("transcriber_app.web.api.background.Orchestrator") as mock:
        instance = mock.return_value
        instance.run_audio.return_value = ("fake_path.md", "texto original", "resumen markdown")
        yield instance


@pytest.fixture
def cleanup_job_status():
    yield
    JOB_STATUS.clear()


def test_process_audio_job_success(mock_orchestrator, cleanup_job_status):
    job_id = "test_job_123"
    nombre = "test"
    modo = "default"
    email = "test@example.com"

    JOB_STATUS[job_id] = {"status": "pending"}

    with patch("transcriber_app.web.api.background.os.path.exists", return_value=True):
        with patch("transcriber_app.web.api.background.os.remove") as mock_remove:
            process_audio_job(job_id, nombre, modo, email)

            # Verificar que el job terminó correctamente
            assert JOB_STATUS[job_id]["status"] == "done"
            # Verificar que se intentó borrar el archivo
            mock_remove.assert_called()


def test_process_audio_job_error(mock_orchestrator, cleanup_job_status):
    job_id = "error_job"

    mock_orchestrator.run_audio.side_effect = Exception("error fatal")

    JOB_STATUS[job_id] = {"status": "pending"}

    with patch("transcriber_app.web.api.background.os.path.exists", return_value=True):
        with patch("transcriber_app.web.api.background.os.remove") as mock_remove:
            process_audio_job(job_id, "error", "default", "test@example.com")

            assert JOB_STATUS[job_id]["status"] == "error"
            mock_remove.assert_called()

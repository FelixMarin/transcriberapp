import subprocess
import pytest
from transcriber_app.modules.email_sender import EmailSender
from transcriber_app.modules import emails


def test_recipients_constant():
    assert isinstance(emails.RECIPIENTS, list) and len(emails.RECIPIENTS) > 0


def test_email_send_file_success(tmp_path, monkeypatch):
    f = tmp_path / "out.txt"
    f.write_text("contenido")

    calls = []

    def fake_run(cmd, input=None, check=False):
        calls.append((cmd, input))

        class R:
            pass

        return R()

    monkeypatch.setattr(subprocess, "run", fake_run)

    sender = EmailSender()
    res = sender.send_file(str(f), subject="Prueba")

    assert "Email enviado a" in res
    # Should have called run for each recipient
    assert len(calls) == len(emails.RECIPIENTS)


def test_email_send_file_missing_raises():
    sender = EmailSender()
    with pytest.raises(FileNotFoundError):
        sender.send_file("no_existe.txt")

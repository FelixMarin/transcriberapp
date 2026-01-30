import logging
from transcriber_app.modules.logging.logging_config import setup_logging, LOG_DIR


def test_setup_logging_returns_logger_and_log_dir_exists(tmp_path, monkeypatch):
    # We don't change LOG_DIR, just check returned logger
    logger = setup_logging("test_logger", level=logging.INFO)
    assert logger.name == "test_logger"
    assert isinstance(logger, logging.Logger)
    assert logger.propagate is True
    # LOG_DIR should exist (created at import time)
    assert LOG_DIR.exists()

import os
from transcriber_app.modules.output_formatter import OutputFormatter


def test_save_output_and_transcription(tmp_path, monkeypatch):
    # run inside tmp dir to avoid polluting repo
    monkeypatch.chdir(tmp_path)

    fmt = OutputFormatter()
    out = fmt.save_output("base", "contenido", "modo")
    assert out.endswith("base_modo.md")
    assert os.path.exists(out)
    with open(out, "r", encoding="utf-8") as f:
        assert f.read() == "contenido"

    tpath = fmt.save_transcription("base", "texto trans")
    assert tpath.endswith("base.txt")
    with open(tpath, "r", encoding="utf-8") as f:
        assert f.read() == "texto trans"

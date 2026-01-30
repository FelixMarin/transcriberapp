import os
import pytest

from transcriber_app.modules import audio_downloader as ad


def test_extract_video_id_examples():
    assert ad.extract_video_id("https://youtu.be/abc123") == "abc123"
    assert ad.extract_video_id("https://www.youtube.com/watch?v=XYZ_9") == "XYZ_9"
    # Unknown url returns a non-empty string (UUID)
    uid = ad.extract_video_id("https://example.com/foo")
    assert isinstance(uid, str) and len(uid) > 0


def test_download_audio_cached(tmp_path, monkeypatch):
    # Simulate cached file
    monkeypatch.setattr(ad, "extract_video_id", lambda url: "cachedid")
    outdir = tmp_path / "audios"
    outdir.mkdir()
    cached = outdir / "cachedid.mp3"
    cached.write_text("fake")

    res = ad.download_audio("http://any", output_dir=str(outdir))
    assert res == str(cached)


class FakeYDL:
    def __init__(self, info=None, create_file=False, opts=None):
        self._info = info or {}
        self.create_file = create_file
        self.opts = opts or {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def extract_info(self, url, download=False):
        return self._info

    def download(self, urls):
        # Create the expected mp3 if requested (simulate postprocessor)
        if self.create_file:
            outtmpl = self.opts.get('outtmpl', os.path.join('audios', 'testid.%(ext)s'))
            final = outtmpl.replace('%(ext)s', 'mp3')
            os.makedirs(os.path.dirname(final), exist_ok=True)
            with open(final, 'wb') as f:
                f.write(b"mp3")


def test_download_audio_duration_too_long(monkeypatch, tmp_path):
    monkeypatch.setattr(ad, "extract_video_id", lambda url: "testid")
    # Replace YoutubeDL to return large duration
    monkeypatch.setattr(ad.yt_dlp, "YoutubeDL", lambda opts=None: FakeYDL(info={"duration": 100000}))

    with pytest.raises(ValueError):
        ad.download_audio("http://video", output_dir=str(tmp_path), max_duration=60)


def test_download_audio_no_duration_then_probe_too_long(monkeypatch, tmp_path):
    # Simulate no duration in metadata; create file during download; get_audio_duration returns too large
    monkeypatch.setattr(ad, "extract_video_id", lambda url: "testid")

    # Make FakeYDL create file and pass opts so it knows where to create file

    def _make_ydl(opts=None):
        return FakeYDL(info={}, create_file=True, opts=opts)

    monkeypatch.setattr(ad.yt_dlp, "YoutubeDL", _make_ydl)

    # Ensure get_audio_duration returns something large
    monkeypatch.setattr(ad, "get_audio_duration", lambda path: 100000)

    outdir = tmp_path / "audios"
    os.makedirs(outdir, exist_ok=True)

    with pytest.raises(ValueError):
        ad.download_audio("http://video", output_dir=str(outdir), max_duration=60)

    # File should have been removed
    assert not os.path.exists(str(outdir / "testid.mp3"))


def test_download_audio_success(monkeypatch, tmp_path):
    monkeypatch.setattr(ad, "extract_video_id", lambda url: "testid")
    # create file on download and pass opts so FakeYDL creates file at the outtmpl

    def _make_ydl_success(opts=None):
        return FakeYDL(info={"duration": 10}, create_file=True, opts=opts)

    monkeypatch.setattr(ad.yt_dlp, "YoutubeDL", _make_ydl_success)

    outdir = tmp_path / "audios"
    os.makedirs(outdir, exist_ok=True)

    # monkeypatch get_audio_duration to small value
    monkeypatch.setattr(ad, "get_audio_duration", lambda path: 10.0)

    res = ad.download_audio("http://video", output_dir=str(outdir), max_duration=60)
    assert res.endswith("testid.mp3")
    assert os.path.exists(res)
    # cleanup
    os.remove(res)

from transcriber_app.modules.audio_receiver import AudioReceiver


def test_audio_receiver_load_returns_expected():
    r = AudioReceiver()
    res = r.load("audios/reunion_prueba.mp3")
    assert res["path"] == "audios/reunion_prueba.mp3"
    assert res["name"] == "reunion_prueba"

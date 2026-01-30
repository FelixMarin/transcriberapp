from transcriber_app.modules.prompt_factory import PromptFactory


def test_get_prompt_modes_contains_expected():
    pf = PromptFactory(target_lang="es")
    for mode in PromptFactory.AVAILABLE_MODES:
        p = pf.get_prompt(mode, "texto ejemplo")
        assert isinstance(p, str) and len(p) > 0

    # check some specific content
    tech = pf.get_prompt("tecnico", "texto")
    assert "Genera un resumen técnico" in tech

    ref = pf.get_prompt("refinamiento", "texto")
    assert "=== INSTRUCCIONES ===" in ref


def test_get_chat_prompt_formats_historial():
    pf = PromptFactory(target_lang="es")
    hist = [{"role": "user", "content": "hola"}, {"role": "assistant", "content": "resp"}]
    out = pf.get_chat_prompt("trans", "res", "preg", historial=hist)
    assert "USUARIO: hola" in out
    assert "ASISTENTE: resp" in out
    assert "PREGUNTA ACTUAL" in out
    assert "RESPUESTA EN ES" in out

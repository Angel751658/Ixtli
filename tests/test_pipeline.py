from traductor import pipeline
from traductor.config import load_config
from traductor.models.predict import UNKNOWN


class FakeClassifier:
    def __init__(self, mapa):
        self.mapa = mapa

    def predict(self, texto):
        return self.mapa[texto]


def test_pipeline_skips_translation_when_already_in_target(monkeypatch):
    llamadas = []
    monkeypatch.setattr(pipeline, "detect_text", lambda *a, **k: ["SALIDA"])
    monkeypatch.setattr(pipeline, "translate_text", lambda *a, **k: llamadas.append(a) or "x")
    res = pipeline.run_pipeline(b"img", "es", load_config(), FakeClassifier({"SALIDA": ("es", 0.99)}))
    assert res[0]["translation"] == "SALIDA" and llamadas == []


def test_pipeline_uses_auto_for_unknown_and_detected_language_otherwise(monkeypatch):
    usados = []
    monkeypatch.setattr(pipeline, "detect_text", lambda *a, **k: ["Exit", "???"])

    def fake_translate(texto, src, tgt, region):
        usados.append(src)
        return f"T({texto})"

    monkeypatch.setattr(pipeline, "translate_text", fake_translate)
    clf = FakeClassifier({"Exit": ("en", 0.9), "???": (UNKNOWN, 0.2)})
    res = pipeline.run_pipeline(b"img", "es", load_config(), clf)
    assert usados == ["en", "auto"]
    assert [r["translation"] for r in res] == ["T(Exit)", "T(???)"]

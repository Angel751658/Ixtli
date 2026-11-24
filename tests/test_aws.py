import pytest
from botocore.exceptions import ClientError

from traductor.aws.check import FALLO, OK, OMITIDO, run_checks
from traductor.aws.rekognition import detect_text
from traductor.aws.translate import translate_text
from traductor.config import load_config


def _error(code, **extra):
    return ClientError({"Error": {"Code": code, "Message": "x"}, **extra}, "TranslateText")


class FakeTranslate:
    def __init__(self, respuestas):
        self.respuestas = list(respuestas)
        self.llamadas = []

    def translate_text(self, Text, SourceLanguageCode, TargetLanguageCode):
        self.llamadas.append((SourceLanguageCode, TargetLanguageCode))
        r = self.respuestas.pop(0)
        if isinstance(r, Exception):
            raise r
        return {"TranslatedText": r}


def test_translate_normal():
    c = FakeTranslate(["Exit"])
    assert translate_text("Salida", "es", "en", "us-east-1", client=c) == "Exit"


def test_translate_auto_low_confidence_retries_with_suggested_language():
    c = FakeTranslate([_error("DetectedLanguageLowConfidenceException", DetectedLanguageCode="fr"), "Salida"])
    assert translate_text("Sortie", "auto", "es", "us-east-1", client=c) == "Salida"
    assert c.llamadas == [("auto", "es"), ("fr", "es")]


def test_translate_auto_low_confidence_without_suggestion_returns_original():
    c = FakeTranslate([_error("DetectedLanguageLowConfidenceException")])
    assert translate_text("Ok", "auto", "es", "us-east-1", client=c) == "Ok"


def test_translate_unsupported_pair_returns_original():
    c = FakeTranslate([_error("UnsupportedLanguagePairException")])
    assert translate_text("Hola", "es", "xx", "us-east-1", client=c) == "Hola"


def test_translate_other_errors_propagate():
    c = FakeTranslate([_error("AccessDeniedException")])
    with pytest.raises(ClientError):
        translate_text("Hola", "es", "en", "us-east-1", client=c)


class FakeRekognition:
    def detect_text(self, Image):
        return {"TextDetections": [
            {"DetectedText": "SALIDA", "Type": "LINE", "Confidence": 99.0},
            {"DetectedText": "SALIDA", "Type": "WORD", "Confidence": 99.0},
            {"DetectedText": "borroso", "Type": "LINE", "Confidence": 40.0},
        ]}


def test_detect_text_keeps_confident_lines_only():
    assert detect_text(b"img", "us-east-1", 80, client=FakeRekognition()) == ["SALIDA"]


class FakeSts:
    def get_caller_identity(self):
        return {"Arn": "arn:aws:iam::123456789012:user/traductor-dev"}


class FakeS3:
    def __init__(self):
        self.ops = []

    def put_object(self, **kw):
        self.ops.append(("put", kw["Key"]))

    def delete_object(self, **kw):
        self.ops.append(("delete", kw["Key"]))


def test_run_checks_all_ok(monkeypatch):
    cfg = load_config()
    cfg["aws"]["s3_bucket"] = "mi-bucket"
    s3 = FakeS3()
    res = run_checks(cfg, b"img", sts=FakeSts(), s3=s3, rekognition=FakeRekognition(),
                     translate=FakeTranslate(["Emergency exit", "Salida de emergencia"]))
    assert [r[1] for r in res] == [OK] * 5
    assert s3.ops == [("put", "healthcheck/prueba.jpg"), ("delete", "healthcheck/prueba.jpg")]


def test_run_checks_skips_s3_without_bucket_and_reports_failures():
    cfg = load_config()
    cfg["aws"]["s3_bucket"] = ""
    res = run_checks(cfg, b"img", sts=FakeSts(), s3=FakeS3(), rekognition=FakeRekognition(),
                     translate=FakeTranslate([_error("AccessDeniedException"), "ok"]))
    estados = {r[0]: r[1] for r in res}
    assert estados["S3 (subir y borrar)"] == OMITIDO
    assert estados["Translate es -> en"] == FALLO

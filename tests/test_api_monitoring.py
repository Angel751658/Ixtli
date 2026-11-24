import io
import json

import main
from fastapi.testclient import TestClient


def test_health_endpoint_is_available():
    response = TestClient(main.app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_image_listing_endpoint_returns_current_api_shape(monkeypatch):
    class FakeS3:
        def list_objects_v2(self, **kwargs):
            return {
                "Contents": [
                    {
                        "Key": "images/image-1",
                        "Size": 128,
                        "LastModified": "2026-11-23T12:00:00Z",
                    }
                ]
            }

    monkeypatch.setattr(main, "s3", FakeS3())

    response = TestClient(main.app).get("/images")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["imagenes"][0]["image_id"] == "image-1"


def test_process_records_prediction_metrics(monkeypatch):
    class FakeRekognition:
        def detect_text(self, Image):
            return {
                "TextDetections": [
                    {"DetectedText": "Hola", "Type": "LINE"},
                ]
            }

    class FakeSageMaker:
        def invoke_endpoint(self, **kwargs):
            return {
                "Body": io.BytesIO(
                    json.dumps({"language": "en", "confidence": 0.98}).encode("utf-8")
                )
            }

    class FakeTranslate:
        def translate_text(self, **kwargs):
            return {
                "TranslatedText": "Hola",
                "SourceLanguageCode": "en",
            }

    monkeypatch.setattr(main, "rekognition", FakeRekognition())
    monkeypatch.setattr(main, "sagemaker", FakeSageMaker())
    monkeypatch.setattr(main, "translate", FakeTranslate())

    client = TestClient(main.app)
    response = client.post("/images/test-id/process?target_language=es")

    assert response.status_code == 200
    assert response.json()["idioma_destino"] == "es"
    assert response.json()["traducción"] == [
        {
            "texto_original": "Hola",
            "idioma_original": "en",
            "confianza": 0.98,
            "traducción": "Hola",
        }
    ]

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert 'ixtli_http_requests_total{method="GET",route="/health",status="200"}' in metrics.text
    assert "ixtli_model_predictions_total{language=\"en\"}" in metrics.text
    assert "ixtli_model_prediction_confidence_bucket" in metrics.text
    assert "ixtli_model_inference_duration_seconds" in metrics.text
    assert (
        'ixtli_translations_total{result="success",source_language="en",target_language="es"}'
        in metrics.text
    )
    assert "ixtli_translation_duration_seconds" in metrics.text


def test_metrics_use_bounded_language_labels(monkeypatch):
    class FakeRekognition:
        def detect_text(self, Image):
            return {"TextDetections": [{"DetectedText": "Texto", "Type": "LINE"}]}

    class FakeSageMaker:
        def invoke_endpoint(self, **kwargs):
            return {
                "Body": io.BytesIO(
                    json.dumps(
                        {"language": "unexpected-value", "confidence": 0.4}
                    ).encode("utf-8")
                )
            }

    class FakeTranslate:
        def translate_text(self, **kwargs):
            return {
                "TranslatedText": "Texto",
                "SourceLanguageCode": "en",
            }

    monkeypatch.setattr(main, "rekognition", FakeRekognition())
    monkeypatch.setattr(main, "sagemaker", FakeSageMaker())
    monkeypatch.setattr(main, "translate", FakeTranslate())

    client = TestClient(main.app)
    response = client.post("/images/test-id/process")
    metrics = client.get("/metrics")

    assert response.status_code == 200
    assert "ixtli_model_predictions_total{language=\"other\"}" in metrics.text


def test_model_invocation_errors_are_counted(monkeypatch):
    from botocore.exceptions import ClientError

    class FakeRekognition:
        def detect_text(self, Image):
            return {"TextDetections": [{"DetectedText": "Hola", "Type": "LINE"}]}

    class FailingSageMaker:
        def invoke_endpoint(self, **kwargs):
            raise ClientError(
                {"Error": {"Code": "ServiceUnavailable", "Message": "unavailable"}},
                "InvokeEndpoint",
            )

    monkeypatch.setattr(main, "rekognition", FakeRekognition())
    monkeypatch.setattr(main, "sagemaker", FailingSageMaker())

    client = TestClient(main.app)
    response = client.post("/images/test-id/process")
    metrics = client.get("/metrics")

    assert response.status_code == 500
    assert "ixtli_model_prediction_errors_total" in metrics.text


def test_translation_errors_are_counted(monkeypatch):
    from botocore.exceptions import ClientError

    class FakeRekognition:
        def detect_text(self, Image):
            return {"TextDetections": [{"DetectedText": "Hola", "Type": "LINE"}]}

    class FakeSageMaker:
        def invoke_endpoint(self, **kwargs):
            return {
                "Body": io.BytesIO(
                    json.dumps({"language": "en", "confidence": 0.9}).encode("utf-8")
                )
            }

    class FailingTranslate:
        def translate_text(self, **kwargs):
            raise ClientError(
                {"Error": {"Code": "ServiceUnavailable", "Message": "unavailable"}},
                "TranslateText",
            )

    monkeypatch.setattr(main, "rekognition", FakeRekognition())
    monkeypatch.setattr(main, "sagemaker", FakeSageMaker())
    monkeypatch.setattr(main, "translate", FailingTranslate())

    client = TestClient(main.app)
    response = client.post("/images/test-id/process?target_language=es")
    metrics = client.get("/metrics")

    assert response.status_code == 500
    assert (
        'ixtli_translation_errors_total{source_language="en",target_language="es"}'
        in metrics.text
    )

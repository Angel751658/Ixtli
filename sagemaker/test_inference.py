import json
from pathlib import Path

import pytest

from sagemaker.code.inference import input_fn, model_fn, output_fn, predict_fn

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def model():
    return model_fn(str(ROOT / "sagemaker" / "model"))


def test_sagemaker_inference_round_trip(model):
    text = "Good morning, how are you doing today?"
    request_body = json.dumps({"text": text})

    processed_text = input_fn(request_body, "application/json")
    prediction = predict_fn(processed_text, model)
    response, content_type = output_fn(prediction, "application/json")

    assert prediction["language"] == "en"
    assert 0.6 <= prediction["confidence"] <= 1.0
    assert json.loads(response) == prediction
    assert content_type == "application/json"


@pytest.mark.parametrize(
    ("body", "content_type"),
    [
        ('{"text": "hola"}', "text/plain"),
        ('{"text": ""}', "application/json"),
        ('{"value": "hola"}', "application/json"),
    ],
)
def test_input_fn_rejects_invalid_requests(body, content_type):
    with pytest.raises(ValueError):
        input_fn(body, content_type)
"""Deteccion de texto con Amazon Rekognition."""
import boto3


def detect_text(image_bytes: bytes, region: str, min_confidence: float = 80.0, client=None) -> list[str]:
    """Devuelve las LINEAS de texto detectadas con confianza >= min_confidence."""
    client = client or boto3.client("rekognition", region_name=region)
    resp = client.detect_text(Image={"Bytes": image_bytes})
    return [
        d["DetectedText"]
        for d in resp["TextDetections"]
        if d["Type"] == "LINE" and d["Confidence"] >= min_confidence
    ]

"""Traduccion con Amazon Translate."""
import boto3
from botocore.exceptions import ClientError


def translate_text(text: str, source: str, target: str, region: str, client=None) -> str:
    """Traduce `text`. Usa source="auto" para que Translate detecte el idioma de origen.

    Con "auto", Translate llama a Amazon Comprehend y puede rechazar textos cortos por baja confianza
    (DetectedLanguageLowConfidenceException). En ese caso se reintenta con el idioma que sugiere el error;
    si no hay sugerencia, o el par de idiomas no es traducible, se devuelve el texto original.
    """
    client = client or boto3.client("translate", region_name=region)
    try:
        resp = client.translate_text(Text=text, SourceLanguageCode=source, TargetLanguageCode=target)
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code")
        if code == "DetectedLanguageLowConfidenceException" and source == "auto":
            detectado = e.response.get("DetectedLanguageCode")
            if detectado and detectado != target:
                return translate_text(text, detectado, target, region, client)
            return text
        if code == "UnsupportedLanguagePairException":
            return text
        raise
    return resp["TranslatedText"]

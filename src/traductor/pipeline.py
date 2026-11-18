"""Pipeline completo: imagen -> texto -> idioma -> traduccion."""
from traductor.aws.rekognition import detect_text
from traductor.aws.translate import translate_text
from traductor.models.predict import UNKNOWN


def run_pipeline(image_bytes: bytes, target: str, cfg: dict, classifier) -> list[dict]:
    """Procesa una imagen y devuelve, por cada linea detectada, su idioma y su traduccion."""
    region = cfg["aws"]["region"]
    lines = detect_text(image_bytes, region, cfg["aws"]["rekognition"]["min_confidence"])
    results = []
    for line in lines:
        lang, conf = classifier.predict(line)
        if lang == target:
            translated = line  # ya esta en el idioma destino: se evita la llamada a Translate
        else:
            source = cfg["aws"]["translate"]["source_auto"] if lang == UNKNOWN else lang
            translated = translate_text(line, source, target, region)
        results.append(
            {"original": line, "language": lang, "confidence": round(conf, 3), "translation": translated}
        )
    return results

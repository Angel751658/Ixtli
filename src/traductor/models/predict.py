"""Inferencia del clasificador de idioma con umbral de confianza."""
import joblib

UNKNOWN = "unknown"


class LanguageClassifier:
    def __init__(self, artifact_path: str, unknown_threshold: float = 0.6):
        self.model = joblib.load(artifact_path)
        self.threshold = unknown_threshold

    def predict(self, text: str) -> tuple[str, float]:
        """Devuelve (idioma, confianza). Bajo el umbral devuelve ("unknown", confianza)."""
        probs = self.model.predict_proba([text])[0]
        idx = int(probs.argmax())
        conf = float(probs[idx])
        lang = str(self.model.classes_[idx])
        return (lang, conf) if conf >= self.threshold else (UNKNOWN, conf)

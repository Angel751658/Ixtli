"""Métricas Prometheus de servicio e inferencia."""
from prometheus_client import Counter, Histogram

HTTP_REQUESTS = Counter(
    "ixtli_http_requests_total",
    "Solicitudes HTTP procesadas por la API.",
    ("method", "route", "status"),
)
HTTP_REQUEST_DURATION = Histogram(
    "ixtli_http_request_duration_seconds",
    "Duración de las solicitudes HTTP.",
    ("method", "route"),
)
MODEL_PREDICTIONS = Counter(
    "ixtli_model_predictions_total",
    "Predicciones de idioma completadas.",
    ("language",),
)
MODEL_CONFIDENCE = Histogram(
    "ixtli_model_prediction_confidence",
    "Confianza de las predicciones de idioma.",
    ("language",),
    buckets=(0.25, 0.5, 0.6, 0.75, 0.9, 0.95, 0.99, 1.0),
)
MODEL_INFERENCE_DURATION = Histogram(
    "ixtli_model_inference_duration_seconds",
    "Duración de las inferencias del modelo hospedado.",
)
MODEL_PREDICTION_ERRORS = Counter(
    "ixtli_model_prediction_errors_total",
    "Errores al invocar el modelo hospedado.",
)
TRANSLATIONS = Counter(
    "ixtli_translations_total",
    "Resultados de las traducciones solicitadas.",
    ("source_language", "target_language", "result"),
)
TRANSLATION_DURATION = Histogram(
    "ixtli_translation_duration_seconds",
    "Duración de las llamadas al servicio de traducción.",
    ("source_language", "target_language"),
)
TRANSLATION_ERRORS = Counter(
    "ixtli_translation_errors_total",
    "Errores al invocar el servicio de traducción.",
    ("source_language", "target_language"),
)

SUPPORTED_LANGUAGES = frozenset({"auto", "de", "en", "es", "fr", "it", "pt", "unknown"})


def language_label(language: str) -> str:
    """Limita las etiquetas para evitar cardinalidad no acotada en Prometheus."""
    return language if language in SUPPORTED_LANGUAGES else "other"

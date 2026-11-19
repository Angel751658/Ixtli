"""Inferencia del clasificador de idiomas en Amazon SageMaker"""
import joblib
import json
import os

UNKNOWN = "unknown"
UNKNOWN_THRESHOLD = float(os.environ.get("UNKNOWN_THRESHOLD", "0.6"))

# Carga el modelo entrenado desde el directorio de SageMaker
def model_fn(model_dir):
    model_path = os.path.join(model_dir, "language_clf.joblib")
    return joblib.load(model_path)

# Recibe el texto enviado por FastAPI
def input_fn(request_body, content_type):
    if content_type != "application/json":
        raise ValueError("El contenido debe estar en formato JSON")

    data = json.loads(request_body)

    if not isinstance(data, dict):
        raise ValueError("Se esperaba un objeto JSON")

    text = data.get("text")

    if not isinstance(text, str) or not text.strip():
        raise ValueError("Debe proporcionarse un texto válido")

    return text

# Predice el idioma y aplica el umbral de confianza
def predict_fn(text, model):
    probabilities = model.predict_proba([text])[0]

    index = int(probabilities.argmax())
    confidence = float(probabilities[index])
    language = str(model.classes_[index])

    if confidence < UNKNOWN_THRESHOLD:
        language = UNKNOWN

    return {
        "language": language,
        "confidence": round(confidence, 3)
    }

# Convierte el resultado a JSON para devolverlo al cliente
def output_fn(prediction, accept):
    if accept != "application/json":
        raise ValueError("Solo se admite application/json")

    return json.dumps(prediction, ensure_ascii=False), "application/json"
import sys
from pathlib import Path
from code.inference import model_fn, input_fn, predict_fn, output_fn

# Obtener la ruta raíz del proyecto
ROOT = Path(__file__).resolve().parent.parent

# 1. Cargar el modelo
MODEL_DIR = ROOT / "sagemaker" / "model"
model = model_fn(str(MODEL_DIR))

print("Modelo cargado correctamente.")
print("Clases del modelo:", model.classes_)

# 2. Preparar textos de prueba
texts = [
    "Hola, ¿cómo estás?",
    "Good morning, how are you?",
    "Bonjour, comment allez-vous?",
    "Guten Morgen, wie geht es dir?",
    "Buongiorno, come stai?",
    "Bom dia, como você está?"
]

# 3. Probar el proceso completo de inferencia
for text in texts:
    print("\nTexto original:", text)

    # Simular la entrada JSON que recibe SageMaker
    request_body = f'{{"text": "{text}"}}'

    # Procesar la entrada
    processed_text = input_fn(request_body, "application/json")

    # Realizar predicción
    prediction = predict_fn(processed_text, model)

    # Convertir la respuesta a JSON
    response, content_type = output_fn(
        prediction,
        "application/json"
    )

    print("Predicción:", response)
    print("Content-Type:", content_type)
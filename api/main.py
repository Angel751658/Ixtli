import boto3
import json

from botocore.exceptions import ClientError
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from uuid import uuid4

# Crear la API de Ixtli
app = FastAPI(
    title="IXTLI API",
    description="API para el reconocimiento y traducción de texto en imágenes",
    version="1.0.0"
)

# Permitir peticiones de React y Vite (puerto 5173)
allowed_origin = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origin,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Variables de AWS
AWS_REGION = "us-east-1"
BUCKET_NAME = "ixtli-images"
SAGEMAKER_ENDPOINT = "ixtli-model-endpoint"

# Cliente de S3
s3 = boto3.client(
    "s3",
    region_name=AWS_REGION
)

# Cliente de Rekognition
rekognition = boto3.client(
    "rekognition",
    region_name=AWS_REGION
)

# Cliente de SageMaker
sagemaker = boto3.client(
    "sagemaker-runtime",
    region_name=AWS_REGION
)

# Cliente de Translate
translate = boto3.client(
    "translate",
    region_name=AWS_REGION
)

# GET: prueba
@app.get("/")
def inicio():
    return {
        "mensaje": "Bienvenido a la API de IXTLI",
        "estado": "Funcionando correctamente"
    }

# POST: subir imagenes al bucket
@app.post("/images")
async def upload_image(file: UploadFile = File(...)):
    # Tipos de imagenes permitidas
    allow_images = ["image/jpeg", "image/jpg", "image/webp", "image/png"]

    # Si el formato de imagen no esta en la lista...
    if file.content_type not in allow_images:
        raise HTTPException(
            status_code=400,
            detail="Formato de imagen no permitido"
        )

    # Leer el contenido de la imagen
    image_data = await file.read()

    # Si la imagen esta vacia...
    if not image_data:
        raise HTTPException(
            status_code=400,
            detail="La imagen esta vacia..."
        )

    # Comprobar que el tamaño de la imagen sea menor a 10MB
    if len(image_data) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="La imagen es demasiado grande. El límite es de 10MB"
        )

    # Generar un id unico para la imagen
    image_id = str(uuid4())

    # Crear una clave unica para c/imagen de S3
    image_key = f"images/{image_id}"

    # Guardar la imagen dentro de 'ixtli-images' en S3
    try:
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=image_key,
            Body=image_data,
            ContentType=file.content_type
        )

    except ClientError as e:
        raise HTTPException(
            status_code=500,
            detail="No fue posible guardar la imagen en S3"
        )

    return {
        "mensaje": "Imagen guardada en S3",
        "imagen_id": image_id,
        "filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": len(image_data)
    }

# GET: obtener una imagen del bucket
@app.get("/images/{image_id}")
async def get_image(image_id: str):
    # Crear una clave unica para c/imagen de S3
    image_key = f"images/{image_id}"

    # Comprobar si la imagen esta guardada
    try:
        image = s3.get_object(
            Bucket=BUCKET_NAME,
            Key=image_key
        )

    except ClientError as e:
        error = e.response["Error"]["Code"]

        if error in ["NoSuchKey", "404", "NotFound"]:
            raise HTTPException(
                status_code=404,
                detail="Imagen no encontrada"
            )

        raise HTTPException(
            status_code=500,
            detail="No fue posible obtener la imagen"
        )

    return StreamingResponse(
        image["Body"],
        media_type=image["ContentType"]
    )

# GET: obtener todas las imagenes del bucket
@app.get("/images")
async def get_all_images():
    try:
        # Obtener 10 imagenes del bucket
        last_images = s3.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix="images/",
            MaxKeys=5
        )

        # Lista para almacenar la info de las imagenes
        images = []

        for image in last_images.get("Contents", []):
            # Obtener el id de c/imagen
            image_key = image["Key"]
            image_id = image_key.replace("images/", "", 1)

            # Guardar la info de c/imagen
            images.append({
                "image_id": image_id,
                "size_bytes": image["Size"],
                "saved_date": image["LastModified"]
            })

        # Ordenar las imagenes de mas recientes a mas antiguas
        images.sort(
            key=lambda image: image["saved_date"],
            reverse=True
        )

    except ClientError:
        raise HTTPException(
            status_code=500,
            detail="No fue posible obtener las imagenes almacenadas en S3"
        )

    return {
        "confirmacion": "Imagenes obtenidas correctamente",
        "total": len(images),
        "imagenes": images
    }

# DELETE: eliminar una imagen del bucket
@app.delete("/images/{image_id}")
async def delete_image(image_id: str):
    # Crear una clave unica para c/imagen de S3
    image_key = f"images/{image_id}"

    try:
        # Comprobar si existe la imagen
        image = s3.head_object(
            Bucket=BUCKET_NAME,
            Key=image_key
        )

        # Eliminar la imagen
        s3.delete_object(
            Bucket=BUCKET_NAME,
            Key=image_key
        )

    except ClientError as e:
        error = e.response["Error"]["Code"]

        if error in ["NoSuchKey", "404", "NotFound"]:
            raise HTTPException(
                status_code=404,
                detail="Imagen no encontrada"
            )

        raise HTTPException(
            status_code=500,
            detail="No fue posible eliminar la imagen"
        )

    return {
        "mensaje": "Imagen eliminada correctamente",
        "image_id": image_id,
        "size_bytes": image.get("ContentLength")
    }

# Funcion para traducir el texto con Translate (una vez pasado por Rekognition y SageMaker)
def translate_text(text: str, source_language: str, target_language: str):
    # Si el lenguaje inicial y el objetivo son iguales, no se hace nada
    if source_language == target_language:
        return text, source_language

    try:
        # Traducir el texto dado
        response = translate.translate_text(
            Text=text,
            SourceLanguageCode=source_language,
            TargetLanguageCode=target_language
        )

    except ClientError as e:
        error = e.response["Error"]["Code"]

        # Si Translate no cumple con ciertos niveles de confianza, no puede traducir de forma automatica,
        # pero guarda el posible idioma detectado en 'DetectedLanguageCode'
        if error == "DetectedLanguageLowConfidenceException":
            detected_language = e.response.get("DetectedLanguageCode")

            # Si el idioma detectado con baja confianza NO es el idioma al que queremos traducir,
            # volvemos a intentar la traduccion
            if detected_language and detected_language != target_language:
                response = translate.translate_text(
                    Text=text,
                    SourceLanguageCode=detected_language,
                    TargetLanguageCode=target_language
                )

            else:
                # Regresa el lenguaje detectado si este es el mismo que el objetivo o es un valor vacio
                return text, detected_language or "unknown"

        # Si el idioma de origen y el objetivo son pares invalidos
        elif error == "UnsupportedLanguagePairException":
            return error, source_language, target_language

        else:
            raise

    return (
        response["TranslatedText"],
        response["SourceLanguageCode"]
    )

# POST: completar el proceso de traduccion
# s3 -> rekognition -> sagemaker -> translate
@app.post("/images/{image_id}/process")
async def process_image(image_id: str, target_language: str = "es"):
    # Crear una clave unica para c/imagen de S3
    image_key = f"images/{image_id}"

    try:
        # 1. Enviar la imagen de S3 a Rekognition
        response = rekognition.detect_text(
            Image = {
                "S3Object": {
                    "Bucket": BUCKET_NAME,
                    "Name": image_key
                }
            }
        )

    except ClientError as e:
            error = e.response["Error"]["Code"]
    
            if error in ["NoSuchKey", "404", "NotFound"]:
                raise HTTPException(
                    status_code=404,
                    detail="Imagen no encontrada"
                )
    
            raise HTTPException (
                status_code=500,
                detail="No fue posible detectar texto en la imagen"
            )

    # Texto detectado
    text_detected = response.get("TextDetections", [])

    # Filtrar las detecciones de texto para que solo se muestren lineas completas en vez de palabras
    # -> esto se hace mas que nada para evitar repeticion de palabras
    image_detected_text = [
        item["DetectedText"]
        for item in text_detected
        if item["Type"] == "LINE"
    ]

    # Diccionario para guardar el idioma de c/linea
    translated_text = []

    for text in image_detected_text:
        try:
            # 2. Enviar cada linea detectada a SageMaker
            prediction = sagemaker.invoke_endpoint(
                EndpointName=SAGEMAKER_ENDPOINT,
                ContentType="application/json",
                Accept="application/json",
                Body=json.dumps({"text": text}) # se manda el texto detectado como JSON (formato aceptado por SageMaker)
            )

            # Leer la respuesta de SageMaker (JSON -> Python)
            prediction_result = json.loads(
                prediction["Body"].read().decode("utf-8")
            )

            # Guardar el idioma original del texto (segun el modelo de SageMaker)
            source_language = prediction_result["language"]
            confidence = prediction_result["confidence"]

            # Si SageMaker no identifica el idioma original (unknown), utiliza la funcion automatica de Translate
            if source_language == "unknown":
                translate_source = "auto"

            else:
                translate_source = source_language

            # 3. Traducir el texto mediante Translate
            final_text, detected_language = translate_text(
                text,
                translate_source,
                target_language
            )

            # Guardar los resultados de la traduccion
            translated_text.append({
                "texto_original": text,
                "idioma_original": detected_language,
                "confianza": confidence,
                "traducción": final_text
            })

        except ClientError as e:
            print("ERROR DE AWS:")
            print("Código:", e.response["Error"]["Code"])
            print("Mensaje:", e.response["Error"]["Message"])
            print("Respuesta completa:", e.response)

            raise HTTPException(
                status_code=500,
                detail="No fue posible clasificar o traducir el texto"
            )    
    
    return {
        "mensaje": "Texto detectado, clasificado y traducido correctamente",
        "image_id": image_id,
        "idioma_destino": target_language,
        "traducción": translated_text
    }
import boto3

from botocore.exceptions import ClientError
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from uuid import uuid4

# Crear la API de Ixtli
app = FastAPI(
    title="IXTLI API",
    description="API para el reconocimiento y traducción de texto en imágenes",
    version="1.0.0"
)

# Variables de AWS
BUCKET_NAME = "ixtli-images"
AWS_REGION = "us-east-1"

# Cliente de S3 (con boto3)
s3 = boto3.client(
    "s3",
    region_name=AWS_REGION
)

# Cliente de Rekognition
rekognition = boto3.client(
    "rekognition",
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

# POST: completar el proceso de traduccion
# s3 -> rekognition -> sagemaker -> translate
@app.post("/images/{image_id}/process")
async def process_image(image_id: str):
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
    
            raise HTTPException(
                status_code=500,
                detail="No fue posible detectar texto en la imagen"
            )

    # Texto detectado
    text_detected = response.get("TextDetections", [])

    # Filtrar las detecciones de texto para que solo se muestren lineas completas en vez de palabras
    # -> esto se hace mas que nada para evitar repeticion de palabras
    image_detected_text = [
        {
            "texto": item["DetectedText"],
            "confianza": item["Confidence"]
        }
        
        for item in text_detected
        if item["Type"] == "LINE"
    ]
    
    return {
        "mensaje": "Texto detectado",
        "image_id": image_id,
        "texto_detectado": image_detected_text
    }
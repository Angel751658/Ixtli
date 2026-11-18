"""Verificacion de la conexion con AWS: identidad, S3, Rekognition y Translate."""
import time

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from traductor.aws.rekognition import detect_text
from traductor.aws.s3 import upload_image
from traductor.aws.translate import translate_text

OK, FALLO, OMITIDO = "OK", "FALLO", "OMITIDO"


def run_checks(cfg: dict, image_bytes: bytes, sts=None, s3=None, rekognition=None, translate=None):
    """Ejecuta las verificaciones y devuelve una lista de (nombre, estado, detalle, ms)."""
    region = cfg["aws"]["region"]
    bucket = cfg["aws"]["s3_bucket"]
    sts = sts or boto3.client("sts", region_name=region)
    s3 = s3 or boto3.client("s3", region_name=region)
    rekognition = rekognition or boto3.client("rekognition", region_name=region)
    translate = translate or boto3.client("translate", region_name=region)

    resultados = []

    def check(nombre, fn):
        t0 = time.perf_counter()
        try:
            detalle = fn()
            estado = OK
        except (ClientError, BotoCoreError) as e:
            detalle, estado = str(e), FALLO
        resultados.append((nombre, estado, detalle, (time.perf_counter() - t0) * 1000))

    def _s3():
        key = "healthcheck/prueba.jpg"
        upload_image(image_bytes, key, bucket, region, client=s3)
        s3.delete_object(Bucket=bucket, Key=key)
        return f"subida y borrado de s3://{bucket}/{key}"

    def _rekognition():
        minimo = cfg["aws"]["rekognition"]["min_confidence"]
        lineas = detect_text(image_bytes, region, minimo, client=rekognition)
        aviso = "" if lineas else " (0 lineas: la foto podria no tener texto legible)"
        return f"{len(lineas)} lineas detectadas: {lineas[:5]}{aviso}"

    check("Identidad (STS)", lambda: sts.get_caller_identity()["Arn"])
    if bucket:
        check("S3 (subir y borrar)", _s3)
    else:
        resultados.append(("S3 (subir y borrar)", OMITIDO, "S3_BUCKET no esta definido en .env", 0.0))
    check("Rekognition DetectText", _rekognition)
    check("Translate es -> en",
          lambda: translate_text("Salida de emergencia", "es", "en", region, client=translate))
    check("Translate auto -> es",
          lambda: translate_text("Sortie de secours", "auto", "es", region, client=translate))
    return resultados

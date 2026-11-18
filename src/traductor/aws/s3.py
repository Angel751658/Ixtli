"""Almacenamiento de imagenes en Amazon S3."""
import boto3


def upload_image(image_bytes: bytes, key: str, bucket: str, region: str, client=None) -> str:
    """Sube la imagen y devuelve su clave en el bucket."""
    client = client or boto3.client("s3", region_name=region)
    client.put_object(Bucket=bucket, Key=key, Body=image_bytes)
    return key

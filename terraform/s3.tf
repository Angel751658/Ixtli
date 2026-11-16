# Crear el bucket ixtli_images
resource "aws_s3_bucket" "ixtli_images" {
  bucket = "ixtli-images"
  force_destroy = true

  # Tags del proyecto
  tags = local.common_tags
}

# Acceso publico al bucket
resource "aws_s3_bucket_public_access_block" "ixtli_images" {
  bucket = aws_s3_bucket.ixtli_images.id
  
  block_public_acls = true
  block_public_policy = true
  ignore_public_acls = true
  restrict_public_buckets = true
}

# Mensaje de confirmacion
output "mensaje_bucket_creado" {
  description = "Mensaje de confirmacion del bucket"
  value = "El bucket ${aws_s3_bucket.ixtli_images.id} ha sido creado!"
}
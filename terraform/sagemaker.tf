# Configuraciones necesarias para cargar el modelo ML en SageMaker IA
# 1. Crear un rol para que Sagemaker pueda acceder a S3
resource "aws_iam_role" "ixtli_sagemaker_role" {
  name = "ixtli-sagemaker-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # Sagemaker
      {
        Effect = "Allow"
        Principal = {
          Service = "sagemaker.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  description = "Rol para el modelo de SageMaker"

  tags = local.common_tags
}

# Politica que le permite a SageMaker:
# -> leer el modelo desde S3
resource "aws_iam_policy" "ixtli_sagemaker_policy" {
  name = "ixtli-sagemaker-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject"]
      Resource = "${aws_s3_bucket.ixtli_images.arn}/sagemaker/*"
    }]
  })

  tags = local.common_tags
}

# Asociar la politica 'ixtli-sagemaker-policy' con el rol 'ixtli-sagemaker-role'
resource "aws_iam_role_policy_attachment" "role_policy_sagemaker" {
  role       = aws_iam_role.ixtli_sagemaker_role.name
  policy_arn = aws_iam_policy.ixtli_sagemaker_policy.arn
}

# Mensaje de confirmacion
output "mensaje_iam_sagemaker_creado" {
  description = "Mensaje de confirmacion del rol iam para sagamaker"
  value       = "El rol IAM ${aws_iam_role.ixtli_sagemaker_role.id} ha sido creado!"
}

# 2. Seleccionar la version de Scikit-learn (biblioteca utilizada para el modelo)
data "aws_sagemaker_prebuilt_ecr_image" "sklearn" {
  repository_name = "sagemaker-scikit-learn"
  image_tag       = "1.9-0-cpu-py3"
  region          = var.aws_region
}

# 3. Integrar el modelo almacenado en S3 en SageMaker
resource "aws_sagemaker_model" "ixtli_language_classifier" {
  name               = "ixtli-language-classifier"
  execution_role_arn = aws_iam_role.ixtli_sagemaker_role.arn

  primary_container {
    image = data.aws_sagemaker_prebuilt_ecr_image.sklearn.registry_path

    # Antes de integrar el modelo a SageMaker, subir el archivo a S3 (paso 6)
    model_data_url = "s3://${aws_s3_object.sagemaker_model.bucket}/${aws_s3_object.sagemaker_model.key}"

    environment = {
      SAGEMAKER_PROGRAM             = "inference.py"
      SAGEMAKER_SUBMIT_DIRECTORY    = "/opt/ml/model/code"
      SAGEMAKER_CONTAINER_LOG_LEVEL = "20"
      SAGEMAKER_REGION              = var.aws_region
    }
  }

  tags = local.common_tags
}

# Mensaje de confirmacion
output "mensaje_modelo_creado" {
  description = "Mensaje de confirmacion del modelo de sagamaker creado"
  value       = "El modelo ML ${aws_sagemaker_model.ixtli_language_classifier.id} ha sido creado!"
}

# 4. Configurar el endpoint del modelo
resource "aws_sagemaker_endpoint_configuration" "ixtli_model_config" {
  name = "ixtli-model-config"

  production_variants {
    variant_name           = "ixtli-model"
    model_name             = aws_sagemaker_model.ixtli_language_classifier.name
    initial_instance_count = 1
    instance_type          = "ml.m5.large"
  }

  tags = local.common_tags
}

# 5. Crear el endpoint final del modelo
resource "aws_sagemaker_endpoint" "ixtli_model_endpoint" {
  name                 = "ixtli-model-endpoint"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.ixtli_model_config.name

  tags = local.common_tags
}

# Mensaje de confirmacion
output "mensaje_endpoint_creado" {
  description = "Mensaje de confirmacion del endpoint del modelo"
  value       = "El endpoint ${aws_sagemaker_endpoint.ixtli_model_endpoint.id} ha sido creado!"
}

# 6. Subir el modelo ML a S3
resource "aws_s3_object" "sagemaker_model" {
  bucket = aws_s3_bucket.ixtli_images.id
  key    = "sagemaker/model.tar.gz" # ubicacion en S3

  source = "${path.module}/../sagemaker/model.tar.gz" # ubicacion local
  etag   = filemd5("${path.module}/../sagemaker/model.tar.gz")
}
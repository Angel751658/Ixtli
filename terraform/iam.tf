# Rol para EC2
resource "aws_iam_role" "ixtli_role" {
  name = "ixtli-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
        # EC2
        {
            Action = "sts:AssumeRole"
            Effect = "Allow"
            Principal = {
                Service = "ec2.amazonaws.com"
            }
        }
    ]
  })
}

# Politica que le permita a EC2:
# -> crear, guardar y consultar buckets en S3
# -> consultar un modelo ML en Sagemaker
# -> manejo de rekognition (detectar texto en imagenes)
# -> manejo de translate (traducir texto)
resource "aws_iam_role_policy" "ixtli_policy" {
  name = "ixtli-policy"
  role = aws_iam_role.ixtli_role.name

  policy = jsondecode({
    Version = "2012-10-17"

    Statement = [
        # S3: Bucket
        {
            Effect = "Allow"
            Action = ["s3:ListBucket"]
            Resource = aws_s3_bucket.ixtli_images.arn
        },
        
        # S3: Objetos dentro del bucket
        {
            Effect = "Allow"
            Action = [
                "s3:PutObject",
                "s3:GetObject"
            ]
            Resource = "${aws_s3_bucket.ixtli_images.arn}/*"
        },

        # SageMaker IA
        {
            Effect = "Allow"
            Action = ["sagemaker:InvokeEndpoint"]
            Resource = "*"
        },

        # Rekognition
        {
            Effect = "Allow"
            Action = ["rekognition:DetectText"]
            Resource = "*"
        },

        # Translate
        {
            Effect = "Allow"
            Action = ["translate:TranslateText"]
            Resource = "*"
        }
    ]
  })
}

# Asociar el rol de IAM con un perfil
resource "aws_iam_instance_profile" "ixtli_profile" {
  name = "ixtli-profile"
  role = aws_iam_role.ixtli_role.name
}
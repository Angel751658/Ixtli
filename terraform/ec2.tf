# Crear la instancia EC2

# VPC donde desplegar la instancia (default)
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# AMI a utilizar en la instancia
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-kernel-*-x86_64"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Instancia a utilizar
resource "aws_instance" "ixtli_ec2" {
  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"

  subnet_id                   = data.aws_subnets.default.ids[0]
  associate_public_ip_address = true

  vpc_security_group_ids = [
    aws_security_group.ixtli_ec2_sg.id
  ]

  iam_instance_profile = aws_iam_instance_profile.ixtli_profile.name

  key_name = var.ec2_key_name

  root_block_device {
    volume_size           = 8
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  tags = merge(
    local.common_tags,
    { Name = "ixtli-ec2" }
  )
}

# Mensaje de confirmacion
output "mensaje_ec2_creado" {
  description = "Mensaje de confirmacion de la instancia ec2"
  value       = "La instancia EC2 ${aws_instance.ixtli_ec2.id} ha sido creada!"
}
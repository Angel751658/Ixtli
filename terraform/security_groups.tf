# Organizar los puertos de entrada y salidad de la app

resource "aws_security_group" "ixtli_ec2_sg" {
    name        = "ixtli-ec2-sg"
    description = "Security Group for EC2 instance"
    vpc_id      = data.aws_vpc.default.id

    # Entrada: SSH (22)
    ingress {
    description = "SSH access"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    # Solo permite la conexion desde la computadora local (con IP publica)
    cidr_blocks = [var.admin_cidr] 
    }

    # Entrada: HTTP (80)
    ingress {
    description = "HTTP access"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    }

    # Salida: Permitir todo
    egress {
    description = "Allow all traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    }

    # Tags del proyecto
    tags = merge(
    local.common_tags, 
    {Name = "ixtli-ec2-sg"}
    )
}

# Mensaje de confirmacion
output "mensaje_sg_creado" {
  description = "Mensaje de confirmacion del security-group"
  value = "El security-group ${aws_security_group.ixtli_ec2_sg.id} ha sido creado!"
}
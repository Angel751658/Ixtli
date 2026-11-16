# Informacion publica de la instancia en ec2

output "ec2_instance_id" {
  description = "Id of the EC2 instance"
  value = aws_instance.ixtli_ec2.id
}

output "ec2_public_ip" {
  description = "Public IP of EC2 instance"
  value = aws_instance.ixtli_ec2.public_ip
}

output "ec2_public_dns" {
  description = "Public DNS of EC2 instance"
  value       = aws_instance.ixtli_ec2.public_dns
}
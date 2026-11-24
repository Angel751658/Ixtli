# Valores configurables

variable "aws_region" {
  description = "AWS region where Ixtli will be deployed"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "ixtli"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

variable "admin_cidr" {
  description = "Local IP"
  type        = string
  default     = "187.189.36.60/32"
}

variable "ec2_key_name" {
  description = "EC2 key pair"
  type        = string
  default     = "ixtli-key-pair"
}
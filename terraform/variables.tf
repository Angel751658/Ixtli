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

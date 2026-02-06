variable "aws_region" {
  description = "Región de AWS"
  type        = string
  default     = "us-east-1"
}

variable "name_prefix" {
  description = "Prefijo común"
  type        = string
  default     = "getupsoft-stg"
}

variable "domain_name" {
  description = "Dominio público"
  type        = string
}

variable "zone_id" {
  description = "Hosted zone de Route53"
  type        = string
}

variable "kms_key_id" {
  description = "KMS Key para Secrets Manager"
  type        = string
}

variable "db_master_password" {
  description = "Contraseña del usuario maestro"
  type        = string
  sensitive   = true
}

variable "tags" {
  description = "Etiquetas globales"
  type        = map(string)
  default = {
    Project     = "getupsoft"
    Environment = "staging"
  }
}

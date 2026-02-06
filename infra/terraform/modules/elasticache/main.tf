terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

resource "aws_elasticache_subnet_group" "this" {
  name       = "${var.name}-subnet-group"
  subnet_ids = var.subnet_ids
  description = "Subredes privadas para Redis"
  tags        = var.tags
}

resource "aws_elasticache_replication_group" "this" {
  replication_group_id          = var.name
  replication_group_description = "Redis para getupsoft"
  node_type                     = var.node_type
  number_cache_clusters         = var.node_count
  automatic_failover_enabled    = true
  multi_az_enabled              = true
  engine                        = "redis"
  engine_version                = var.engine_version
  port                          = 6379
  parameter_group_name          = var.parameter_group
  subnet_group_name             = aws_elasticache_subnet_group.this.name
  at_rest_encryption_enabled    = true
  transit_encryption_enabled    = true
  security_group_ids            = var.security_group_ids
  maintenance_window            = var.maintenance_window
  tags                          = var.tags
}

output "primary_endpoint" {
  value = aws_elasticache_replication_group.this.primary_endpoint_address
}

output "reader_endpoint" {
  value = aws_elasticache_replication_group.this.reader_endpoint_address
}

locals {
  azs = ["${var.aws_region}a", "${var.aws_region}b"]
}

module "vpc" {
  source              = "../../modules/vpc"
  name                = var.name_prefix
  cidr_block          = "10.30.0.0/16"
  availability_zones  = local.azs
  public_subnets      = ["10.30.0.0/20", "10.30.16.0/20"]
  private_subnets     = ["10.30.32.0/20", "10.30.48.0/20"]
  create_nat_gateway  = true
  tags                = var.tags
}

resource "aws_security_group" "alb" {
  name        = "${var.name_prefix}-alb"
  description = "ALB inbound"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.tags
}

resource "aws_security_group" "api" {
  name        = "${var.name_prefix}-api"
  description = "API Fargate"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description              = "ALB"
    from_port                = 8080
    to_port                  = 8080
    protocol                 = "tcp"
    security_groups          = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.tags
}

resource "aws_security_group" "db" {
  name        = "${var.name_prefix}-db"
  description = "Aurora"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description     = "API"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.api.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.tags
}

resource "aws_security_group" "redis" {
  name        = "${var.name_prefix}-redis"
  description = "Redis"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description     = "API"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.api.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.tags
}

module "acm" {
  source                     = "../../modules/acm"
  domain_name                = var.domain_name
  subject_alternative_names  = ["api.${var.domain_name}", "admin.${var.domain_name}"]
  zone_id                    = var.zone_id
  tags                       = var.tags
}

module "alb" {
  source               = "../../modules/alb"
  name                 = "${var.name_prefix}-alb"
  vpc_id               = module.vpc.vpc_id
  subnet_ids           = module.vpc.public_subnet_ids
  security_group_ids   = [aws_security_group.alb.id]
  certificate_arn      = module.acm.certificate_arn
  tags                 = var.tags
}

module "ecr" {
  source       = "../../modules/ecr"
  repositories = ["getupsoft-api", "getupsoft-nginx"]
  tags         = var.tags
}

module "rds" {
  source              = "../../modules/rds"
  identifier          = "${var.name_prefix}-aurora"
  database_name       = "getupsoft"
  master_username     = "getupsoft"
  master_password     = var.db_master_password
  subnet_ids          = module.vpc.private_subnet_ids
  security_group_ids  = [aws_security_group.db.id]
  tags                = var.tags
}

module "elasticache" {
  source             = "../../modules/elasticache"
  name               = "${var.name_prefix}-redis"
  subnet_ids         = module.vpc.private_subnet_ids
  security_group_ids = [aws_security_group.redis.id]
  tags               = var.tags
}

module "secrets" {
  source     = "../../modules/secrets"
  kms_key_id = var.kms_key_id
  tags       = var.tags
  secrets = {
    api = {
      name        = "${var.name_prefix}/api"
      description = "Credenciales API getupsoft"
      value = {
        DB_URL             = "postgresql+psycopg://getupsoft:${var.db_master_password}@${module.rds.cluster_endpoint}:5432/getupsoft"
        REDIS_URL          = "rediss://${module.elasticache.primary_endpoint}:6379/0"
        JWT_SECRET         = "changeme"
        HMAC_SERVICE_SECRET = "changeme"
      }
    }
  }
}

locals {
  api_container = [{
    name      = "api"
    image     = "${module.ecr.repository_urls["getupsoft-api"]}:latest"
    essential = true
    portMappings = [{
      containerPort = 8080
      hostPort      = 8080
      protocol      = "tcp"
    }]
    environment = [
      { name = "ENVIRONMENT", value = "staging" }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = "/aws/ecs/${var.name_prefix}"
        awslogs-region        = var.aws_region
        awslogs-stream-prefix = "api"
      }
    }
  }]
}

module "ecs" {
  source                = "../../modules/ecs"
  name                  = "${var.name_prefix}-api"
  subnet_ids            = module.vpc.private_subnet_ids
  security_group_ids    = [aws_security_group.api.id]
  container_definitions = local.api_container
  load_balancer = {
    target_group_arn = module.alb.target_group_arn
    container_name   = "api"
    container_port   = 8080
  }
  tags = var.tags
}

module "route53" {
  source        = "../../modules/route53"
  zone_id       = var.zone_id
  record_name   = "api.${var.domain_name}"
  alias_name    = module.alb.lb_dns_name
  alias_zone_id = module.alb.lb_zone_id
}

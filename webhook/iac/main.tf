data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

# IAM Role for ECS Task Execution
module "execution_role" {
  source = "./modules/iam"
  name   = "${var.service_name}-ExecutionRole"

  effect  = "Allow"
  actions = ["sts:AssumeRole"]
  principals = [{
    type        = "Service"
    identifiers = ["ecs-tasks.amazonaws.com"]
  }]

  policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
    "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceAutoscaleRole",
    "arn:aws:iam::aws:policy/CloudWatchFullAccessV2",
    "arn:aws:iam::aws:policy/SecretsManagerReadWrite",
    "arn:aws:iam::aws:policy/AmazonSNSFullAccess"
  ]
}

# IAM Role for ECS Task
module "task_role" {
  source = "./modules/iam"
  name   = "${var.service_name}-TaskRole"

  effect  = "Allow"
  actions = ["sts:AssumeRole"]
  principals = [{
    type        = "Service"
    identifiers = ["ecs-tasks.amazonaws.com"]
  }]

  policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceAutoscaleRole",
    "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
    "arn:aws:iam::aws:policy/CloudWatchFullAccessV2",
    "arn:aws:iam::aws:policy/SecretsManagerReadWrite",
    "arn:aws:iam::aws:policy/AmazonSNSFullAccess"
  ]
}

# Security group for service container
module "service_container_sg" {
  source      = "./modules/security_group"
  name        = "${var.service_name}-ContainerSecurityGroup"
  description = "${var.service_name} Container Security Group"
  vpc_id      = var.vpc
}

# Allow inbound traffic from the load balancer to the container on port container_port
module "service_container_sg_ingress_rule_load_balancer_to_container" {
  source                        = "./modules/vpc_source_security_group_ingress_rule"
  from_port                     = var.container_port
  ip_protocol                   = "tcp"
  to_port                       = var.container_port
  security_group_id             = module.service_container_sg.id[0]
  referenced_security_group_id  = module.load_balancer_sg.id[0]
}

# Allow outbound traffic from the container to anywhere
module "service_container_sg_egress_rule_all" {
  source            = "./modules/vpc_security_group_egress_rule"
  security_group_id = module.service_container_sg.id[0]
  ip_protocol       = -1
  cidr_ipv4         = "0.0.0.0/0"
}

# Security group for load balancer
module "load_balancer_sg" {
  source      = "./modules/security_group"
  name        = "${var.service_name}-LoadBalancerSecurityGroup"
  description = "${var.service_name} Load Balancer Security Group"
  vpc_id      = var.vpc
}

# Allow inbound traffic to the load balancer on load_balancer_port (HTTPS)
module "load_balancer_sg_ingress_rule_https" {
  source            = "./modules/vpc_security_group_ingress_rule"
  cidr_ipv4         = "0.0.0.0/0"  # GitHub webhooks come from internet
  from_port         = var.load_balancer_port
  ip_protocol       = "tcp"
  to_port           = var.load_balancer_port
  security_group_id = module.load_balancer_sg.id[0]
}

# Allow inbound traffic to the load balancer on HTTP port (redirects to HTTPS)
module "load_balancer_sg_ingress_rule_http" {
  source            = "./modules/vpc_security_group_ingress_rule"
  cidr_ipv4         = "0.0.0.0/0"  # GitHub webhooks may come via HTTP
  from_port         = 80
  ip_protocol       = "tcp"
  to_port           = 80
  security_group_id = module.load_balancer_sg.id[0]
}

# Allow outbound traffic from the load balancer to anywhere
module "load_balancer_sg_egress_rule_all" {
  source            = "./modules/vpc_security_group_egress_rule"
  security_group_id = module.load_balancer_sg.id[0]
  ip_protocol       = -1
  cidr_ipv4         = "0.0.0.0/0"
}

# ECR repository for webhook container image
module "ecr" {
  source = "./modules/ecr"
  name   = var.service_name
}

# ECS cluster
module "ecs_cluster" {
  source = "./modules/ecs_cluster"
  name   = "${var.service_name}-Cluster"
}

# Application Load Balancer
module "load_balancer" {
  source          = "./modules/lb"
  name            = "${var.service_name}-LoadBalancer"
  subnets         = [var.subnet_a, var.subnet_b]
  security_groups = [module.load_balancer_sg.id[0]]
  idle_timeout    = 3600
}

# Target group to route HTTP traffic to container port
module "load_balancer_target_group" {
  source   = "./modules/lb_target_group"
  name     = "${var.service_name}-TargetGroup"
  port     = var.container_port
  protocol = "HTTP"
  vpc_id   = var.vpc
  type     = "ip"
  health_check = [{
    interval            = 30
    timeout             = 10
    healthy_threshold   = 2
    unhealthy_threshold = 3
    path                = "/"
  }]
}

# Load balancer listener for HTTPS traffic
module "load_balancer_https_listener" {
  source           = "./modules/lb_listener_forward"
  lb_arn           = module.load_balancer.arn[0]
  port             = var.load_balancer_port
  protocol         = "HTTPS"
  certificate_arn  = var.certificate_arn
  target_group_arn = module.load_balancer_target_group.arn[0]
}

# Load balancer listener for HTTP traffic (redirects to HTTPS)
module "load_balancer_http_listener" {
  source   = "./modules/lb_listener_redirect"
  lb_arn   = module.load_balancer.arn[0]
  port     = 80
  protocol = "HTTP"
  redirect = [{
    port        = var.load_balancer_port
    protocol    = "HTTPS"
    host        = "#{host}"
    path        = "/#{path}"
    query       = "#{query}"
    status_code = "HTTP_301"
  }]
}

# Route53 DNS record
module "route53" {
  source  = "./modules/route53"
  name    = var.dns_name
  records = [module.load_balancer.dns_name[0]]
  zone_id = var.zone_id
}

# ECS Task Definition
module "task_definition" {
  source                   = "./modules/task_definition"
  family                   = "${var.service_name}-TaskDefinition"
  requires_compatibilities = ["FARGATE"]
  memory                   = 512
  cpu                      = 256
  network_mode             = "awsvpc"
  execution_role_arn       = module.execution_role.arn[0]
  task_role_arn            = module.task_role.arn[0]
  
  container_definitions = [{
    name      = "ai-sast-webhook"
    image     = "${var.aws_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.service_name}:latest"
    essential = true
    
    environment = [
      { name = "SNS_TOPIC_ARN", value = var.sns_topic_arn },
      { name = "AI_SAST_DATABRICKS_HOST", value = var.databricks_host },
      { name = "AI_SAST_DATABRICKS_HTTP_PATH", value = var.databricks_http_path },
      { name = "AI_SAST_DATABRICKS_CATALOG", value = var.databricks_catalog },
      { name = "AI_SAST_DATABRICKS_SCHEMA", value = var.databricks_schema },
      { name = "AI_SAST_DATABRICKS_TABLE", value = var.databricks_table }
    ]
    
    portMappings = [{
      containerPort = var.container_port
    }]
    
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-create-group  = "true"
        awslogs-group         = "/ecs/${var.service_name}"
        awslogs-region        = var.aws_region
        awslogs-stream-prefix = "ecs"
      }
    }
  }]
}

# ECS Service
module "ecs_service" {
  source                             = "./modules/ecs_service"
  name                               = var.service_name
  task_definition                    = module.task_definition.arn[0]
  desired_count                      = 1
  cluster                            = module.ecs_cluster.id[0]
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200
  health_check_grace_period_seconds  = 60
  launch_type                        = "FARGATE"
  
  network_configuration = [{
    assign_public_ip = false
    subnets          = [var.subnet_a, var.subnet_b]
    security_groups  = [module.service_container_sg.id[0]]
  }]
  
  load_balancer = [{
    target_group_arn = module.load_balancer_target_group.arn[0]
    container_name   = "ai-sast-webhook"
    container_port   = var.container_port
  }]
}

# Secrets Manager for GitHub webhook secret and Databricks token
module "secrets_manager" {
  source = "./modules/secrets-manager"
}

# SNS Topic for notifications (optional)
module "sns_topic" {
  source     = "./modules/sns"
  name       = "${var.service_name}-SNS-Topic"
  account-id = var.aws_id
}


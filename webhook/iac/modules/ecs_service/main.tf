resource "aws_ecs_service" "this" {
  name            = var.name
  cluster         = var.cluster
  task_definition = var.task_definition
  desired_count   = var.desired_count
  deployment_minimum_healthy_percent = var.deployment_minimum_healthy_percent
  deployment_maximum_percent = var.deployment_maximum_percent
  health_check_grace_period_seconds = var.health_check_grace_period_seconds
  launch_type = var.launch_type

  dynamic "network_configuration" {
    for_each = var.network_configuration
    content {
      subnets = lookup(network_configuration.value, "subnets")
      security_groups = lookup(network_configuration.value, "security_groups")
      assign_public_ip = lookup(network_configuration.value, "assign_public_ip")
    }
  }

  dynamic "load_balancer" {
    for_each = var.load_balancer
    content {
      target_group_arn = lookup(load_balancer.value, "target_group_arn")
      container_name = lookup(load_balancer.value, "container_name")
      container_port = lookup(load_balancer.value, "container_port")
    }
  }
}
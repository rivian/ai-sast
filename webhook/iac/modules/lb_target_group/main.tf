resource "aws_lb_target_group" "this" {
  name     = var.name
  port     = var.port
  protocol = var.protocol
  vpc_id   = var.vpc_id
  target_type = var.type

  dynamic "health_check" {
    for_each = var.health_check
    content {
      interval = lookup(health_check.value, "interval")
      timeout = lookup(health_check.value, "timeout")
      healthy_threshold = lookup(health_check.value, "healthy_threshold")
      unhealthy_threshold = lookup(health_check.value, "unhealthy_threshold")
    }
  }
}
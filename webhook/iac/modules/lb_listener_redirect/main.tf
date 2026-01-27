resource "aws_lb_listener" "this" {
  load_balancer_arn = var.lb_arn
  port              = var.port
  protocol          = var.protocol

  default_action {
    type = "redirect"

    dynamic "redirect" {
      for_each = var.redirect
      content {
        port = lookup(redirect.value, "port")
        protocol = lookup(redirect.value, "protocol")
        status_code = lookup(redirect.value, "status_code")
        host = lookup(redirect.value, "host")
        path = lookup(redirect.value, "path")
        query = lookup(redirect.value, "query")
      }
    }
  }
}
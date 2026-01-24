
resource "aws_lb_listener" "this" {
  load_balancer_arn = var.lb_arn
  port              = var.port
  protocol          = var.protocol
  certificate_arn   = var.certificate_arn

  default_action {
    type = "forward"
    target_group_arn = var.target_group_arn
  }
}

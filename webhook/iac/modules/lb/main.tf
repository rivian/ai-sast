resource "aws_lb" "this" {
  name = var.name
  internal = true
  security_groups = var.security_groups
  subnets = var.subnets
  idle_timeout = var.idle_timeout
}
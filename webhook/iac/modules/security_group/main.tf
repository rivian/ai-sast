resource "aws_security_group" "this" {
  name        = var.name
  description = var.description
  vpc_id = var.vpc_id
}
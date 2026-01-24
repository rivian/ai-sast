output "arn" {
  value = aws_vpc_security_group_ingress_rule.this[*].arn
}

output "this" {
  value = aws_vpc_security_group_ingress_rule.this[*]
}
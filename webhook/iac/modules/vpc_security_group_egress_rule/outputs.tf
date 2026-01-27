output "arn" {
  value = aws_vpc_security_group_egress_rule.this[*].arn
}

output "this" {
  value = aws_vpc_security_group_egress_rule.this[*]
}
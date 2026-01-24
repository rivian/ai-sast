output "arn" {
  value = aws_lb_target_group.this[*].arn
}

output "this" {
  value = aws_lb_target_group.this[*]
}
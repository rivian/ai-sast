output "arn" {
  value = aws_lb_listener.this[*].arn
}

output "this" {
  value = aws_lb_listener.this[*]
}
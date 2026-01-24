output "arn" {
  value = aws_lb.this[*].arn
}

output "this" {
  value = aws_lb.this[*]
}

output "dns_name" {
  value = aws_lb.this[*].dns_name
}
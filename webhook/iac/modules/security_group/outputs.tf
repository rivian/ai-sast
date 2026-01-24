output "arn" {
  value = aws_security_group.this[*].arn
}

output "this" {
  value = aws_security_group.this[*]
}

output "id" {
  value = aws_security_group.this[*].id
}

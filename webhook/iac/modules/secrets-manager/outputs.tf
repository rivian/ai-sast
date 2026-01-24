output "this" {
  value = aws_secretsmanager_secret.this[*]
}

output "id" {
  value = aws_secretsmanager_secret.this[*].id
}

output "arn" {
  value = aws_secretsmanager_secret.this[*].arn
}
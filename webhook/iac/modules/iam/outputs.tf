output "arn" {
  value = aws_iam_role.this[*].arn
}

output "this" {
  value = aws_iam_role.this[*]
}
output "arn" {
  value = aws_ecr_repository.ecr[*].arn
}

output "this" {
  value = aws_ecr_repository.ecr[*]
}
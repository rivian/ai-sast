output "this" {
  value = aws_ecs_service.this[*]
}

output "id" {
  value = aws_ecs_service.this[*].id
}
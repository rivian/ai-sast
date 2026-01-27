output "arn" {
  value = aws_ecs_cluster.this[*].arn
}

output "this" {
  value = aws_ecs_cluster.this[*]
}

output "id" {
  value = aws_ecs_cluster.this[*].id
}
output "arn" {
  value = aws_ecs_task_definition.bruno-TaskDefinition[*].arn
}

output "this" {
  value = aws_ecs_task_definition.bruno-TaskDefinition[*]
}
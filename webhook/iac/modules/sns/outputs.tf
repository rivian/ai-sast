output "arn" {
  value = aws_sns_topic.this[*].arn
}

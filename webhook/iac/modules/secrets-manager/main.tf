resource "aws_secretsmanager_secret" "this" {
  name = "github-webhook-secret"
}
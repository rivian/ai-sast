# Data type for AWS IAM Policy Document
data "aws_iam_policy_document" "iam_policy_document" {
    statement {
        effect = var.effect
        actions = var.actions

        dynamic "principals" {
            for_each = var.principals
            content {
                type = lookup(principals.value, "type")
                identifiers = lookup(principals.value, "identifiers")
            }
        }
    }
}

# Resource for AWS IAM Role
resource "aws_iam_role" "this" {
  name = var.name
  assume_role_policy = data.aws_iam_policy_document.iam_policy_document.json
}

# Resource for attaching managed policies
resource "aws_iam_role_policy_attachment" "iam_policy_attachment" {
    role = aws_iam_role.this.name

    for_each = var.policy_arns
    policy_arn = each.value
}


data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

resource "aws_lambda_function" "this" {
  function_name = "${var.lambda_name}-lambda_function"
  role          = aws_iam_role.this.arn
  package_type  = "Image"
  image_uri     = var.image_uri

  image_config {
    entry_point = ["/lambda-entrypoint.sh"]
    command     = ["app.handler"]
  }

  memory_size = 512
  timeout     = 30

  architectures = ["arm64"] # Graviton support for better price/performance
}

# IAM role for Lambda execution
data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "this" {
  name               = "${var.lambda_name}-lambda_execution_role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

# Attach the basic execution policy to the lambda execution role
resource "aws_iam_role_policy_attachment" "this" {
  role       = aws_iam_role.this.id
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}


# Add policy to the execution role
resource "aws_iam_policy" "this" {
  name = "${var.lambda_name}-sns-notification-policy"
  description = "Policy for the sns notification execution role"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface",
        ],
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:*",
        ]
        Resource = "arn:aws:ecr:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:repository/*"
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Subscribe",
          "sns:Receive",
          "sns:Publish",
          "sns:ListSubscriptionsByTopic",
          "sns:GetTopicAttributes",
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
        ]
        Resource = "*"
      },    
    ]
  })
}

# Attach the policy to the execution role
resource "aws_iam_role_policy_attachment" "custom_policy" {
  role = aws_iam_role.this.id
  policy_arn = aws_iam_policy.this.arn
}

resource "aws_sns_topic" "this" {
  name = var.name
}

resource "aws_sns_topic_policy" "default" {
  arn = aws_sns_topic.this.arn

  policy = data.aws_iam_policy_document.sns_topic_policy.json
}

data "aws_iam_policy_document" "sns_topic_policy" {

  statement {
    actions = [
      "SNS:Subscribe",
      "SNS:Receive",
      "SNS:Publish",
      "SNS:ListSubscriptionsByTopic",
      "SNS:GetTopicAttributes",
    ]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceOwner"

      values = [
        var.account-id,
      ]
    }

    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }

    resources = [
      aws_sns_topic.this.arn,
    ]

    sid = "__default_statement_ID"
  }
}
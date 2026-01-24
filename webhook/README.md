# AI-SAST Webhook Listener

This directory contains the infrastructure and code for the AI-SAST webhook listener, which captures developer feedback from GitHub pull request comments and stores it in Databricks for continuous improvement.

## Overview

The webhook listener is a Flask application deployed on AWS ECS (Fargate) behind an Application Load Balancer. It:

1. Receives webhook events from GitHub when developers interact with AI-SAST bot comments on PRs
2. Verifies the GitHub webhook signature for security
3. Extracts developer feedback (True Positive / False Positive selections)
4. Stores feedback in Databricks for the AI model to learn from
5. Optionally sends SNS notifications for confirmed vulnerabilities

## Architecture

```
GitHub → ALB (HTTPS) → ECS Fargate → Databricks
                ↓
               SNS (optional)
```

### Components

- **Flask Application** (`main.py`): Handles webhook events and processes feedback
- **Dockerfile**: Containerizes the Flask app
- **Terraform IaC** (`iac/`): AWS infrastructure as code
  - ECS Cluster & Service (Fargate)
  - Application Load Balancer with HTTPS
  - Security Groups
  - IAM Roles
  - Route53 DNS
  - ECR Repository
  - Secrets Manager
  - SNS Topic (optional)

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **Domain & SSL Certificate** (ACM) for HTTPS
3. **GitHub Repository** configured with AI-SAST
4. **Databricks Workspace** (optional, for feedback storage)
5. **Terraform** >= 1.0
6. **Docker** for building container images

## Setup Instructions

### 1. Configure GitHub Webhook Secret

Create a secure secret for GitHub webhook verification:

```bash
# Generate a secure random token
WEBHOOK_SECRET=$(openssl rand -hex 32)

# Store it in AWS Secrets Manager
aws secretsmanager create-secret \
  --name github-webhook-secret \
  --secret-string "{\"github-webhook-secret\":\"$WEBHOOK_SECRET\"}"
```

**Save this secret** - you'll need it when configuring the GitHub webhook.

### 2. Configure Databricks Token (Optional)

If using Databricks for feedback storage:

```bash
# Store Databricks access token in Secrets Manager
aws secretsmanager create-secret \
  --name databricks-access-token \
  --secret-string "{\"databricks-access-token\":\"YOUR_DATABRICKS_TOKEN\"}"
```

### 3. Build and Push Docker Image

```bash
cd webhook

# Build the Docker image
docker build -t ai-sast-webhook-listener .

# Tag for ECR
docker tag ai-sast-webhook-listener:latest \
  YOUR_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/ai-sast-webhook-listener:latest

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  YOUR_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Push to ECR
docker push YOUR_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/ai-sast-webhook-listener:latest
```

### 4. Configure Terraform Variables

Create `iac/terraform.tfvars`:

```hcl
# AWS Configuration
aws_id     = "123456789012"
aws_region = "us-east-1"

# Networking
vpc       = "vpc-xxxxxxxxx"
subnet_a  = "subnet-xxxxxxxxx"  # Private subnet 1
subnet_b  = "subnet-xxxxxxxxx"  # Private subnet 2
subnet_c  = "subnet-xxxxxxxxx"  # Private subnet 3

# DNS & SSL
dns_name        = "ai-sast-webhook.yourdomain.com"
zone_id         = "Z1234567890ABC"
certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/xxxxx"

# Databricks Configuration (optional)
databricks_host      = "https://your-workspace.cloud.databricks.com"
databricks_http_path = "/sql/1.0/warehouses/xxxxx"
databricks_catalog   = "your_catalog"
databricks_schema    = "your_schema"
databricks_table     = "vulnerability_feedback"

# SNS Topic (optional, for notifications)
sns_topic_arn = "arn:aws:sns:us-east-1:123456789012:ai-sast-notifications"

# Tags
tags = {
  ProjectOwner = "security-team"
  Customer     = "internal"
  Project      = "ai-sast"
  Environment  = "production"
  Terraform    = true
}
```

### 5. Deploy with Terraform

```bash
cd iac

# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Deploy infrastructure
terraform apply
```

This will create:
- ECR repository
- ECS cluster and Fargate service
- Application Load Balancer
- Security groups with appropriate rules
- Route53 DNS record
- IAM roles with necessary permissions

### 6. Configure GitHub Webhook

After deployment, configure the webhook in your GitHub repository:

1. Go to **Settings** → **Webhooks** → **Add webhook**
2. **Payload URL**: `https://ai-sast-webhook.yourdomain.com/webhook`
3. **Content type**: `application/json`
4. **Secret**: Use the `WEBHOOK_SECRET` you generated in step 1
5. **Events**: Select "Issue comments"
6. **Active**: ✓ Enabled

### 7. Test the Webhook

Create a test PR with AI-SAST comments and try checking the feedback boxes. Monitor the logs:

```bash
# View ECS task logs
aws logs tail /ecs/ai-sast-webhook-listener --follow
```

## How It Works

### 1. Developer Provides Feedback

When AI-SAST posts a comment on a PR with vulnerability findings, it includes interactive checkboxes:

```markdown
🤖 AI-SAST Security Scan Results

**Vulnerability**: SQL Injection
**Severity**: HIGH
**File**: `app/routes.py:45`

Developer Feedback:
- [ ] ✅ True Positive
- [ ] ❌ False Positive
```

### 2. GitHub Sends Webhook

When a developer checks a box (edits the comment), GitHub sends an `issue_comment` webhook to your endpoint.

### 3. Webhook Processes Feedback

The Flask app:
1. Verifies the GitHub signature
2. Parses the comment for checkbox selections
3. Extracts vulnerability details
4. Stores feedback in Databricks

### 4. AI Model Learns

The feedback is used to:
- Reduce false positives in future scans
- Improve detection accuracy
- Build a knowledge base of confirmed vulnerabilities

## Security Considerations

### Authentication & Authorization

- **GitHub Signature Verification**: All webhooks are verified using HMAC-SHA256
- **HTTPS Only**: All traffic is encrypted in transit
- **AWS Secrets Manager**: Sensitive credentials are never hardcoded
- **IAM Roles**: Principle of least privilege

### Network Security

- **Private Subnets**: ECS tasks run in private subnets (no public IP)
- **Security Groups**: Restricted ingress/egress rules
- **ALB**: Public-facing load balancer with WAF-ready setup

### Input Validation

- Sanitization of user input for logging
- Validation of comment structure
- Deduplication to prevent replay attacks

## Troubleshooting

### Webhook Returns 401 Unauthorized

- **Cause**: GitHub signature verification failed
- **Solution**: Verify the webhook secret in AWS Secrets Manager matches the one configured in GitHub

### No Feedback Being Stored

- **Check Databricks Configuration**: Ensure environment variables are correct
- **Check Logs**: Review CloudWatch logs for errors
- **Verify Databricks Token**: Ensure the token has write permissions

### ECS Task Fails to Start

- **Check ECR Image**: Ensure the Docker image is pushed and tagged correctly
- **Check IAM Permissions**: Task role needs Secrets Manager and Databricks access
- **Check Health Check**: Ensure the Flask app responds to `GET /`

### CloudWatch Logs Access

```bash
# List log streams
aws logs describe-log-streams \
  --log-group-name /ecs/ai-sast-webhook-listener

# Tail logs
aws logs tail /ecs/ai-sast-webhook-listener --follow

# Filter for errors
aws logs filter-log-events \
  --log-group-name /ecs/ai-sast-webhook-listener \
  --filter-pattern "ERROR"
```

## Environment Variables

The ECS task uses these environment variables (configured in Terraform):

| Variable | Description | Required |
|----------|-------------|----------|
| `SNS_TOPIC_ARN` | SNS topic for notifications | No |
| `AI_SAST_DATABRICKS_HOST` | Databricks workspace URL | Yes* |
| `AI_SAST_DATABRICKS_HTTP_PATH` | SQL warehouse HTTP path | Yes* |
| `AI_SAST_DATABRICKS_CATALOG` | Unity Catalog name | Yes* |
| `AI_SAST_DATABRICKS_SCHEMA` | Schema name | Yes* |
| `AI_SAST_DATABRICKS_TABLE` | Table name for feedback | Yes* |
| `FLASK_DEBUG` | Enable debug mode (0 or 1) | No |

*Required if using Databricks integration

## Monitoring

### Key Metrics

Monitor these metrics in CloudWatch:

- **HTTP 2xx Responses**: Successful webhook processing
- **HTTP 4xx Responses**: Authentication/validation failures
- **HTTP 5xx Responses**: Application errors
- **Target Healthy Host Count**: ECS task health
- **Request Count**: Webhook volume

### Alarms

Set up CloudWatch alarms for:

- High error rate (5xx responses)
- Unhealthy ECS tasks
- High response latency

## Cost Optimization

- **Fargate Spot**: Consider using Spot instances for non-critical environments
- **Auto Scaling**: Scale down to 0 during off-hours if applicable
- **ALB Idle Timeout**: Configured to 3600s for long-lived connections
- **Log Retention**: Set CloudWatch log retention to 30 days

## Updating the Service

To deploy a new version:

```bash
# Build and push new image
docker build -t ai-sast-webhook-listener:v2 .
docker tag ai-sast-webhook-listener:v2 \
  YOUR_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/ai-sast-webhook-listener:latest
docker push YOUR_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/ai-sast-webhook-listener:latest

# Force new deployment
aws ecs update-service \
  --cluster ai-sast-webhook-listener-Cluster \
  --service ai-sast-webhook-listener \
  --force-new-deployment
```

## Cleanup

To destroy all resources:

```bash
cd iac
terraform destroy
```

**Warning**: This will delete all infrastructure. Ensure you have backups of any data in Databricks.

## Support

For issues or questions:
- Check the [main README](../README.md)
- Review [INTEGRATIONS.md](../INTEGRATIONS.md) for Databricks setup
- Open an issue on GitHub

## License

Apache License 2.0 - See [LICENSE](../LICENSE) for details.


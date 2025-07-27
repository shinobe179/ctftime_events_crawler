# KMS key for Secrets Manager
resource "aws_kms_key" "secrets" {
  description             = "KMS key for Secrets Manager encryption"
  deletion_window_in_days = var.kms_deletion_window_in_days
  enable_key_rotation     = var.enable_key_rotation

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      }
    ]
  })
}

resource "aws_kms_alias" "secrets" {
  name          = "alias/${var.project_prefix}-secrets"
  target_key_id = aws_kms_key.secrets.key_id
}

# Get current AWS account ID
data "aws_caller_identity" "current" {}

# Secrets Manager secret for Slack credentials
resource "aws_secretsmanager_secret" "slack_credentials" {
  name        = "${var.project_prefix}/slack-credentials"
  description = "Slack credentials for CTFTime event notifications"
  kms_key_id  = aws_kms_key.secrets.arn

  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "slack_credentials" {
  secret_id = aws_secretsmanager_secret.slack_credentials.id
  secret_string = jsonencode({
    slack_oauth_token = var.slack_oauth_token
    target_channel_id = var.target_channel_id
  })
}
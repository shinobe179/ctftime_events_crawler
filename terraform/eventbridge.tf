# EventBridge rule for scheduling Lambda function
resource "aws_cloudwatch_event_rule" "schedule" {
  name                = "${var.project_prefix}-schedule"
  description         = "Schedule for CTFTime events crawler Lambda function"
  schedule_expression = var.schedule_expression

  # Use state instead of is_enabled (deprecated)
  state = "ENABLED"
}

# EventBridge target
resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.schedule.name
  target_id = "LambdaFunction"
  arn       = aws_lambda_function.ctftime_events.arn

  # Retry policy
  retry_policy {
    maximum_event_age_in_seconds = 3600  # 1 hour
    maximum_retry_attempts       = 2
  }
}
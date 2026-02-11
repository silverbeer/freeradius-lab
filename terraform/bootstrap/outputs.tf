output "state_bucket_name" {
  description = "S3 bucket name for Terraform state"
  value       = aws_s3_bucket.tfstate.id
}

output "lock_table_name" {
  description = "DynamoDB table name for Terraform state locking"
  value       = aws_dynamodb_table.tflock.name
}

output "init_command" {
  description = "Command to initialize the main Terraform config with this backend"
  value       = "terraform init -backend-config=\"bucket=${aws_s3_bucket.tfstate.id}\" -backend-config=\"dynamodb_table=${aws_dynamodb_table.tflock.name}\""
}

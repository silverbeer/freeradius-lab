output "freeradius_instance_id" {
  description = "EC2 instance ID of the FreeRADIUS server"
  value       = aws_instance.freeradius.id
}

output "freeradius_public_ip" {
  description = "Public IP of the FreeRADIUS server"
  value       = aws_instance.freeradius.public_ip
}

output "rpm_bucket_name" {
  description = "S3 bucket name for RPM artifacts"
  value       = aws_s3_bucket.rpm_artifacts.id
}

output "ssm_connect_command" {
  description = "AWS CLI command to connect via SSM Session Manager"
  value       = "aws ssm start-session --target ${aws_instance.freeradius.id} --region ${var.aws_region}"
}

output "radius_test_config" {
  description = "JSON config object for the test suite (server IP, ports, etc.)"
  value = jsonencode({
    server_ip    = aws_instance.freeradius.public_ip
    auth_port    = 1812
    acct_port    = 1813
    instance_id  = aws_instance.freeradius.id
    region       = var.aws_region
    rpm_bucket   = aws_s3_bucket.rpm_artifacts.id
    architecture = var.instance_architecture
  })
}

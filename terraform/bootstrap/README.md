# Terraform Bootstrap — State Backend & GitHub Actions OIDC

One-time setup to create:
- S3 bucket + DynamoDB table for Terraform remote state
- GitHub Actions OIDC provider + IAM role for CI/CD pipelines

## Prerequisites

- AWS CLI configured with credentials
- Terraform >= 1.5

## Usage

```bash
cd terraform/bootstrap
terraform init
terraform plan
terraform apply
```

## After Apply

### 1. Initialize main Terraform config

The `init_command` output gives you the exact command:

```bash
cd ../          # back to terraform/
$(terraform -chdir=bootstrap output -raw init_command)
```

### 2. Set GitHub Actions variable

Copy the `gha_role_arn` output and set it as a repository variable:

1. Go to repo **Settings** > **Secrets and variables** > **Actions** > **Variables**
2. Create variable `AWS_ROLE_ARN` with the role ARN value

```bash
terraform output -raw gha_role_arn
# Example: arn:aws:iam::123456789012:role/freeradius-lab-gha-role
```

## Teardown

To destroy the bootstrap resources (only after destroying all managed infrastructure):

```bash
cd terraform/bootstrap
terraform destroy
```

**Warning:** Destroying the state bucket will delete all Terraform state history.

# Terraform Bootstrap — State Backend

One-time setup to create the S3 bucket and DynamoDB table used as the Terraform remote backend for the main configuration.

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

The `init_command` output gives you the exact command to initialize the main Terraform config:

```bash
cd ../          # back to terraform/
$(terraform -chdir=bootstrap output -raw init_command)
```

Or manually:

```bash
cd ../
terraform init \
  -backend-config="bucket=freeradius-lab-tfstate-<ACCOUNT_ID>" \
  -backend-config="dynamodb_table=freeradius-lab-tflock"
```

## Teardown

To destroy the state backend (only after destroying all managed resources):

```bash
cd terraform/bootstrap
terraform destroy
```

**Warning:** Destroying the state bucket will delete all Terraform state history.

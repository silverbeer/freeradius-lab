terraform {
  backend "s3" {
    # Bucket and DynamoDB table are passed via -backend-config at init time:
    #   terraform init \
    #     -backend-config="bucket=freeradius-lab-tfstate-<ACCOUNT_ID>" \
    #     -backend-config="dynamodb_table=freeradius-lab-tflock"
    key    = "freeradius-lab/grafana.tfstate"
    region = "us-east-2"
  }
}

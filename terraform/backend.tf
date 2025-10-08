terraform {
  backend "s3" {
    bucket = "my-terraform-state-bucket-3tierapp"  # replace with your bucket name
    key    = "ha-ecommerce-platform/terraform.tfstate"
    region = "ap-south-1"
  }
}

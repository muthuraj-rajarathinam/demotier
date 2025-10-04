#!/bin/bash
# ---------------------------------------
# EC2 User Data Script for 3-Tier App
# Using Terraform template variables
# ---------------------------------------

# Update packages
yum update -y

# Install Docker
amazon-linux-extras install docker -y
service docker start
usermod -a -G docker ec2-user
chkconfig docker on

# Install Git
yum install git -y

# Create app directory
mkdir -p /home/ec2-user/app
cd /home/ec2-user/app

# Pull your 3-tier app from GitHub
git clone https://github.com/<your-username>/three-tier-app.git .

# Export DB credentials from Terraform
export DB_HOST=${db_endpoint}
export DB_USER=${db_user}
export DB_PASS=${db_pass}

# Run backend container
docker build -t backend ./backend
docker run -d -p 8080:8080 \
  -e DB_HOST=$DB_HOST \
  -e DB_USER=$DB_USER \
  -e DB_PASS=$DB_PASS \
  backend

# Run frontend container
docker build -t frontend ./frontend
docker run -d -p 80:80 frontend

echo "3-tier app deployed successfully" > /home/ec2-user/deploy.log

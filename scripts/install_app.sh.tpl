#!/bin/bash
# ---------------------------------------
# EC2 User Data Script for 3-Tier App
# ---------------------------------------

# --- Pre-requisites Setup ---
# Update and install dependencies
echo "Starting system update and dependency installation..."
yum update -y
amazon-linux-extras install docker -y
yum install -y git

# Start Docker
systemctl start docker
systemctl enable docker
# Add ec2-user to the docker group so it can run docker commands without sudo
usermod -a -G docker ec2-user

# --- Application Deployment ---

# Create working directory in the home folder
cd /home/ec2-user
mkdir -p app
cd app

# Clone your GitHub repository
# NOTE: git clone creates the directory (e.g., 3tierapp_aws) but DOES NOT enter it.
git clone https://github.com/muthuraj-rajarathinam/3tierapp_aws.git

# MANDATORY STEP: Change directory into the cloned repository
cd 3tierapp_aws

# Export DB credentials (injected from Terraform)
# These will be available as environment variables for the running containers
export DB_HOST=${db_endpoint}
export DB_USER=${db_user}
export DB_PASS=${db_pass}

echo "Database credentials set. DB_HOST: $DB_HOST"

# ----------------------------
# Backend setup (Port 8080)
# ----------------------------
echo "Setting up backend application..."
cd backend
docker build -t backend-app .
docker run -d --name backend-app \
  -p 8080:8080 \
  -e DB_HOST=$DB_HOST \
  -e DB_USER=$DB_USER \
  -e DB_PASS=$DB_PASS \
  backend-app
cd .. # Move back to the 3tierapp_aws root directory

# ----------------------------
# Frontend setup (Port 80)
# ----------------------------
echo "Setting up frontend application..."
cd frontend
docker build -t frontend-app .
# Assuming the frontend needs to connect to the backend on the host's IP/localhost:8080
# If the frontend needs the backend IP, you might need to adjust the Docker network or use the host IP.
# For simplicity in this script, we assume the frontend is standalone or configured via relative paths.
docker run -d --name frontend-app \
  -p 80:80 \
  frontend-app
cd ..

# ----------------------------
# Finish setup
# ----------------------------
echo "3-tier app deployment script finished on $(date)" > /home/ec2-user/deploy.log
echo "Check ports 80 and 8080."

#!/bin/bash

# Variables
REGION="us-east-1"
ACCOUNT_ID="767397968725"
REPOSITORY_NAME_PREFIX="video-processing-repo-dev"
IMAGE_TAG="latest"

# Determine stage and set ECR URI
if [ "$STAGE" = "production" ]; then
  IMAGE_NAME="${REPOSITORY_NAME_PREFIX}-production"
elif [ "$STAGE" = "staging" ]; then
  IMAGE_NAME="${REPOSITORY_NAME_PREFIX}-staging"
  ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${IMAGE_NAME}:${IMAGE_TAG}"
else
  IMAGE_NAME="${REPOSITORY_NAME_PREFIX}"
fi
  echo "image name: IMAGE_NAME"
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${IMAGE_NAME}:${IMAGE_TAG}"

# Retrieve authentication token and authenticate Docker client
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_URI

# Build Docker image
docker build -t $IMAGE_NAME .

# Tag Docker image
docker tag $IMAGE_NAME:$IMAGE_TAG $ECR_URI

# Push Docker image to ECR
docker push $ECR_URI

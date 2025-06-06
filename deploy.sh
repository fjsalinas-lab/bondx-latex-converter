#!/bin/bash
set -euo pipefail

AWS_REGION="us-east-2"
ECR_REPO_NAME="bondx-latex-converter"
LAMBDA_FUNCTION_NAME="bondx-latex-converter"  # Nombre estático de la función

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REPO_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME"

# Login a ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Crear repositorio ECR si no existe
aws ecr describe-repositories --repository-names $ECR_REPO_NAME --region $AWS_REGION || \
    aws ecr create-repository --repository-name $ECR_REPO_NAME --region $AWS_REGION

# Construir imagen Docker
echo "Construyendo imagen Docker..."
docker build \
    --platform=linux/amd64 \
    --provenance=false \
    -t $ECR_REPO_NAME:latest \
    -t $REPO_URI:latest \
    lambda/

# Push the image
echo "Subiendo imagen a ECR..."
docker push $REPO_URI:latest

# Esperar unos segundos para asegurar que la imagen esté disponible
echo "Esperando que la imagen esté disponible..."
sleep 5

# Actualizar función Lambda
echo "Actualizando función Lambda ($LAMBDA_FUNCTION_NAME)..."
aws lambda update-function-code \
    --function-name $LAMBDA_FUNCTION_NAME \
    --image-uri $REPO_URI:latest \
    --region $AWS_REGION \
    --publish

echo "¡Despliegue completado!" 

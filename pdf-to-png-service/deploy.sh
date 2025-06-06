#!/bin/bash

# Script para deployar el microservicio PDF to PNG (INDEPENDIENTE)

set -e

echo "🚀 Iniciando deploy del microservicio PDF to PNG (INDEPENDIENTE)..."

# Verificar que estamos en el directorio correcto
if [ ! -f "app.py" ]; then
    echo "❌ Error: No se encuentra app.py. Ejecuta este script desde el directorio pdf-to-png-service"
    exit 1
fi

# Verificar que Docker está corriendo
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker no está corriendo"
    exit 1
fi

# Verificar que CDK está instalado
if ! command -v cdk &> /dev/null; then
    echo "❌ Error: CDK no está instalado"
    echo "Instala CDK con: npm install -g aws-cdk"
    exit 1
fi

# Verificar credenciales AWS
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ Error: Credenciales AWS no configuradas"
    echo "Configura AWS CLI con: aws configure"
    exit 1
fi

echo "✅ Verificaciones iniciales completadas"

# Mostrar información de la cuenta AWS
ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
echo "📋 Deployando en cuenta AWS: $ACCOUNT_ID"

# Bootstrap CDK para esta cuenta si es necesario
echo "🔧 Verificando bootstrap de CDK..."
cdk bootstrap

# Synthesizar template
echo "🏗️  Synthesizing CDK template..."
cdk synth

# Deploy
echo "📦 Deploying infrastructure..."
cdk deploy --require-approval never

# Obtener outputs del stack
echo "🔍 Obteniendo información del deployment..."

API_URL=$(aws cloudformation describe-stacks \
    --stack-name BondxPdfToPngStack \
    --query 'Stacks[0].Outputs[?OutputKey==`PdfToPngApiUrl`].OutputValue' \
    --output text 2>/dev/null || echo "")

CONVERT_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name BondxPdfToPngStack \
    --query 'Stacks[0].Outputs[?OutputKey==`PdfToPngConvertEndpoint`].OutputValue' \
    --output text 2>/dev/null || echo "")

HEALTH_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name BondxPdfToPngStack \
    --query 'Stacks[0].Outputs[?OutputKey==`PdfToPngHealthEndpoint`].OutputValue' \
    --output text 2>/dev/null || echo "")

FUNCTION_NAME=$(aws cloudformation describe-stacks \
    --stack-name BondxPdfToPngStack \
    --query 'Stacks[0].Outputs[?OutputKey==`PdfToPngFunctionName`].OutputValue' \
    --output text 2>/dev/null || echo "")

if [ -n "$API_URL" ] && [ -n "$CONVERT_ENDPOINT" ]; then
    echo "✅ Deploy completado exitosamente!"
    echo ""
    echo "📋 Información del deployment:"
    echo "  - Stack Name: BondxPdfToPngStack"
    echo "  - Cuenta AWS: $ACCOUNT_ID"
    echo "  - Región: us-east-2"
    echo "  - API Gateway URL: $API_URL"
    echo "  - Endpoint Conversión: $CONVERT_ENDPOINT"
    echo "  - Endpoint Health Check: $HEALTH_ENDPOINT"
    echo "  - Lambda Function: $FUNCTION_NAME"
    echo ""
    echo "🔧 Configuración para Django settings.py:"
    echo "  PDF_TO_PNG_API_URL = '$CONVERT_ENDPOINT'"
    echo ""
    echo "🧪 Para probar el microservicio:"
    echo ""
    echo "1. Health Check:"
    echo "   curl $HEALTH_ENDPOINT"
    echo ""
    echo "2. Conversión PDF a PNG:"
    echo '   curl -X POST "'$CONVERT_ENDPOINT'" \'
    echo '     -H "Content-Type: application/json" \'
    echo '     -d "{\"pdf_s3_key\": \"path/to/document.pdf\", \"bucket_name\": \"bondx-bucket\"}"'
    echo ""
    echo "📚 Ejemplo de uso desde Python:"
    echo "   import requests"
    echo "   response = requests.post('$CONVERT_ENDPOINT', json={"
    echo "       'pdf_s3_key': 'documents/sample.pdf',"
    echo "       'bucket_name': 'bondx-bucket'"
    echo "   })"
    echo "   print(response.json())"
else
    echo "⚠️  Deploy completado pero no se pudieron obtener todos los outputs"
    echo "Puedes obtenerlos manualmente desde la consola AWS CloudFormation"
    echo "Stack name: BondxPdfToPngStack"
fi

echo ""
echo "🎉 ¡Deploy del microservicio PDF to PNG completado!"
echo "🔍 Este microservicio es COMPLETAMENTE INDEPENDIENTE de tu stack LaTeX existente" 
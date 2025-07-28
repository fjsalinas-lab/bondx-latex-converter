#!/bin/bash

# Script para deployar el microservicio Upload Document (INDEPENDIENTE)

set -e

echo "🚀 Iniciando deploy del microservicio Upload Document (INDEPENDIENTE)..."

# Verificar que estamos en el directorio correcto
if [ ! -f "app.py" ]; then
    echo "❌ Error: No se encuentra app.py. Ejecuta este script desde el directorio upload-document-service"
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
    --stack-name BondxUploadDocumentStack \
    --query 'Stacks[0].Outputs[?OutputKey==`UploadDocumentApiUrl`].OutputValue' \
    --output text 2>/dev/null || echo "")

UPLOAD_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name BondxUploadDocumentStack \
    --query 'Stacks[0].Outputs[?OutputKey==`UploadDocumentUploadEndpoint`].OutputValue' \
    --output text 2>/dev/null || echo "")

HEALTH_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name BondxUploadDocumentStack \
    --query 'Stacks[0].Outputs[?OutputKey==`UploadDocumentHealthEndpoint`].OutputValue' \
    --output text 2>/dev/null || echo "")

FUNCTION_NAME=$(aws cloudformation describe-stacks \
    --stack-name BondxUploadDocumentStack \
    --query 'Stacks[0].Outputs[?OutputKey==`UploadDocumentFunctionName`].OutputValue' \
    --output text 2>/dev/null || echo "")

if [ -n "$API_URL" ] && [ -n "$UPLOAD_ENDPOINT" ]; then
    echo "✅ Deploy completado exitosamente!"
    echo ""
    echo "📋 Información del deployment:"
    echo "  - Stack Name: BondxUploadDocumentStack"
    echo "  - Cuenta AWS: $ACCOUNT_ID"
    echo "  - Región: us-east-2"
    echo "  - API Gateway URL: $API_URL"
    echo "  - Endpoint Upload: $UPLOAD_ENDPOINT"
    echo "  - Endpoint Health Check: $HEALTH_ENDPOINT"
    echo "  - Lambda Function: $FUNCTION_NAME"
    echo ""
    echo "🔧 Configuración para Django settings.py:"
    echo "  UPLOAD_DOCUMENT_API_URL = '$UPLOAD_ENDPOINT'"
    echo ""
    echo "🧪 Para probar el microservicio:"
    echo ""
    echo "1. Health Check:"
    echo "   curl $HEALTH_ENDPOINT"
    echo ""
    echo "2. Upload Document (ejemplo con curl):"
    echo '   curl -X POST "'$UPLOAD_ENDPOINT'" \'
    echo '     -F "file=@/path/to/document.pdf" \'
    echo '     -F "document_type=pagare" \'
    echo '     -F "id_pagare=12345"'
    echo ""
    echo "📚 Ejemplo de uso desde JavaScript:"
    echo "   const formData = new FormData();"
    echo "   formData.append('file', fileInput.files[0]);"
    echo "   formData.append('document_type', 'pagare');"
    echo "   formData.append('id_pagare', '12345');"
    echo "   "
    echo "   fetch('$UPLOAD_ENDPOINT', {"
    echo "     method: 'POST',"
    echo "     body: formData"
    echo "   }).then(response => response.json())"
    echo "     .then(data => console.log(data));"
else
    echo "⚠️  Deploy completado pero no se pudieron obtener todos los outputs"
    echo "Puedes obtenerlos manualmente desde la consola AWS CloudFormation"
    echo "Stack name: BondxUploadDocumentStack"
fi

echo ""
echo "🎉 ¡Deploy del microservicio Upload Document completado!"
echo "🔍 Este microservicio es COMPLETAMENTE INDEPENDIENTE de tu stack LaTeX existente" 
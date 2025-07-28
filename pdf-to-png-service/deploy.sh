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

CONVERT_ASYNC_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name BondxPdfToPngStack \
    --query 'Stacks[0].Outputs[?OutputKey==`PdfToPngConvertAsyncEndpoint`].OutputValue' \
    --output text 2>/dev/null || echo "")

CONVERT_FAST_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name BondxPdfToPngStack \
    --query 'Stacks[0].Outputs[?OutputKey==`PdfToPngConvertFastEndpoint`].OutputValue' \
    --output text 2>/dev/null || echo "")

JOB_STATUS_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name BondxPdfToPngStack \
    --query 'Stacks[0].Outputs[?OutputKey==`PdfToPngJobStatusEndpoint`].OutputValue' \
    --output text 2>/dev/null || echo "")

JOBS_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name BondxPdfToPngStack \
    --query 'Stacks[0].Outputs[?OutputKey==`PdfToPngJobsEndpoint`].OutputValue' \
    --output text 2>/dev/null || echo "")

HEALTH_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name BondxPdfToPngStack \
    --query 'Stacks[0].Outputs[?OutputKey==`PdfToPngHealthEndpoint`].OutputValue' \
    --output text 2>/dev/null || echo "")

FUNCTION_NAME=$(aws cloudformation describe-stacks \
    --stack-name BondxPdfToPngStack \
    --query 'Stacks[0].Outputs[?OutputKey==`PdfToPngFunctionName`].OutputValue' \
    --output text 2>/dev/null || echo "")

JOBS_TABLE_NAME=$(aws cloudformation describe-stacks \
    --stack-name BondxPdfToPngStack \
    --query 'Stacks[0].Outputs[?OutputKey==`JobsTableName`].OutputValue' \
    --output text 2>/dev/null || echo "")

if [ -n "$API_URL" ] && [ -n "$CONVERT_ENDPOINT" ]; then
    echo "✅ Deploy completado exitosamente!"
    echo ""
    echo "📋 Información del deployment:"
    echo "  - Stack Name: BondxPdfToPngStack"
    echo "  - Cuenta AWS: $ACCOUNT_ID"
    echo "  - Región: us-east-2"
    echo "  - API Gateway URL: $API_URL"
    echo "  - Lambda Function: $FUNCTION_NAME"
    echo "  - DynamoDB Table: $JOBS_TABLE_NAME"
    echo ""
    echo "🔗 Endpoints disponibles:"
    echo "  - Health Check: $HEALTH_ENDPOINT"
    echo "  - Conversión Estándar: $CONVERT_ENDPOINT"
    echo "  - Conversión Asíncrona: $CONVERT_ASYNC_ENDPOINT"
    echo "  - Conversión Rápida: $CONVERT_FAST_ENDPOINT"
    echo "  - Estado de Jobs: $JOB_STATUS_ENDPOINT"
    echo "  - Lista de Jobs: $JOBS_ENDPOINT"
    echo ""
    echo "🔧 Configuración para Django settings.py:"
    echo "  PDF_TO_PNG_API_BASE_URL = '$API_URL'"
    echo "  PDF_TO_PNG_CONVERT_ENDPOINT = '$CONVERT_ENDPOINT'"
    echo "  PDF_TO_PNG_ASYNC_ENDPOINT = '$CONVERT_ASYNC_ENDPOINT'"
    echo "  PDF_TO_PNG_FAST_ENDPOINT = '$CONVERT_FAST_ENDPOINT'"
    echo "  PDF_TO_PNG_STATUS_ENDPOINT = '$JOB_STATUS_ENDPOINT'"
    echo "  PDF_TO_PNG_JOBS_ENDPOINT = '$JOBS_ENDPOINT'"
    echo ""
    echo "🧪 Para probar el microservicio:"
    echo ""
    echo "1. Health Check:"
    echo "   curl $HEALTH_ENDPOINT"
    echo ""
    echo "2. Conversión Asíncrona (RECOMENDADO para documentos grandes):"
    echo '   curl -X POST "'$CONVERT_ASYNC_ENDPOINT'" \'
    echo '     -H "Content-Type: application/json" \'
    echo '     -d "{\"pdf_s3_key\": \"documents/cronograma.pdf\", \"bucket_name\": \"bondx-bucket\"}"'
    echo ""
    echo "3. Verificar estado de job (usar job_id del paso anterior):"
    echo '   curl "'$JOB_STATUS_ENDPOINT/JOB_ID_HERE'"'
    echo ""
    echo "4. Conversión Rápida (para documentos pequeños):"
    echo '   curl -X POST "'$CONVERT_FAST_ENDPOINT'" \'
    echo '     -H "Content-Type: application/json" \'
    echo '     -d "{\"pdf_base64\": \"JVBERi0xLjQK...\", \"dpi\": 150}"'
    echo ""
    echo "📚 Ejemplo de uso desde Python (procesamiento asíncrono):"
    echo "   from client.pdf_to_png_client import convert_pdf_to_png_async_and_wait"
    echo "   result = convert_pdf_to_png_async_and_wait("
    echo "       pdf_s3_key='documents/cronograma.pdf',"
    echo "       bucket_name='bondx-bucket',"
    echo "       async_api_endpoint='$CONVERT_ASYNC_ENDPOINT',"
    echo "       status_api_endpoint='$JOB_STATUS_ENDPOINT'"
    echo "   )"
else
    echo "⚠️  Deploy completado pero no se pudieron obtener todos los outputs"
    echo "Puedes obtenerlos manualmente desde la consola AWS CloudFormation"
    echo "Stack name: BondxPdfToPngStack"
fi

echo ""
echo "🎉 ¡Deploy del microservicio PDF to PNG completado!"
echo "🔍 Este microservicio es COMPLETAMENTE INDEPENDIENTE de tu stack LaTeX existente" 
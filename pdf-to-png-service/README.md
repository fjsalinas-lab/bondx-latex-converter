# Microservicio PDF to PNG

Microservicio **completamente independiente** para conversión de archivos PDF a imágenes PNG usando AWS Lambda, API Gateway y pdf2image.

## 🎯 Características

- ✅ **Completamente independiente** - No afecta el stack LaTeX existente
- ✅ **High performance** - Usando pdf2image en Lambda con contenedor Docker
- ✅ **Escalable** - Lambda se escala automáticamente según demanda
- ✅ **Confiable** - Manejo de errores y reintentos automáticos
- ✅ **Flexible** - Soporte para múltiples páginas y configuración de DPI
- ✅ **S3 Integration** - Lee PDFs y guarda PNGs automáticamente en S3

## 🏗️ Arquitectura

```
PDF en S3 → API Gateway → Lambda (pdf2image) → PNGs en S3
```

**Componentes:**
- **Lambda Function**: `bondx-pdf-to-png-converter`
- **API Gateway**: Endpoint REST independiente
- **Stack CloudFormation**: `BondxPdfToPngStack`
- **Container**: Docker con Python 3.11 + poppler-utils

## 🚀 Deploy

### Prerrequisitos

1. AWS CLI configurado
2. Docker Desktop corriendo
3. CDK v2 instalado: `npm install -g aws-cdk`

### Pasos de deploy

```bash
# 1. Navegar al directorio del microservicio
cd pdf-to-png-service

# 2. Instalar dependencias CDK (opcional)
pip install -r requirements.txt

# 3. Deploy completo
chmod +x deploy.sh
./deploy.sh
```

El script automáticamente:
- ✅ Verifica prerrequisitos
- ✅ Hace bootstrap de CDK
- ✅ Construye la imagen Docker
- ✅ Despliega infraestructura
- ✅ Muestra URLs y configuración

## 📡 API

### Endpoint de Conversión

**POST** `/convert`

```json
{
  "pdf_s3_key": "documents/sample.pdf",
  "bucket_name": "bondx-bucket",
  "output_prefix": "converted",
  "dpi": 300,
  "return_base64": false
}
```

**Respuesta exitosa:**
```json
{
  "success": true,
  "total_pages": 3,
  "dpi": 300,
  "source_pdf": "documents/sample.pdf",
  "images": [
    {
      "page": 1,
      "s3_key": "converted/sample_page_1.png",
      "size_bytes": 234567
    },
    {
      "page": 2,
      "s3_key": "converted/sample_page_2.png",
      "size_bytes": 245678
    }
  ]
}
```

### Health Check

**GET** `/health`

```json
{
  "status": "healthy",
  "service": "pdf-to-png"
}
```

## 🔧 Integración con Django

### 1. Agregar configuración en settings.py

```python
# Después del deploy, agregar esta línea con tu URL real:
PDF_TO_PNG_API_URL = 'https://your-api-id.execute-api.us-east-2.amazonaws.com/prod/convert'
```

### 2. Copiar cliente al proyecto Django

```bash
# Copiar el cliente a tu proyecto Django
cp client/pdf_to_png_client.py /path/to/your/django/project/
```

### 3. Usar en textract_service.py

```python
from .pdf_to_png_client import convert_pdf_to_png_via_microservice
from django.conf import settings

# En lugar de _pdf_to_png_all_pages(), usar:
def convert_pdf_via_microservice(pdf_s3_key, bucket_name):
    png_keys = convert_pdf_to_png_via_microservice(
        pdf_s3_key=pdf_s3_key,
        bucket_name=bucket_name,
        api_endpoint=settings.PDF_TO_PNG_API_URL,
        output_prefix="processed_documents",
        dpi=300
    )
    return png_keys
```

## 🧪 Testing

### Test directo con curl

```bash
# Health check
curl https://your-api-id.execute-api.us-east-2.amazonaws.com/prod/health

# Conversión
curl -X POST https://your-api-id.execute-api.us-east-2.amazonaws.com/prod/convert \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_s3_key": "documents/test.pdf",
    "bucket_name": "bondx-bucket"
  }'
```

### Test con Python

```python
from client.pdf_to_png_client import PdfToPngClient

client = PdfToPngClient("https://your-api-id.execute-api.us-east-2.amazonaws.com/prod/convert")

result = client.convert_pdf_to_png(
    pdf_s3_key="documents/test.pdf",
    bucket_name="bondx-bucket",
    output_prefix="test-output",
    dpi=300
)

print(f"Converted {result['total_pages']} pages")
for img in result['images']:
    print(f"Page {img['page']}: {img['s3_key']}")
```

## 🔍 Monitoreo

### CloudWatch Logs

```bash
# Ver logs de la función Lambda
aws logs tail /aws/lambda/bondx-pdf-to-png-converter --follow
```

### Métricas importantes

- **Duration**: Tiempo de conversión
- **Errors**: Errores de la función
- **Throttles**: Limitaciones de concurrencia
- **MemoryUtilization**: Uso de memoria

## 🎛️ Configuración

### Parámetros del Lambda

- **Memory**: 1536 MB (ajustable según PDFs)
- **Timeout**: 5 minutos
- **Runtime**: Python 3.11 (Container)

### Variables de entorno

- `BUCKET_NAME`: Bucket S3 por defecto

## 🔧 Troubleshooting

### Error común: "poppler not found"

**Solución**: El Dockerfile ya incluye poppler-utils, pero si aparece este error:

```dockerfile
# Verificar que esta línea esté en el Dockerfile:
RUN yum install -y poppler-utils
```

### Error: "Memory exceeded"

**Solución**: Aumentar memoria del Lambda en `pdf_to_png_stack.py`:

```python
memory_size=2048,  # Cambiar de 1536 a 2048
```

### Error: "Timeout"

**Solución**: Aumentar timeout para PDFs grandes:

```python
timeout=Duration.minutes(10),  # Cambiar de 5 a 10 minutos
```

## 🗑️ Cleanup

Para eliminar completamente el microservicio:

```bash
cd pdf-to-png-service
cdk destroy
```

## 🔗 Enlaces útiles

- [pdf2image Documentation](https://pdf2image.readthedocs.io/)
- [AWS Lambda Container Images](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html)
- [CDK Python Reference](https://docs.aws.amazon.com/cdk/api/v2/python/)

---

## 🎉 ¡Ya está listo!

El microservicio está **completamente separado** de tu stack LaTeX existente y listo para usar. Solo necesitas:

1. ✅ Hacer el deploy con `./deploy.sh`
2. ✅ Copiar la URL del endpoint 
3. ✅ Agregarla a tu Django settings
4. ✅ Integrar el cliente en tu código

**¡No hay riesgo de afectar tu aplicación existente!** 🛡️ 
# 🚀 BondX LaTeX to Word/PDF Converter

> **Microservicio empresarial para convertir documentos LaTeX a Word y PDF de alta calidad usando AWS Lambda**

[![AWS](https://img.shields.io/badge/AWS-Lambda%20%7C%20API%20Gateway-orange)](https://aws.amazon.com)
[![Docker](https://img.shields.io/badge/Docker-Container%20Ready-blue)](https://docker.com)
[![Python](https://img.shields.io/badge/Python-3.11-green)](https://python.org)
[![Pandoc](https://img.shields.io/badge/Pandoc-3.1.11-red)](https://pandoc.org)

---

## 📋 Tabla de Contenidos

- [🎯 ¿Qué es BondX LaTeX Converter?](#-qué-es-bondx-latex-converter)
- [🏗️ ¿Qué es Infrastructure as Code (IAC)?](#️-qué-es-infrastructure-as-code-iac)
- [🚀 Despliegue Rápido (5 minutos)](#-despliegue-rápido-5-minutos)
- [⚡ Endpoints Disponibles](#-endpoints-disponibles)
- [💻 Integración con tu Aplicación](#-integración-con-tu-aplicación)
- [🔧 Configuración Avanzada](#-configuración-avanzada)
- [📊 Monitoreo](#-monitoreo)
---

## 🎯 ¿Qué es BondX LaTeX Converter?

**BondX LaTeX Converter** es un microservicio serverless que convierte documentos LaTeX (.tex) a documentos Word (DOCX) y PDF de alta calidad de manera automática, escalable y confiable.

### ✨ **Características principales:**
- **🚀 Serverless**: Usa AWS Lambda, solo pagas por lo que usas
- **📈 Auto-escalable**: Maneja desde 1 hasta 1000+ conversiones simultáneas
- **🔒 Seguro**: Encriptación completa y acceso controlado
- **⚡ Rápido**: Conversiones en segundos usando Pandoc optimizado
- **💰 Económico**: Sin servidores que mantener, costos variables
- **🎨 Estilos personalizados**: Aplica formatos específicos con filtros Lua

### 🏢 **Perfecto para:**
- **Académico**: Conversión de papers y tesis LaTeX a Word para revisión
- **Editorial**: Preparación de manuscritos para diferentes formatos
- **Corporativo**: Documentos técnicos LaTeX a formatos empresariales
- **Legal**: Contratos y documentos legales con formato consistente

### 🛠️ **Tecnologías utilizadas:**
- **Pandoc 3.1.11**: Motor de conversión LaTeX→DOCX
- **LibreOffice**: Conversión DOCX→PDF (opcional)
- **Filtros Lua**: Personalización de estilos y formato
- **Docker**: Contenedor optimizado para Lambda
- **python-magic**: Detección automática de tipos de archivo

---

## 🏗️ ¿Qué es Infrastructure as Code (IAC)?

**Infrastructure as Code (IAC)** es la práctica de definir y gestionar tu infraestructura de nube usando código en lugar de configuraciones manuales.

### 🎁 **Ventajas del IAC:**
- **🔄 Reproducible**: Mismo resultado siempre
- **📝 Versionado**: Control de cambios como en cualquier código
- **🚀 Rápido**: Deploy automático en minutos
- **🛡️ Confiable**: Sin errores humanos
- **💰 Económico**: Solo recursos necesarios

### 🛠️ **En este proyecto usamos:**
- **AWS CDK (Cloud Development Kit)**: Framework para definir infraestructura con Python
- **Docker**: Contenedores con Pandoc y LibreOffice preinstalados
- **CloudFormation**: AWS despliega automáticamente los recursos
- **ECR**: Registro de contenedores para imágenes Docker

**¿Qué significa esto para ti?** Con un solo comando (`./deploy.sh`) tendrás toda la infraestructura lista y funcionando.

---

## 🚀 Despliegue Rápido (5 minutos)

### 📋 **Prerrequisitos**
```bash
# 1. AWS CLI configurado
aws configure
# Necesitas: Access Key ID, Secret Access Key, Region (ej: us-east-2)

# 2. Docker corriendo
docker --version

# 3. CDK instalado
npm install -g aws-cdk

# 4. Python 3.11+
python3 --version

# 5. Bucket S3 existente (el código asume 'bondx-bucket')
aws s3 ls s3://bondx-bucket  # Verificar que existe
```

### ⚡ **Deploy en 3 comandos**
```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/bondx-latex-converter.git
cd bondx-latex-converter

# 2. Activar el entorno virtual e instalar dependencias
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Deploy completo (infraestructura + aplicación)
cdk deploy  # Despliega la infraestructura
./deploy.sh  # Despliega la aplicación Lambda
```

### 🎯 **Resultado esperado:**
```
✅ Stack desplegado exitosamente!

📡 Tu API está lista en:
https://abc123.execute-api.us-east-2.amazonaws.com/prod

🔧 Recursos creados en AWS:
- Lambda Function: bondx-latex-converter
- API Gateway: latex-converter-api  
- ECR Repository: bondx-latex-converter
- S3 Permissions: Configurados automáticamente

💰 Costo estimado: $0.00/mes (solo pagas por uso)
```

---

## ⚡ Endpoints Disponibles

### 1. **🔄 Conversión de LaTeX a DOCX/PDF** 
**POST** `/convert`

**El endpoint principal** que convierte tus archivos LaTeX a Word y opcionalmente a PDF.

```bash
curl -X POST https://tu-api-url/prod/convert \
  -H "Content-Type: application/json" \
  -d '{
    "input_key": "documentos/mi-paper.tex",
    "bucket_name": "bondx-bucket",
    "output_prefix": "convertidos",
    "generate_pdf": true
  }'
```

**Parámetros:**
- **input_key** (requerido): Ruta del archivo LaTeX en S3
- **bucket_name** (opcional): Bucket S3, usa 'bondx-bucket' por defecto
- **output_prefix** (opcional): Prefijo para archivos de salida, usa 'converted' por defecto
- **generate_pdf** (opcional): true/false para generar PDF adicional

**Respuesta exitosa:**
```json
{
  "docx_key": "convertidos/mi-paper.docx",
  "pdf_key": "convertidos/mi-paper.pdf"
}
```

**Respuesta solo DOCX:**
```json
{
  "docx_key": "convertidos/mi-paper.docx"
}
```

### 2. **🔍 Características del procesamiento**

**Estilos automáticos aplicados:**
- **`.center`**: Texto centrado con estilo "Centered"
- **`.headerblock`**: Bloques de encabezado con estilo "HeaderLeft"  
- **`.summary`**: Resúmenes con estilo "Summary"
- **Documento de referencia**: Aplica formatos predefinidos desde `reference.docx`

**Formatos soportados de entrada:**
- Archivos LaTeX (.tex)
- Texto plano con sintaxis LaTeX
- Documentos con encoding UTF-8

**Formatos de salida:**
- **DOCX**: Microsoft Word (siempre generado)
- **PDF**: Adobe PDF (opcional, vía LibreOffice)

---

## 💻 Integración con tu Aplicación

### 🐍 **Python/Django**

#### 1. **Cliente Python básico**
```python
import requests
import json

def convert_latex_to_word(latex_s3_key, bucket_name="bondx-bucket", generate_pdf=False):
    """
    Convertir LaTeX a DOCX/PDF usando el microservicio.
    
    Args:
        latex_s3_key: Ruta del archivo LaTeX en S3
        bucket_name: Bucket S3 donde está el archivo
        generate_pdf: Si generar PDF adicional
        
    Returns:
        Dict con las rutas de los archivos generados
    """
    API_URL = "https://tu-api-url.execute-api.us-east-2.amazonaws.com/prod/convert"
    
    payload = {
        "input_key": latex_s3_key,
        "bucket_name": bucket_name,
        "output_prefix": "documentos_convertidos",
        "generate_pdf": generate_pdf
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=300)  # 5 min timeout
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ DOCX generado: {result['docx_key']}")
        
        if 'pdf_key' in result:
            print(f"✅ PDF generado: {result['pdf_key']}")
            
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error en la conversión: {e}")
        raise

# Ejemplo de uso
if __name__ == "__main__":
    result = convert_latex_to_word(
        latex_s3_key="papers/mi-tesis.tex",
        bucket_name="bondx-bucket",
        generate_pdf=True
    )
    
    # Descargar los archivos convertidos
    print(f"Archivo Word: {result['docx_key']}")
    print(f"Archivo PDF: {result['pdf_key']}")
```

#### 2. **Integración en Django**
```python
# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def convert_document(request):
    """Vista para convertir documentos LaTeX subidos por usuarios."""
    if request.method == 'POST':
        data = json.loads(request.body)
        latex_file_key = data.get('latex_file_key')
        
        try:
            # Usar el cliente del microservicio
            result = convert_latex_to_word(
                latex_s3_key=latex_file_key,
                generate_pdf=True
            )
            
            return JsonResponse({
                'success': True,
                'docx_url': f"https://bondx-bucket.s3.amazonaws.com/{result['docx_key']}",
                'pdf_url': f"https://bondx-bucket.s3.amazonaws.com/{result['pdf_key']}"
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
```

### 🌐 **Node.js/JavaScript**
```javascript
const axios = require('axios');

async function convertLatexToWord(latexS3Key, bucketName = 'bondx-bucket', generatePdf = false) {
    const API_URL = 'https://tu-api-url.execute-api.us-east-2.amazonaws.com/prod/convert';
    
    try {
        const response = await axios.post(API_URL, {
            input_key: latexS3Key,
            bucket_name: bucketName,
            output_prefix: 'converted_docs',
            generate_pdf: generatePdf
        }, {
            timeout: 300000  // 5 minutos
        });
        
        console.log(`✅ DOCX generado: ${response.data.docx_key}`);
        
        if (response.data.pdf_key) {
            console.log(`✅ PDF generado: ${response.data.pdf_key}`);
        }
        
        return response.data;
        
    } catch (error) {
        console.error('❌ Error:', error.response?.data || error.message);
        throw error;
    }
}

// Uso con async/await
async function procesarDocumento() {
    try {
        const result = await convertLatexToWord(
            'academic/mi-paper.tex',
            'bondx-bucket', 
            true  // Generar PDF
        );
        
        return {
            wordUrl: `https://bondx-bucket.s3.amazonaws.com/${result.docx_key}`,
            pdfUrl: `https://bondx-bucket.s3.amazonaws.com/${result.pdf_key}`
        };
    } catch (error) {
        console.error('Error procesando documento:', error);
        throw error;
    }
}
```

### 🔌 **Cualquier lenguaje (REST API)**
```bash
# Conversión básica (solo DOCX)
curl -X POST https://tu-api-url/prod/convert \
  -H "Content-Type: application/json" \
  -d '{
    "input_key": "academic/mi-tesis.tex",
    "bucket_name": "bondx-bucket",
    "output_prefix": "tesis_convertida"
  }'

# Conversión completa (DOCX + PDF)
curl -X POST https://tu-api-url/prod/convert \
  -H "Content-Type: application/json" \
  -d '{
    "input_key": "academic/mi-tesis.tex",
    "bucket_name": "bondx-bucket",
    "output_prefix": "tesis_convertida",
    "generate_pdf": true
  }'
```

---

## 🔧 Configuración Avanzada

### ⚙️ **Variables de entorno**

Puedes configurar el comportamiento del microservicio editando `bondx_latex_converter_stack.py`:

```python
# En la definición de la Lambda
environment={
    "BUCKET_NAME": storage_bucket.bucket_name,
    "DEFAULT_OUTPUT_PREFIX": "converted",     # Prefijo por defecto
    "MAX_FILE_SIZE_MB": "50",                # Tamaño máximo de archivo
    "ENABLE_DEBUG_LOGS": "true"              # Logs detallados
}
```

### 🎛️ **Configuración de recursos**

Para documentos muy grandes o complejos, puedes aumentar los recursos:

```python
# En bondx_latex_converter_stack.py
latex_function = _lambda.DockerImageFunction(
    self, "LatexConverterFunction",
    memory_size=3008,                    # 3GB de memoria (máximo)
    timeout=Duration.minutes(15),        # 15 minutos máximo
    ephemeral_storage_size=Size.gibibytes(10)  # 10GB de almacenamiento temporal
)
```


#### **Actualizar documento de referencia**:
- Modifica `lambda/reference.docx` con tus estilos corporativos
- Define los estilos: "Centered", "HeaderLeft", "Summary", etc.
- Incluye fuentes, colores y formato de párrafo deseados

### 🔐 **Configuración de buckets S3**

```python
# Agregar más buckets en el stack
additional_bucket = s3.Bucket.from_bucket_name(
    self, "AdditionalBucket",
    bucket_name="mi-bucket-corporativo"
)
additional_bucket.grant_read_write(latex_function)
```


## 📊 Monitoreo

### 🔍 **CloudWatch Logs**
```bash
# Ver logs en tiempo real
aws logs tail /aws/lambda/bondx-latex-converter --follow

# Ver logs de errores específicos
aws logs filter-log-events \
  --log-group-name /aws/lambda/bondx-latex-converter \
  --filter-pattern "ERROR"

# Ver métricas de duración
aws logs filter-log-events \
  --log-group-name /aws/lambda/bondx-latex-converter \
  --filter-pattern "Duration:"
```





### 🔧 **Comandos útiles para debugging**

```bash
# Ver estado del stack
cdk list
cdk describe BondxLatexConverterStack

# Ver diferencias antes de deploy
cdk diff

# Rebuild y redeploy completo
./deploy.sh

# Ver logs específicos de un request
aws logs filter-log-events \
  --log-group-name /aws/lambda/bondx-latex-converter \
  --start-time $(date -d '10 minutes ago' +%s)000 \
  --filter-pattern "Starting handler"

# Verificar que la función está actualizada
aws lambda get-function --function-name bondx-latex-converter \
  --query 'Configuration.[LastModified,CodeSha256]'

# Test directo de la función
aws lambda invoke \
  --function-name bondx-latex-converter \
  --payload file://test-payload.json \
  response.json
```

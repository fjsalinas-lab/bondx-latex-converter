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

### 🎨 **Personalizar estilos LaTeX**

#### 1. **Modificar el filtro Lua** (`lambda/centered.lua`):
```lua
function Div(el)
  -- Agregar nuevo estilo para ecuaciones
  if el.classes and el.classes[1] == "equation" then
    el.attributes["custom-style"] = "EquationStyle"
    return el
  end
  
  -- Estilo para código
  if el.classes and el.classes[1] == "code" then
    el.attributes["custom-style"] = "CodeBlock"
    return el
  end
  
  return el
end

-- Función para personalizar tablas
function Table(el)
  el.attributes["custom-style"] = "CustomTable"
  return el
end
```

#### 2. **Actualizar documento de referencia**:
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

### 🚀 **Optimización para diferentes tipos de documentos**

```python
# Variables específicas por tipo de documento
DOCUMENT_CONFIGS = {
    "academic": {
        "memory_size": 2048,
        "timeout_minutes": 5,
        "pandoc_args": ["--bibliography", "--citeproc"]
    },
    "corporate": {
        "memory_size": 1024,
        "timeout_minutes": 3,
        "pandoc_args": ["--toc", "--number-sections"]
    }
}
```

---

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

### 📈 **Métricas importantes**
- **Duration**: Tiempo de conversión (target: <60s para documentos típicos)
- **Errors**: Errores de conversión (target: <2%)
- **Invocations**: Número de conversiones
- **Memory Usage**: Uso de memoria (target: <80% de lo asignado)
- **Throttles**: Limitación de concurrencia (should be 0)

### 🚨 **Alertas recomendadas**

Configurar en CloudWatch:

```python
# En el stack CDK
error_alarm = cloudwatch.Alarm(
    self, "LatexConverterErrors",
    metric=latex_function.metric_errors(),
    threshold=5,
    evaluation_periods=2,
    alarm_description="Muchos errores en conversión LaTeX"
)

duration_alarm = cloudwatch.Alarm(
    self, "LatexConverterDuration",
    metric=latex_function.metric_duration(),
    threshold=Duration.minutes(2),
    evaluation_periods=2,
    alarm_description="Conversiones muy lentas"
)
```

### 📊 **Dashboard personalizado**
```python
dashboard = cloudwatch.Dashboard(
    self, "LatexConverterDashboard",
    dashboard_name="LaTeX-Converter-Metrics"
)

dashboard.add_widgets(
    cloudwatch.GraphWidget(
        title="Conversiones por hora",
        left=[latex_function.metric_invocations()]
    ),
    cloudwatch.GraphWidget(
        title="Duración promedio",
        left=[latex_function.metric_duration()]
    )
)
```

---

## 💰 Costos

### 💵 **Estructura de costos AWS**

| Componente | Costo | Descripción |
|------------|-------|-------------|
| **Lambda** | $0.0000166667/GB-segundo | Solo cuando convierte |
| **API Gateway** | $3.50/millón requests | Por llamada |
| **S3** | $0.023/GB/mes | Almacenamiento |
| **ECR** | $0.10/GB/mes | Imágenes Docker |

### 📊 **Ejemplos reales de uso**

| Volumen mensual | Archivos promedio | Costo estimado | Equivale a |
|----------------|------------------|----------------|------------|
| **50 documentos** | 10 páginas c/u | ~$3/mes | 1 café ☕ |
| **500 documentos** | 15 páginas c/u | ~$18/mes | 1 almuerzo 🍕 |
| **2,000 documentos** | 20 páginas c/u | ~$65/mes | 1 cena 🍽️ |

**Factores que afectan el costo:**
- **Tamaño del documento**: Más páginas = más tiempo de procesamiento
- **Complejidad**: Ecuaciones y tablas requieren más memoria
- **Generación de PDF**: Proceso adicional con LibreOffice
- **Almacenamiento**: Archivos convertidos en S3

**Sin conversiones = $0** - Solo pagas por lo que usas.

---

## 🆘 Solución de Problemas

### ❌ **Errores comunes**

#### 1. **"LaTeX file not found in S3"**
```bash
# Verificar que el archivo existe
aws s3 ls s3://bondx-bucket/documentos/mi-archivo.tex

# Verificar permisos de lectura
aws s3api head-object --bucket bondx-bucket --key documentos/mi-archivo.tex
```

#### 2. **"Invalid file type detected"**
```bash
# El archivo debe ser texto plano
file mi-archivo.tex
# Output esperado: mi-archivo.tex: UTF-8 Unicode text

# Convertir encoding si es necesario
iconv -f ISO-8859-1 -t UTF-8 mi-archivo.tex > mi-archivo-utf8.tex
```

#### 3. **"Error al generar DOCX" - Pandoc failure**
```bash
# Verificar sintaxis LaTeX localmente
pandoc mi-archivo.tex -o test.docx --from=latex --to=docx
```

**Problemas comunes de LaTeX:**
- **Caracteres especiales no escapados**: `$`, `%`, `&`, `#`
- **Paquetes no soportados**: Pandoc no soporta todos los paquetes LaTeX
- **Encoding incorrecto**: Usar UTF-8 siempre
- **Comandos personalizados**: Definir antes de usar

#### 4. **"Timeout" - Función excede 5 minutos**
```python
# Aumentar timeout en bondx_latex_converter_stack.py
timeout=Duration.minutes(15),
memory_size=3008,  # También aumentar memoria
```

#### 5. **"Error al generar PDF" - LibreOffice failure**
- El PDF se genera desde el DOCX, así que primero verificar que el DOCX esté bien
- LibreOffice a veces falla con documentos muy complejos
- Alternativa: usar el DOCX y convertir externamente

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

### 🧪 **Archivo de prueba** (`test-payload.json`):
```json
{
  "body": "{\"input_key\": \"test/sample.tex\", \"bucket_name\": \"bondx-bucket\", \"generate_pdf\": false}",
  "isBase64Encoded": false
}
```

---

## 🎯 Casos de Uso Reales

### 🎓 **Sector Académico**
```python
# Convertir tesis de LaTeX a Word para revisión de asesores
def procesar_tesis(latex_file):
    result = convert_latex_to_word(
        latex_s3_key=latex_file,
        bucket_name="tesis-universitarias",
        generate_pdf=True  # Versión final en PDF
    )
    
    # Notificar al asesor que la versión Word está lista
    send_email_to_advisor(
        word_url=f"https://s3.amazonaws.com/tesis-universitarias/{result['docx_key']}",
        student_name="Juan Pérez"
    )
    
    return result
```

### 📖 **Editorial y Publicaciones**
```python
# Pipeline de conversión para manuscritos
def preparar_manuscrito_para_revision(author_latex):
    """Convierte LaTeX de autor a Word para editores."""
    
    # 1. Conversión inicial
    result = convert_latex_to_word(
        latex_s3_key=f"manuscripts/{author_latex}",
        bucket_name="editorial-bucket",
        generate_pdf=False  # Solo Word para revisión
    )
    
    # 2. Aplicar estilos editoriales específicos
    apply_editorial_styles(result['docx_key'])
    
    # 3. Enviar a revisores
    distribute_to_reviewers(result['docx_key'])
    
    return result
```

### 🏢 **Corporativo - Documentación Técnica**
```python
# Convertir documentación técnica LaTeX a Word corporativo
def generar_documentacion_corporativa(tech_doc):
    result = convert_latex_to_word(
        latex_s3_key=f"technical-docs/{tech_doc}",
        bucket_name="corporate-docs",
        generate_pdf=True  # Ambos formatos
    )
    
    # Aplicar plantilla corporativa
    apply_corporate_template(result['docx_key'])
    
    # Distribuir según política corporativa
    distribute_internally(result)
    
    return result
```

### ⚖️ **Legal - Contratos y Documentos**
```python
# Procesar contratos LaTeX a formato legal estándar
def procesar_contrato_legal(contract_latex):
    result = convert_latex_to_word(
        latex_s3_key=f"legal/contracts/{contract_latex}",
        bucket_name="legal-documents",
        generate_pdf=True  # PDF para firma digital
    )
    
    # Verificar formato legal
    validate_legal_format(result['docx_key'])
    
    # Preparar para firma digital
    prepare_for_digital_signature(result['pdf_key'])
    
    return result
```

### 🔬 **Investigación - Papers y Reports**
```python
# Convertir papers de investigación para journals
def preparar_paper_para_journal(paper_latex, journal_format):
    """Convierte paper LaTeX según requerimientos del journal."""
    
    result = convert_latex_to_word(
        latex_s3_key=f"research/papers/{paper_latex}",
        bucket_name="research-bucket",
        generate_pdf=True
    )
    
    # Aplicar formato específico del journal
    if journal_format == "ieee":
        apply_ieee_format(result['docx_key'])
    elif journal_format == "springer":
        apply_springer_format(result['docx_key'])
    
    return result
```

---

## 🚀 Roadmap y Mejoras Futuras

### 🎯 **Versión 2.0 (Próximamente)**
- **Conversión batch**: Múltiples archivos en una sola llamada
- **Plantillas personalizadas**: Subir tu propio `reference.docx`
- **Más formatos de salida**: HTML, EPUB, Markdown
- **API de configuración**: Cambiar parámetros sin redeploy

### 🎨 **Mejoras de formato**
- **Mejor soporte de ecuaciones**: MathJax integrado
- **Tablas complejas**: Soporte mejorado para tablas LaTeX
- **Bibliografías**: Integración con BibTeX
- **Índices automáticos**: TOC, figuras, tablas

### ⚡ **Optimizaciones de rendimiento**
- **Caché inteligente**: Evitar reconversiones innecesarias
- **Procesamiento paralelo**: Múltiples páginas simultáneas
- **Compresión optimizada**: Archivos más pequeños sin perder calidad

---

## 📞 Soporte

### 🛠️ **¿Necesitas ayuda?**

- **📧 Email**: support@bondx.com
- **📖 Documentación**: Esta misma página
- **🐛 Issues**: GitHub Issues del repositorio
- **💬 Discord**: [BondX Community](https://discord.gg/bondx)

### 🚀 **¿Quieres más funcionalidades?**

- Conversión de otros formatos (Markdown, HTML, etc.)
- Integración con más servicios de nube (Azure, GCP)
- API de procesamiento en tiempo real
- Webhooks para notificaciones automáticas

### 📝 **Contribuir al proyecto**

```bash
# 1. Fork del repositorio
git clone https://github.com/tu-usuario/bondx-latex-converter.git

# 2. Crear branch para tu feature
git checkout -b feature/nueva-funcionalidad

# 3. Hacer cambios y commit
git commit -m "Agregar nueva funcionalidad"

# 4. Push y crear Pull Request
git push origin feature/nueva-funcionalidad
```

---

**© 2024 BondX Technologies. Todos los derechos reservados.**

*BondX LaTeX Converter - La solución serverless definitiva para conversión de documentos académicos y profesionales.*

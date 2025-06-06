import os
import json
import subprocess
import tempfile
import boto3
import magic
from pathlib import Path
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
BUCKET_NAME = os.environ['BUCKET_NAME']

def lambda_handler(event, context):
    try:
        logger.info(f"Starting handler with event: {json.dumps(event)}")
        
        # Parsear el cuerpo de la petición
        body = event.get('body', '')
        if event.get('isBase64Encoded', False):
            import base64
            body = base64.b64decode(body).decode('utf-8')
        
        data = json.loads(body)
        logger.info(f"Parsed request data: {json.dumps(data)}")
        
        input_key = data.get('input_key')
        output_prefix = data.get('output_prefix', 'converted')  # Default to 'converted' if not provided
        bucket_name = data.get('bucket_name', os.environ['BUCKET_NAME'])  # Use provided bucket or fall back to env var
        generate_pdf = data.get('generate_pdf', False)  # Nuevo parámetro para controlar si se genera PDF

        if not input_key:
            logger.error("Missing input_key in request")
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Se requiere input_key en el cuerpo de la petición'
                })
            }

        # Crear directorio temporal para trabajo
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info(f"Created temp directory: {temp_dir}")
            
            # Descargar archivo LaTeX de S3
            input_file = os.path.join(temp_dir, 'input.tex')
            logger.info(f"Downloading {input_key} from bucket {BUCKET_NAME} to {input_file}")
            s3.download_file(BUCKET_NAME, input_key, input_file)

            # Verificar que es un archivo LaTeX
            mime = magic.Magic(mime=True)
            file_type = mime.from_file(input_file)
            logger.info(f"File type detected: {file_type}")
            
            if not file_type.startswith('text/'):
                logger.error(f"Invalid file type: {file_type}")
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'error': f'Tipo de archivo no válido: {file_type}'
                    })
                }

            # Log file contents for debugging
            logger.info(f"File contents of {input_file}:")
            with open(input_file, 'r') as f:
                logger.info(f.read())

            # Usar el archivo de referencia estático y el filtro Lua
            reference_doc = '/var/task/reference.docx'  # Ruta al archivo en el contenedor Lambda
            lua_filter = '/var/task/centered.lua'  # Ruta al filtro Lua en el contenedor Lambda

            # Generar DOCX usando pandoc con el documento de referencia y el filtro Lua
            logger.info("Starting DOCX generation...")
            docx_file = os.path.join(temp_dir, 'output.docx')
            result = subprocess.run(
                ['pandoc',
                 input_file,
                 '-o', docx_file,
                 '--from=latex',
                 '--to=docx',
                 '--standalone',
                 f'--reference-doc={reference_doc}',
                 f'--lua-filter={lua_filter}'
                ],
                capture_output=True,
                text=True
            )

            logger.info(f"pandoc stdout: {result.stdout}")
            logger.info(f"pandoc stderr: {result.stderr}")
            logger.info(f"pandoc return code: {result.returncode}")

            if result.returncode != 0:
                return {
                    'statusCode': 500,
                    'body': json.dumps({
                        'error': 'Error al generar DOCX',
                        'details': result.stderr
                    })
                }

            # Subir archivo DOCX a S3
            base_key = Path(input_key).stem
            docx_key = f'{output_prefix}/{base_key}.docx'
            logger.info(f"Uploading DOCX to {docx_key}")
            s3.upload_file(docx_file, bucket_name, docx_key)

            response_data = {
                'docx_key': docx_key
            }

            # Si se solicita PDF, convertir DOCX a PDF
            if generate_pdf:
                logger.info("Starting PDF generation from DOCX...")
                pdf_file = os.path.join(temp_dir, 'output.pdf')
                result = subprocess.run(
                    ['soffice', '--headless', '--convert-to', 'pdf', '--outdir', temp_dir, docx_file],
                    capture_output=True,
                    text=True
                )

                logger.info(f"soffice stdout: {result.stdout}")
                logger.info(f"soffice stderr: {result.stderr}")
                logger.info(f"soffice return code: {result.returncode}")

                if result.returncode != 0:
                    return {
                        'statusCode': 500,
                        'body': json.dumps({
                            'error': 'Error al generar PDF',
                            'details': result.stderr
                        })
                    }

                # Subir archivo PDF a S3
                pdf_key = f'{output_prefix}/{base_key}.pdf'
                logger.info(f"Uploading PDF to {pdf_key}")
                s3.upload_file(pdf_file, bucket_name, pdf_key)
                response_data['pdf_key'] = pdf_key

            return {
                'statusCode': 200,
                'body': json.dumps(response_data)
            }

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error: {str(e)}\nStacktrace: {error_details}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'details': error_details
            })
        }
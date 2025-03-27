import boto3
import json
import requests
import os
from pathlib import Path

# Configuración
API_ENDPOINT = "https://nbd03seupa.execute-api.us-east-1.amazonaws.com/prod/convert"
BUCKET_NAME = "bondx-latex-converter-latexconverterbucketc4c7e915-1qvhzn6qqvz4p"  # Este es el nombre del bucket creado por CDK

# Inicializar cliente S3
s3 = boto3.client('s3')

def upload_file(file_path):
    """Sube un archivo a S3"""
    file_name = Path(file_path).name
    print(f"Subiendo {file_name} a S3...")
    s3.upload_file(file_path, BUCKET_NAME, file_name)
    return file_name

def convert_file(input_key):
    """Llama al API para convertir el archivo"""
    print(f"Llamando al API para convertir {input_key}...")
    response = requests.post(
        API_ENDPOINT,
        json={"input_key": input_key}
    )
    return response.json()

def download_file(s3_key, local_path):
    """Descarga un archivo de S3"""
    print(f"Descargando {s3_key} a {local_path}...")
    s3.download_file(BUCKET_NAME, s3_key, local_path)

def main():
    # Subir archivo LaTeX
    input_file = "test_document.tex"
    s3_key = upload_file(input_file)
    
    # Convertir archivo
    result = convert_file(s3_key)
    print("Respuesta del API:", json.dumps(result, indent=2))
    
    if "body" in result:
        body = json.loads(result["body"])
        
        # Descargar archivos convertidos
        if "pdf_key" in body:
            download_file(body["pdf_key"], "output.pdf")
        if "docx_key" in body:
            download_file(body["docx_key"], "output.docx")
        
        print("\n¡Conversión completada!")
        print("Archivos generados:")
        print("- output.pdf")
        print("- output.docx")

if __name__ == "__main__":
    main() 
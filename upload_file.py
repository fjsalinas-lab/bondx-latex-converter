import boto3
from pathlib import Path

# Inicializar cliente S3
s3 = boto3.client('s3')

# Nombre correcto del bucket
BUCKET_NAME = "bondxlatexconverterstack-latexconverterbucketc4c7e-jvtxouhguqp5"

def upload_file(file_path):
    """Sube un archivo a S3"""
    file_name = Path(file_path).name
    print(f"Subiendo {file_name} a S3...")
    try:
        s3.upload_file(file_path, BUCKET_NAME, file_name)
        print(f"¡Archivo subido exitosamente!")
        print(f"Bucket: {BUCKET_NAME}")
        print(f"Key: {file_name}")
        return file_name
    except Exception as e:
        print(f"Error al subir el archivo: {str(e)}")
        return None

def main():
    input_file = "test_document.tex"
    result = upload_file(input_file)
    
    if result:
        print("\nAhora puedes usar Postman para probar la API con esta configuración:")
        print("\nMétodo: POST")
        print("URL: https://nbd03seupa.execute-api.us-east-1.amazonaws.com/prod/convert")
        print("Headers:")
        print("  Content-Type: application/json")
        print("\nBody (raw JSON):")
        print('{')
        print(f'    "input_key": "{result}"')
        print('}')

if __name__ == "__main__":
    main() 
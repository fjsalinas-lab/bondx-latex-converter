import boto3

# Inicializar cliente S3
s3 = boto3.client('s3')

# Nombre del bucket
BUCKET_NAME = "bondxlatexconverterstack-latexconverterbucketc4c7e-jvtxouhguqp5"

def list_bucket_contents():
    """Lista el contenido del bucket"""
    try:
        print(f"\nListando contenido del bucket: {BUCKET_NAME}")
        print("-" * 50)
        
        response = s3.list_objects_v2(Bucket=BUCKET_NAME)
        
        if 'Contents' in response:
            for obj in response['Contents']:
                print(f"- {obj['Key']} ({obj['Size']} bytes)")
        else:
            print("El bucket está vacío")
            
    except Exception as e:
        print(f"Error al listar el contenido del bucket: {str(e)}")

if __name__ == "__main__":
    list_bucket_contents() 
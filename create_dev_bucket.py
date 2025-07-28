#!/usr/bin/env python3
"""
Script para crear el bucket de desarrollo bondx-bucket-dev
"""

import boto3
import sys
from botocore.exceptions import ClientError

def create_dev_bucket():
    """Crear el bucket de desarrollo si no existe"""
    bucket_name = "bondx-bucket-dev"
    region = "us-east-2"  # Misma región que producción
    
    s3_client = boto3.client('s3', region_name=region)
    
    try:
        # Verificar si el bucket ya existe
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print(f"✅ El bucket {bucket_name} ya existe")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                # El bucket no existe, crearlo
                print(f"📦 Creando bucket {bucket_name}...")
                
                if region == 'us-east-1':
                    # us-east-1 no requiere LocationConstraint
                    s3_client.create_bucket(Bucket=bucket_name)
                else:
                    s3_client.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': region}
                    )
                
                # Configurar el bucket para bloquear acceso público
                s3_client.put_public_access_block(
                    Bucket=bucket_name,
                    PublicAccessBlockConfiguration={
                        'BlockPublicAcls': True,
                        'IgnorePublicAcls': True,
                        'BlockPublicPolicy': True,
                        'RestrictPublicBuckets': True
                    }
                )
                
                print(f"✅ Bucket {bucket_name} creado exitosamente")
                print(f"🔒 Configuración de seguridad aplicada")
                return True
            else:
                # Otro error
                raise e
                
    except ClientError as e:
        print(f"❌ Error al crear bucket: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def list_buckets():
    """Listar todos los buckets de BondX"""
    s3_client = boto3.client('s3')
    
    try:
        response = s3_client.list_buckets()
        bondx_buckets = [bucket['Name'] for bucket in response['Buckets'] if 'bondx' in bucket['Name'].lower()]
        
        if bondx_buckets:
            print("\n📂 Buckets de BondX encontrados:")
            for bucket in bondx_buckets:
                print(f"  - {bucket}")
        else:
            print("\n📭 No se encontraron buckets de BondX")
            
    except ClientError as e:
        print(f"❌ Error al listar buckets: {e}")

if __name__ == "__main__":
    print("🚀 BondX - Configuración de Bucket de Desarrollo")
    print("=" * 50)
    
    # Verificar credenciales de AWS
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"👤 AWS Account: {identity['Account']}")
        print(f"👤 User: {identity.get('UserName', identity.get('Arn', 'Unknown'))}")
    except:
        print("❌ Error: No se encontraron credenciales de AWS válidas")
        sys.exit(1)
    
    # Crear bucket de desarrollo
    success = create_dev_bucket()
    
    # Mostrar buckets existentes
    list_buckets()
    
    if success:
        print("\n🎉 ¡Configuración completada!")
        print("\nAhora puedes usar el bucket de desarrollo en tus requests:")
        print('{"input_key": "document.tex", "bucket_name": "bondx-bucket-dev"}')
    else:
        print("\n❌ Falló la configuración")
        sys.exit(1) 
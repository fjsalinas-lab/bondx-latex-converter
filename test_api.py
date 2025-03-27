import requests
import json
import uuid
import os
from datetime import datetime

# Configuración
API_URL = "https://sr96hcsryc.execute-api.us-east-2.amazonaws.com/prod/convert"
INPUT_KEY = "demand_letters/43/carta_demandante_43.tex"
BUCKET_NAME = "bondx-bucket"

def test_conversion():
    """Prueba la conversión usando la API"""
    # Generar un prefijo único para esta prueba
    test_id = str(uuid.uuid4())[:8]
    current_date = datetime.now().strftime("%Y%m%d")
    output_prefix = f"test_outputs/{current_date}/{test_id}"
    
    print(f"\nEnviando petición a la API...")
    print(f"URL: {API_URL}")
    print(f"Input key: {INPUT_KEY}")
    print(f"Output prefix: {output_prefix}")
    print(f"Bucket: {BUCKET_NAME}")
    print("-" * 50)
    
    try:
        # Test case 1: Petición válida
        print("\nTest Case 1: Petición válida")
        payload = {
            "input_key": INPUT_KEY,
            "output_prefix": output_prefix,
            "bucket_name": BUCKET_NAME
        }
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            API_URL,
            data=json.dumps(payload),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        
        print(f"Código de respuesta: {response.status_code}")
        print("Respuesta:")
        try:
            print(json.dumps(response.json(), indent=2))
        except json.JSONDecodeError:
            print(f"Raw response: {response.text}")
        
        # Test case 2: Petición sin output_prefix
        print("\nTest Case 2: Petición sin output_prefix")
        payload = {
            "input_key": INPUT_KEY,
            "bucket_name": BUCKET_NAME
        }
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            API_URL,
            data=json.dumps(payload),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        
        print(f"Código de respuesta: {response.status_code}")
        print("Respuesta:")
        try:
            print(json.dumps(response.json(), indent=2))
        except json.JSONDecodeError:
            print(f"Raw response: {response.text}")
        
        # Test case 3: Petición sin input_key
        print("\nTest Case 3: Petición sin input_key")
        payload = {
            "output_prefix": output_prefix,
            "bucket_name": BUCKET_NAME
        }
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            API_URL,
            data=json.dumps(payload),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        
        print(f"Código de respuesta: {response.status_code}")
        print("Respuesta:")
        try:
            print(json.dumps(response.json(), indent=2))
        except json.JSONDecodeError:
            print(f"Raw response: {response.text}")
        
    except Exception as e:
        print(f"Error al llamar a la API: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    test_conversion() 
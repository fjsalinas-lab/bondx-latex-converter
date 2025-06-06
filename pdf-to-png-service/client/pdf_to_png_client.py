import logging
import json
import requests
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class PdfToPngClient:
    """
    Cliente para el microservicio de conversión PDF a PNG
    """
    
    def __init__(self, api_endpoint: str, timeout: int = 300):
        """
        Inicializar cliente
        
        Args:
            api_endpoint: URL completa del endpoint de conversión
            timeout: Timeout en segundos para las requests
        """
        self.api_endpoint = api_endpoint.rstrip('/')
        self.timeout = timeout
        
    def convert_pdf_to_png(
        self,
        pdf_s3_key: str,
        bucket_name: str,
        output_prefix: str = "converted",
        dpi: int = 300,
        return_base64: bool = False,
        max_retries: int = 3,
        retry_delay: int = 2
    ) -> Dict[str, Any]:
        """
        Convertir PDF a PNG usando el microservicio
        
        Args:
            pdf_s3_key: Clave S3 del archivo PDF
            bucket_name: Nombre del bucket S3
            output_prefix: Prefijo para los archivos de salida
            dpi: DPI para la conversión (default: 300)
            return_base64: Si retornar imágenes como base64 en lugar de subirlas a S3
            max_retries: Número máximo de reintentos
            retry_delay: Delay entre reintentos en segundos
            
        Returns:
            Dict con el resultado de la conversión
            
        Raises:
            Exception: Si la conversión falla después de todos los reintentos
        """
        
        payload = {
            "pdf_s3_key": pdf_s3_key,
            "bucket_name": bucket_name,
            "output_prefix": output_prefix,
            "dpi": dpi,
            "return_base64": return_base64
        }
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Llamando al microservicio PDF to PNG (intento {attempt + 1}/{max_retries})")
                logger.info(f"Endpoint: {self.api_endpoint}")
                logger.info(f"Payload: {json.dumps(payload)}")
                
                start_time = time.time()
                
                response = requests.post(
                    self.api_endpoint,
                    json=payload,
                    timeout=self.timeout,
                    headers={
                        'Content-Type': 'application/json'
                    }
                )
                
                elapsed_time = time.time() - start_time
                logger.info(f"Microservicio respondió en {elapsed_time:.2f} segundos")
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Conversión exitosa: {result.get('total_pages', 0)} páginas")
                    return result
                else:
                    error_msg = f"Error del microservicio: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    
                    if attempt < max_retries - 1:
                        logger.info(f"Reintentando en {retry_delay} segundos...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise Exception(error_msg)
                        
            except requests.Timeout:
                error_msg = f"Timeout del microservicio después de {self.timeout} segundos"
                logger.error(error_msg)
                
                if attempt < max_retries - 1:
                    logger.info(f"Reintentando en {retry_delay} segundos...")
                    time.sleep(retry_delay)
                    continue
                else:
                    raise Exception(error_msg)
                    
            except requests.RequestException as e:
                error_msg = f"Error de conexión con el microservicio: {str(e)}"
                logger.error(error_msg)
                
                if attempt < max_retries - 1:
                    logger.info(f"Reintentando en {retry_delay} segundos...")
                    time.sleep(retry_delay)
                    continue
                else:
                    raise Exception(error_msg)
                    
            except Exception as e:
                error_msg = f"Error inesperado: {str(e)}"
                logger.error(error_msg)
                
                if attempt < max_retries - 1:
                    logger.info(f"Reintentando en {retry_delay} segundos...")
                    time.sleep(retry_delay)
                    continue
                else:
                    raise Exception(error_msg)

# Función de conveniencia para usar desde textract_service.py
def convert_pdf_to_png_via_microservice(
    pdf_s3_key: str,
    bucket_name: str,
    api_endpoint: str,
    output_prefix: str = "processed_documents",
    dpi: int = 300
) -> List[str]:
    """
    Función de conveniencia para convertir PDF a PNG via microservicio
    
    Args:
        pdf_s3_key: Clave S3 del PDF
        bucket_name: Nombre del bucket
        api_endpoint: URL completa del endpoint de conversión
        output_prefix: Prefijo para archivos de salida
        dpi: DPI para conversión
        
    Returns:
        Lista de claves S3 de las imágenes PNG generadas
        
    Raises:
        Exception: Si la conversión falla
    """
    
    client = PdfToPngClient(api_endpoint)
    
    try:
        result = client.convert_pdf_to_png(
            pdf_s3_key=pdf_s3_key,
            bucket_name=bucket_name,
            output_prefix=output_prefix,
            dpi=dpi,
            return_base64=False  # Subir a S3, no retornar base64
        )
        
        if result.get('success'):
            # Extraer las claves S3 de las imágenes
            png_keys = [img['s3_key'] for img in result.get('images', [])]
            logger.info(f"Generadas {len(png_keys)} imágenes PNG: {png_keys}")
            return png_keys
        else:
            raise Exception(f"Microservicio reportó fallo: {result}")
            
    except Exception as e:
        logger.error(f"Error convirtiendo PDF a PNG via microservicio: {str(e)}")
        raise

# Función de health check
def check_microservice_health(api_base_url: str) -> bool:
    """
    Verificar si el microservicio está funcionando
    
    Args:
        api_base_url: URL base del API Gateway
        
    Returns:
        bool: True si el microservicio está healthy
    """
    try:
        health_url = f"{api_base_url.rstrip('/')}/health"
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return result.get('status') == 'healthy'
        else:
            return False
            
    except Exception as e:
        logger.error(f"Error checking microservice health: {str(e)}")
        return False

# Ejemplo de uso
if __name__ == "__main__":
    # Configurar logging para pruebas
    logging.basicConfig(level=logging.INFO)
    
    # Ejemplo de uso del cliente
    endpoint = "https://your-api-gateway-url.execute-api.us-east-2.amazonaws.com/prod/convert"
    client = PdfToPngClient(endpoint)
    
    try:
        result = client.convert_pdf_to_png(
            pdf_s3_key="documents/sample.pdf",
            bucket_name="bondx-bucket",
            output_prefix="converted",
            dpi=300
        )
        
        print("Conversión exitosa:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Error: {str(e)}") 
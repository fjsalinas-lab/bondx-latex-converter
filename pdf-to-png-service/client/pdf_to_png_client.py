import logging
import json
import requests
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import base64

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

    def convert_pdf_to_png_fast(self, pdf_base64: str, 
                               api_endpoint: str, 
                               dpi: int = 150,
                               page_number: int = None) -> dict:
        """
        Convert PDF to PNG using the fast endpoint (no S3 operations).
        
        Args:
            pdf_base64: Base64 encoded PDF content
            api_endpoint: API endpoint URL (should end with /convert-fast)
            dpi: DPI for conversion (default 150 for speed)
            page_number: Optional specific page to convert (for speed)
        
        Returns:
            Dictionary with conversion results including base64 images
        """
        try:
            # Prepare request payload
            payload = {
                'pdf_base64': pdf_base64,
                'dpi': dpi
            }
            
            if page_number:
                payload['page_number'] = page_number
            
            # Make API request
            response = requests.post(
                api_endpoint,
                json=payload,
                timeout=120  # 2 minutes timeout
            )
            
            # Check response
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Fast conversion successful: {result.get('total_pages', 0)} pages")
                return result
            else:
                error_msg = f"API error: {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f" - {error_detail.get('error', 'Unknown error')}"
                except:
                    error_msg += f" - {response.text}"
                
                print(f"❌ Fast conversion failed: {error_msg}")
                return {'error': error_msg}
                
        except requests.exceptions.Timeout:
            error_msg = "Request timeout (conversion taking too long)"
            print(f"❌ Fast conversion failed: {error_msg}")
            return {'error': error_msg}
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            print(f"❌ Fast conversion failed: {error_msg}")
            return {'error': error_msg}
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"❌ Fast conversion failed: {error_msg}")
            return {'error': error_msg}

    def pdf_file_to_base64(self, file_path: str) -> str:
        """
        Convert a PDF file to base64 string.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Base64 encoded string of the PDF content
        """
        try:
            with open(file_path, 'rb') as f:
                pdf_bytes = f.read()
            return base64.b64encode(pdf_bytes).decode('utf-8')
        except Exception as e:
            raise ValueError(f"Error reading PDF file: {str(e)}")

    def save_base64_image(self, base64_string: str, output_path: str):
        """
        Save a base64 encoded image to a file.
        
        Args:
            base64_string: Base64 encoded image data
            output_path: Path where to save the image
        """
        try:
            image_bytes = base64.b64decode(base64_string)
            with open(output_path, 'wb') as f:
                f.write(image_bytes)
            print(f"✅ Image saved to: {output_path}")
        except Exception as e:
            print(f"❌ Error saving image: {str(e)}")

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

# Función de conveniencia para conversión rápida
def convert_pdf_to_png_fast_via_microservice(
    pdf_file_path: str,
    api_endpoint: str,
    dpi: int = 150,
    page_number: int = None,
    save_to_files: bool = False,
    output_dir: str = "."
) -> dict:
    """
    Función de conveniencia para conversión rápida PDF a PNG sin S3
    
    Args:
        pdf_file_path: Ruta al archivo PDF local
        api_endpoint: URL completa del endpoint de conversión rápida (debe incluir /convert-fast)
        dpi: DPI para conversión (default 150 para velocidad)
        page_number: Número de página específica a convertir (optional)
        save_to_files: Si True, guarda las imágenes como archivos
        output_dir: Directorio donde guardar las imágenes (si save_to_files=True)
        
    Returns:
        Dictionary con resultados de conversión incluidas las imágenes en base64
        
    Raises:
        Exception: Si la conversión falla
    """
    
    client = PdfToPngClient(api_endpoint)
    
    try:
        # Leer PDF y convertir a base64
        pdf_base64 = client.pdf_file_to_base64(pdf_file_path)
        
        # Hacer conversión rápida
        result = client.convert_pdf_to_png_fast(
            pdf_base64=pdf_base64,
            api_endpoint=api_endpoint,
            dpi=dpi,
            page_number=page_number
        )
        
        if not result.get('success'):
            raise Exception(f"Conversión rápida falló: {result.get('error', 'Unknown error')}")
        
        # Guardar archivos si se solicita
        if save_to_files:
            import os
            base_name = os.path.splitext(os.path.basename(pdf_file_path))[0]
            
            for img_data in result.get('images', []):
                page_num = img_data.get('page')
                base64_data = img_data.get('base64')
                
                if base64_data:
                    output_path = os.path.join(output_dir, f"{base_name}_page_{page_num}.png")
                    client.save_base64_image(base64_data, output_path)
        
        logger.info(f"Conversión rápida exitosa: {result.get('total_pages', 0)} páginas")
        return result
        
    except Exception as e:
        logger.error(f"Error en conversión rápida: {str(e)}")
        raise

# Función de conveniencia para conversión de una sola página
def convert_pdf_page_to_png_fast(
    pdf_file_path: str,
    page_number: int,
    api_endpoint: str,
    dpi: int = 150,
    save_to_file: bool = False,
    output_path: str = None
) -> str:
    """
    Función de conveniencia para convertir una sola página PDF a PNG rápidamente
    
    Args:
        pdf_file_path: Ruta al archivo PDF local
        page_number: Número de página a convertir
        api_endpoint: URL completa del endpoint de conversión rápida
        dpi: DPI para conversión (default 150 para velocidad)
        save_to_file: Si True, guarda la imagen como archivo
        output_path: Ruta donde guardar la imagen (opcional)
        
    Returns:
        Base64 string de la imagen PNG generada
        
    Raises:
        Exception: Si la conversión falla
    """
    
    client = PdfToPngClient(api_endpoint)
    
    try:
        # Leer PDF y convertir a base64
        pdf_base64 = client.pdf_file_to_base64(pdf_file_path)
        
        # Convertir solo la página específica
        result = client.convert_pdf_to_png_fast(
            pdf_base64=pdf_base64,
            api_endpoint=api_endpoint,
            dpi=dpi,
            page_number=page_number
        )
        
        if not result.get('success'):
            raise Exception(f"Conversión de página falló: {result.get('error', 'Unknown error')}")
        
        # Obtener la imagen de la página
        images = result.get('images', [])
        if not images:
            raise Exception("No se generó ninguna imagen")
        
        page_image = images[0]  # Solo debería haber una imagen
        base64_data = page_image.get('base64')
        
        if not base64_data:
            raise Exception("No se recibió imagen en base64")
        
        # Guardar archivo si se solicita
        if save_to_file:
            if not output_path:
                import os
                base_name = os.path.splitext(os.path.basename(pdf_file_path))[0]
                output_path = f"{base_name}_page_{page_number}.png"
            
            client.save_base64_image(base64_data, output_path)
        
        logger.info(f"Página {page_number} convertida exitosamente")
        return base64_data
        
    except Exception as e:
        logger.error(f"Error convirtiendo página {page_number}: {str(e)}")
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
    
    # Ejemplo de uso del cliente estándar
    endpoint = "https://your-api-gateway-url.execute-api.us-east-2.amazonaws.com/prod/convert"
    client = PdfToPngClient(endpoint)
    
    try:
        result = client.convert_pdf_to_png(
            pdf_s3_key="documents/sample.pdf",
            bucket_name="bondx-bucket",
            output_prefix="converted",
            dpi=300
        )
        
        print("Conversión estándar exitosa:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Ejemplo de uso del endpoint rápido
    print("\n" + "="*50)
    print("Ejemplo de conversión rápida:")
    
    try:
        fast_endpoint = "https://your-api-gateway-url.execute-api.us-east-2.amazonaws.com/prod/convert-fast"
        
        # Convertir una sola página rápidamente
        base64_image = convert_pdf_page_to_png_fast(
            pdf_file_path="sample.pdf",
            page_number=1,
            api_endpoint=fast_endpoint,
            dpi=150,
            save_to_file=True,
            output_path="page1_fast.png"
        )
        
        print("Conversión rápida exitosa!")
        print(f"Tamaño imagen base64: {len(base64_image)} caracteres")
        
    except Exception as e:
        print(f"Error en conversión rápida: {str(e)}") 

# Nuevas funciones para procesamiento asíncrono

def convert_pdf_to_png_async(
    pdf_s3_key: str,
    bucket_name: str,
    api_endpoint: str,
    output_prefix: str = "converted",
    dpi: int = 300,
    return_base64: bool = False,
    callback_url: str = None
) -> str:
    """
    Iniciar conversión asíncrona PDF a PNG.
    
    Args:
        pdf_s3_key: Clave S3 del archivo PDF
        bucket_name: Nombre del bucket S3
        api_endpoint: URL del endpoint async (debe terminar con /convert-async)
        output_prefix: Prefijo para los archivos de salida
        dpi: DPI para la conversión (default: 300)
        return_base64: Si retornar imágenes como base64 en lugar de subirlas a S3
        callback_url: URL opcional para webhook cuando se complete
        
    Returns:
        job_id: ID del trabajo para monitorear el progreso
        
    Raises:
        Exception: Si falla al iniciar la conversión
    """
    try:
        payload = {
            "pdf_s3_key": pdf_s3_key,
            "bucket_name": bucket_name,
            "output_prefix": output_prefix,
            "dpi": dpi,
            "return_base64": return_base64
        }
        
        if callback_url:
            payload["callback_url"] = callback_url
        
        print(f"🚀 Iniciando conversión asíncrona para {pdf_s3_key}")
        
        response = requests.post(
            api_endpoint,
            json=payload,
            timeout=30  # Solo para iniciar el job
        )
        
        if response.status_code == 202:
            result = response.json()
            job_id = result.get('job_id')
            print(f"✅ Conversión iniciada exitosamente. Job ID: {job_id}")
            return job_id
        else:
            error_msg = f"Error al iniciar conversión: {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f" - {error_detail.get('error', 'Unknown error')}"
            except:
                error_msg += f" - {response.text}"
            
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
            
    except requests.exceptions.RequestException as e:
        error_msg = f"Error de conexión: {str(e)}"
        print(f"❌ {error_msg}")
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Error inesperado: {str(e)}"
        print(f"❌ {error_msg}")
        raise Exception(error_msg)

def check_conversion_status(job_id: str, api_endpoint: str) -> Dict[str, Any]:
    """
    Verificar el estado de una conversión asíncrona.
    
    Args:
        job_id: ID del trabajo obtenido de convert_pdf_to_png_async
        api_endpoint: URL del endpoint de status (debe terminar con /job-status)
        
    Returns:
        Dict con información del estado del trabajo
        
    Raises:
        Exception: Si falla al obtener el estado
    """
    try:
        # Construir URL con el job_id
        status_url = f"{api_endpoint.rstrip('/')}/{job_id}"
        
        response = requests.get(status_url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            status = result.get('status')
            progress = result.get('progress', 0)
            
            if status == 'completed':
                print(f"✅ Conversión completada (100%)")
            elif status == 'processing':
                print(f"⏳ Procesando... ({progress}%)")
            elif status == 'failed':
                error_msg = result.get('error_message', 'Unknown error')
                print(f"❌ Conversión falló: {error_msg}")
            else:
                print(f"📋 Estado: {status}")
                
            return result
            
        elif response.status_code == 404:
            error_msg = f"Job no encontrado: {job_id}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
        else:
            error_msg = f"Error al verificar estado: {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f" - {error_detail.get('error', 'Unknown error')}"
            except:
                error_msg += f" - {response.text}"
            
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
            
    except requests.exceptions.RequestException as e:
        error_msg = f"Error de conexión: {str(e)}"
        print(f"❌ {error_msg}")
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Error inesperado: {str(e)}"
        print(f"❌ {error_msg}")
        raise Exception(error_msg)

def wait_for_conversion_completion(
    job_id: str,
    status_api_endpoint: str,
    max_wait_time: int = 900,  # 15 minutos
    check_interval: int = 5    # 5 segundos
) -> Dict[str, Any]:
    """
    Esperar hasta que la conversión asíncrona se complete.
    
    Args:
        job_id: ID del trabajo
        status_api_endpoint: URL del endpoint de status
        max_wait_time: Tiempo máximo de espera en segundos
        check_interval: Intervalo entre verificaciones en segundos
        
    Returns:
        Dict con el resultado final de la conversión
        
    Raises:
        Exception: Si la conversión falla o excede el tiempo máximo
    """
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        try:
            result = check_conversion_status(job_id, status_api_endpoint)
            status = result.get('status')
            
            if status == 'completed':
                print(f"🎉 Conversión completada exitosamente!")
                return result
            elif status == 'failed':
                error_msg = result.get('error_message', 'Unknown error')
                raise Exception(f"Conversión falló: {error_msg}")
            elif status in ['submitted', 'processing']:
                # Continuar esperando
                time.sleep(check_interval)
            else:
                raise Exception(f"Estado desconocido: {status}")
                
        except Exception as e:
            if "Conversión falló" in str(e):
                raise  # Re-lanzar errores de conversión
            else:
                print(f"⚠️ Error verificando estado: {e}")
                time.sleep(check_interval)
    
    raise Exception(f"Timeout: Conversión no completada después de {max_wait_time} segundos")

def convert_pdf_to_png_async_and_wait(
    pdf_s3_key: str,
    bucket_name: str,
    async_api_endpoint: str,
    status_api_endpoint: str,
    output_prefix: str = "converted",
    dpi: int = 300,
    return_base64: bool = False,
    callback_url: str = None,
    max_wait_time: int = 900,
    check_interval: int = 5
) -> Dict[str, Any]:
    """
    Conversión asíncrona completa: iniciar + esperar + obtener resultados.
    
    Args:
        pdf_s3_key: Clave S3 del archivo PDF
        bucket_name: Nombre del bucket S3
        async_api_endpoint: URL del endpoint async
        status_api_endpoint: URL del endpoint de status
        output_prefix: Prefijo para los archivos de salida
        dpi: DPI para la conversión
        return_base64: Si retornar imágenes como base64
        callback_url: URL opcional para webhook
        max_wait_time: Tiempo máximo de espera
        check_interval: Intervalo entre verificaciones
        
    Returns:
        Dict con el resultado final de la conversión
        
    Raises:
        Exception: Si cualquier paso falla
    """
    print(f"🔄 Iniciando conversión asíncrona completa para {pdf_s3_key}")
    
    # Paso 1: Iniciar conversión
    job_id = convert_pdf_to_png_async(
        pdf_s3_key=pdf_s3_key,
        bucket_name=bucket_name,
        api_endpoint=async_api_endpoint,
        output_prefix=output_prefix,
        dpi=dpi,
        return_base64=return_base64,
        callback_url=callback_url
    )
    
    # Paso 2: Esperar completación
    result = wait_for_conversion_completion(
        job_id=job_id,
        status_api_endpoint=status_api_endpoint,
        max_wait_time=max_wait_time,
        check_interval=check_interval
    )
    
    print(f"✅ Conversión asíncrona completada: {result.get('total_pages', 0)} páginas")
    return result

def list_conversion_jobs(
    jobs_api_endpoint: str,
    status_filter: str = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Listar jobs de conversión.
    
    Args:
        jobs_api_endpoint: URL del endpoint de jobs
        status_filter: Filtrar por estado ('submitted', 'processing', 'completed', 'failed')
        limit: Máximo número de jobs a retornar
        
    Returns:
        Lista de jobs con su información
        
    Raises:
        Exception: Si falla al obtener la lista
    """
    try:
        params = {'limit': limit}
        if status_filter:
            params['status'] = status_filter
        
        response = requests.get(jobs_api_endpoint, params=params, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            jobs = result.get('jobs', [])
            count = result.get('count', 0)
            
            print(f"📋 Encontrados {count} jobs")
            
            if status_filter:
                print(f"   Filtrado por estado: {status_filter}")
            
            return jobs
        else:
            error_msg = f"Error al listar jobs: {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f" - {error_detail.get('error', 'Unknown error')}"
            except:
                error_msg += f" - {response.text}"
            
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
            
    except requests.exceptions.RequestException as e:
        error_msg = f"Error de conexión: {str(e)}"
        print(f"❌ {error_msg}")
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Error inesperado: {str(e)}"
        print(f"❌ {error_msg}")
        raise Exception(error_msg) 
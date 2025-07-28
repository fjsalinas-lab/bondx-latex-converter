#!/usr/bin/env python3
"""
Ejemplo de uso del microservicio PDF to PNG con procesamiento asíncrono.

Este script demuestra cómo usar las nuevas funcionalidades para evitar
los timeouts de 30 segundos con documentos grandes.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'client'))

from pdf_to_png_client import (
    convert_pdf_to_png_async,
    check_conversion_status,
    wait_for_conversion_completion,
    convert_pdf_to_png_async_and_wait,
    list_conversion_jobs,
    convert_pdf_to_png_fast_via_microservice
)

# Configuración - Actualizar con tus URLs reales después del deploy
API_BASE_URL = "https://your-api-id.execute-api.us-east-2.amazonaws.com/prod"
ASYNC_ENDPOINT = f"{API_BASE_URL}/convert-async"
STATUS_ENDPOINT = f"{API_BASE_URL}/job-status"
JOBS_ENDPOINT = f"{API_BASE_URL}/jobs"
FAST_ENDPOINT = f"{API_BASE_URL}/convert-fast"

# Configuración del documento
PDF_S3_KEY = "documents/cronograma.pdf"  # Cambiar por tu documento
BUCKET_NAME = "bondx-bucket"
OUTPUT_PREFIX = "converted"

def example_1_async_conversion():
    """
    Ejemplo 1: Conversión asíncrona paso a paso
    Recomendado para documentos grandes (>500KB o >10 páginas)
    """
    print("🔄 Ejemplo 1: Conversión asíncrona paso a paso")
    print("=" * 50)
    
    try:
        # Paso 1: Iniciar conversión asíncrona
        print("📤 Iniciando conversión asíncrona...")
        job_id = convert_pdf_to_png_async(
            pdf_s3_key=PDF_S3_KEY,
            bucket_name=BUCKET_NAME,
            api_endpoint=ASYNC_ENDPOINT,
            output_prefix=OUTPUT_PREFIX,
            dpi=300
        )
        
        # Paso 2: Monitorear progreso manualmente
        print("📊 Monitoreando progreso...")
        import time
        
        while True:
            status_result = check_conversion_status(job_id, STATUS_ENDPOINT)
            
            if status_result['status'] == 'completed':
                print("🎉 ¡Conversión completada!")
                
                # Mostrar resultados
                images = status_result.get('images', [])
                print(f"📸 Imágenes generadas: {len(images)}")
                
                for img in images:
                    print(f"   • Página {img['page']}: {img['s3_key']} ({img['size_bytes']} bytes)")
                
                break
                
            elif status_result['status'] == 'failed':
                print(f"❌ Conversión falló: {status_result.get('error_message')}")
                break
                
            elif status_result['status'] in ['submitted', 'processing']:
                progress = status_result.get('progress', 0)
                print(f"⏳ Procesando... {progress}%")
                time.sleep(5)  # Esperar 5 segundos antes de verificar de nuevo
                
    except Exception as e:
        print(f"❌ Error: {e}")

def example_2_async_and_wait():
    """
    Ejemplo 2: Conversión asíncrona con espera automática
    Más simple - inicia y espera hasta completar
    """
    print("\n🔄 Ejemplo 2: Conversión asíncrona con espera automática")
    print("=" * 50)
    
    try:
        # Conversión completa con espera automática
        result = convert_pdf_to_png_async_and_wait(
            pdf_s3_key=PDF_S3_KEY,
            bucket_name=BUCKET_NAME,
            async_api_endpoint=ASYNC_ENDPOINT,
            status_api_endpoint=STATUS_ENDPOINT,
            output_prefix=OUTPUT_PREFIX,
            dpi=300,
            max_wait_time=900,  # 15 minutos máximo
            check_interval=5    # Verificar cada 5 segundos
        )
        
        # Mostrar resultados
        images = result.get('images', [])
        print(f"📸 Imágenes generadas: {len(images)}")
        
        for img in images:
            print(f"   • Página {img['page']}: {img['s3_key']} ({img['size_bytes']} bytes)")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def example_3_fast_conversion():
    """
    Ejemplo 3: Conversión rápida para documentos pequeños
    Sin S3, usando base64 - para documentos <500KB
    """
    print("\n⚡ Ejemplo 3: Conversión rápida para documentos pequeños")
    print("=" * 50)
    
    try:
        # Para este ejemplo, necesitarías un archivo PDF local
        local_pdf_path = "sample.pdf"  # Cambiar por tu archivo
        
        if not os.path.exists(local_pdf_path):
            print(f"⚠️  Archivo no encontrado: {local_pdf_path}")
            print("   Omitiendo este ejemplo...")
            return
        
        result = convert_pdf_to_png_fast_via_microservice(
            pdf_file_path=local_pdf_path,
            api_endpoint=FAST_ENDPOINT,
            dpi=150,  # DPI más bajo para velocidad
            save_to_files=True,
            output_dir="fast_output"
        )
        
        if 'error' not in result:
            print(f"✅ Conversión rápida exitosa: {result.get('total_pages', 0)} páginas")
        else:
            print(f"❌ Error en conversión rápida: {result['error']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def example_4_list_jobs():
    """
    Ejemplo 4: Listar jobs de conversión
    Útil para monitorear trabajos en curso
    """
    print("\n📋 Ejemplo 4: Listar jobs de conversión")
    print("=" * 50)
    
    try:
        # Listar todos los jobs
        print("📋 Todos los jobs:")
        all_jobs = list_conversion_jobs(JOBS_ENDPOINT, limit=10)
        
        for job in all_jobs:
            print(f"   • {job['job_id'][:8]}... - {job['status']} - {job['created_at']}")
        
        # Listar solo jobs completados
        print("\n✅ Jobs completados:")
        completed_jobs = list_conversion_jobs(
            JOBS_ENDPOINT,
            status_filter='completed',
            limit=5
        )
        
        for job in completed_jobs:
            print(f"   • {job['job_id'][:8]}... - {job['total_pages']} páginas - {job['created_at']}")
            
        # Listar jobs en proceso
        print("\n⏳ Jobs en proceso:")
        processing_jobs = list_conversion_jobs(
            JOBS_ENDPOINT,
            status_filter='processing',
            limit=5
        )
        
        for job in processing_jobs:
            progress = job.get('progress', 0)
            print(f"   • {job['job_id'][:8]}... - {progress}% - {job['created_at']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """
    Función principal - ejecutar ejemplos
    """
    print("🚀 Ejemplos de uso del microservicio PDF to PNG")
    print("=" * 60)
    
    # Verificar configuración
    if "your-api-id" in API_BASE_URL:
        print("⚠️  IMPORTANTE: Actualiza las URLs en este script con tu API real")
        print("   Después del deploy, reemplaza 'your-api-id' con tu ID real")
        print()
    
    # Ejecutar ejemplos
    try:
        # Ejemplo 1: Conversión asíncrona paso a paso
        example_1_async_conversion()
        
        # Ejemplo 2: Conversión asíncrona con espera
        example_2_async_and_wait()
        
        # Ejemplo 3: Conversión rápida
        example_3_fast_conversion()
        
        # Ejemplo 4: Listar jobs
        example_4_list_jobs()
        
    except KeyboardInterrupt:
        print("\n🛑 Interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error general: {e}")
    
    print("\n🎯 Recomendaciones:")
    print("   • Para documentos grandes (>500KB): usar /convert-async")
    print("   • Para documentos pequeños: usar /convert-fast")
    print("   • Para integración en producción: usar convert_pdf_to_png_async_and_wait")

if __name__ == "__main__":
    main() 
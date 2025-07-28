import os
import json
import boto3
import logging
from io import BytesIO
from pdf2image import convert_from_bytes
import base64
from typing import List, Dict, Any
import uuid
import time
from datetime import datetime, timedelta
import threading
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize S3 client
s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get('BUCKET_NAME')

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
JOBS_TABLE_NAME = os.environ.get('JOBS_TABLE_NAME')
jobs_table = dynamodb.Table(JOBS_TABLE_NAME) if JOBS_TABLE_NAME else None

# Configuration from environment variables
PDF_OPTIMIZATION_LEVEL = os.environ.get('PDF_OPTIMIZATION_LEVEL', 'MEDIUM')
MAX_CONCURRENT_PAGES = int(os.environ.get('MAX_CONCURRENT_PAGES', '2'))
COMPRESSION_QUALITY = int(os.environ.get('COMPRESSION_QUALITY', '90'))

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main handler that routes to appropriate conversion method based on path.
    """
    try:
        # Check if this is the fast conversion endpoint
        path = event.get('path', '')
        http_method = event.get('httpMethod', 'POST')
        
        if path.endswith('/convert-fast'):
            return handle_fast_conversion(event, context)
        elif path.endswith('/convert-async'):
            return handle_async_conversion(event, context)
        elif path.startswith('/job-status/'):
            return handle_job_status(event, context)
        elif path.endswith('/jobs'):
            return handle_jobs_list(event, context)
        else:
            return handle_standard_conversion(event, context)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Unexpected error in main handler: {str(e)}\nStacktrace: {error_details}")
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'Internal server error: {str(e)}',
                'details': error_details
            })
        }

def handle_fast_conversion(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Fast PDF to PNG conversion without S3 operations.
    
    Expected input:
    {
        "pdf_base64": "base64-encoded-pdf-content",
        "dpi": 150,  # optional, default 150 for speed
        "page_number": 1  # optional, convert only specific page for speed
    }
    
    Returns:
    {
        "statusCode": 200,
        "body": {
            "success": true,
            "total_pages": 3,
            "requested_page": 1,  # if page_number specified
            "images": [
                {
                    "page": 1,
                    "base64": "base64-encoded-png-content",
                    "size_bytes": 12345
                }
            ]
        }
    }
    """
    try:
        logger.info("Starting fast PDF to PNG conversion")
        
        # Parse request body
        body = event.get('body', '')
        if event.get('isBase64Encoded', False):
            body = base64.b64decode(body).decode('utf-8')
        
        if isinstance(body, str):
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Invalid JSON in request body'})
                }
        else:
            data = body
        
        # Extract parameters - optimized for speed
        pdf_base64 = data.get('pdf_base64')
        dpi = data.get('dpi', 150)  # Lower DPI for speed
        page_number = data.get('page_number')  # Optional: convert only specific page
        
        if not pdf_base64:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'pdf_base64 is required'})
            }
        
        # Decode PDF from base64
        try:
            pdf_bytes = base64.b64decode(pdf_base64)
            logger.info(f"Decoded PDF: {len(pdf_bytes)} bytes")
        except Exception as e:
            logger.error(f"Error decoding PDF from base64: {str(e)}")
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': f'Invalid PDF base64: {str(e)}'})
            }
        
        # Convert PDF to PNG images using pdf2image
        logger.info(f"Converting PDF to PNG images with DPI={dpi}")
        
        try:
            # Apply optimization settings for maximum speed
            if PDF_OPTIMIZATION_LEVEL == 'SPEED':
                thread_count = MAX_CONCURRENT_PAGES  # Maximum parallelization
                dpi = min(dpi, 200)  # Cap DPI for speed
            else:
                thread_count = 1 if PDF_OPTIMIZATION_LEVEL == 'HIGH' else min(MAX_CONCURRENT_PAGES, 2)
            
            # Convert PDF bytes to PIL images
            if page_number:
                # Convert only specific page for speed
                images = convert_from_bytes(
                    pdf_bytes,
                    dpi=dpi,
                    fmt='PNG',
                    thread_count=thread_count,
                    first_page=page_number,
                    last_page=page_number
                )
            else:
                # Convert all pages
                images = convert_from_bytes(
                    pdf_bytes,
                    dpi=dpi,
                    fmt='PNG',
                    thread_count=thread_count
                )
            
            total_pages = len(images)
            logger.info(f"Successfully converted PDF to {total_pages} PNG images")
            
        except Exception as e:
            logger.error(f"Error converting PDF to PNG: {str(e)}")
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': f'Error converting PDF to PNG: {str(e)}'})
            }
        
        # Process each image - always return as base64
        result_images = []
        
        for page_num, image in enumerate(images, page_number or 1):
            try:
                # Convert PIL image to bytes with speed-optimized compression
                img_buffer = BytesIO()
                
                # Apply compression based on optimization level
                if PDF_OPTIMIZATION_LEVEL == 'SPEED':
                    # Maximum speed - minimal compression
                    image.save(img_buffer, format='PNG', optimize=False, compress_level=1)
                elif PDF_OPTIMIZATION_LEVEL == 'HIGH':
                    # High compression for smaller files
                    image.save(img_buffer, format='PNG', optimize=True, compress_level=9)
                else:
                    # Balanced compression for speed
                    image.save(img_buffer, format='PNG', optimize=True, compress_level=6)
                
                img_bytes = img_buffer.getvalue()
                img_size = len(img_bytes)
                
                # Convert to base64
                img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                result_images.append({
                    'page': page_num,
                    'base64': img_base64,
                    'size_bytes': img_size
                })
                
                logger.info(f"Page {page_num}: Generated PNG ({img_size} bytes)")
                
            except Exception as e:
                logger.error(f"Error processing page {page_num}: {str(e)}")
                return {
                    'statusCode': 500,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': f'Error processing page {page_num}: {str(e)}'})
                }
        
        # Return success response
        response_body = {
            'success': True,
            'total_pages': total_pages,
            'dpi': dpi,
            'conversion_type': 'fast',
            'images': result_images
        }
        
        # Include requested page info if specified
        if page_number:
            response_body['requested_page'] = page_number
        
        logger.info(f"Fast PDF to PNG conversion completed successfully: {total_pages} pages")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps(response_body)
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Unexpected error in fast conversion: {str(e)}\nStacktrace: {error_details}")
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'Internal server error: {str(e)}',
                'details': error_details
            })
        }

def handle_standard_conversion(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Standard PDF to PNG conversion with S3 operations (original functionality).
    
    Expected input:
    {
        "pdf_s3_key": "path/to/document.pdf",
        "bucket_name": "optional-bucket-name",
        "output_prefix": "optional-output-prefix", 
        "dpi": 300,  # optional, default 300
        "return_base64": false  # optional, return images as base64 or upload to S3
    }
    
    Returns:
    {
        "statusCode": 200,
        "body": {
            "success": true,
            "total_pages": 3,
            "images": [
                {
                    "page": 1,
                    "s3_key": "converted/document_page_1.png",
                    "size_bytes": 12345
                }
            ]
        }
    }
    """
    try:
        logger.info(f"Starting standard PDF to PNG conversion with event: {json.dumps(event, default=str)}")
        
        # Parse request body
        body = event.get('body', '')
        if event.get('isBase64Encoded', False):
            body = base64.b64decode(body).decode('utf-8')
        
        if isinstance(body, str):
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Invalid JSON in request body'})
                }
        else:
            data = body
        
        logger.info(f"Parsed request data: {json.dumps(data, default=str)}")
        
        # Extract parameters
        pdf_s3_key = data.get('pdf_s3_key')
        bucket_name = data.get('bucket_name', BUCKET_NAME)
        output_prefix = data.get('output_prefix', 'converted')
        dpi = data.get('dpi', 300)
        return_base64 = data.get('return_base64', False)
        
        if not pdf_s3_key:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'pdf_s3_key is required'})
            }
        
        if not bucket_name:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'bucket_name is required (either in request or environment)'})
            }
        
        # Download PDF from S3
        logger.info(f"Downloading PDF from s3://{bucket_name}/{pdf_s3_key}")
        
        try:
            response = s3.get_object(Bucket=bucket_name, Key=pdf_s3_key)
            pdf_bytes = response['Body'].read()
            logger.info(f"Downloaded PDF: {len(pdf_bytes)} bytes")
        except Exception as e:
            logger.error(f"Error downloading PDF from S3: {str(e)}")
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': f'PDF not found in S3: {str(e)}'})
            }
        
        # Convert PDF to PNG images using pdf2image
        logger.info(f"Converting PDF to PNG images with DPI={dpi}")
        
        try:
            # Apply optimization settings for maximum speed
            if PDF_OPTIMIZATION_LEVEL == 'SPEED':
                thread_count = MAX_CONCURRENT_PAGES  # Maximum parallelization
                dpi = min(dpi, 200)  # Cap DPI for speed
            else:
                thread_count = 1 if PDF_OPTIMIZATION_LEVEL == 'HIGH' else MAX_CONCURRENT_PAGES
            
            # Convert PDF bytes to PIL images
            images = convert_from_bytes(
                pdf_bytes,
                dpi=dpi,
                fmt='PNG',
                thread_count=thread_count
            )
            
            total_pages = len(images)
            logger.info(f"Successfully converted PDF to {total_pages} PNG images")
            
        except Exception as e:
            logger.error(f"Error converting PDF to PNG: {str(e)}")
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': f'Error converting PDF to PNG: {str(e)}'})
            }
        
        # Process each image
        result_images = []
        base_filename = os.path.splitext(os.path.basename(pdf_s3_key))[0]
        
        for page_num, image in enumerate(images, 1):
            try:
                # Convert PIL image to bytes with speed-optimized compression
                img_buffer = BytesIO()
                
                # Apply compression based on optimization level
                if PDF_OPTIMIZATION_LEVEL == 'SPEED':
                    # Maximum speed - minimal compression
                    image.save(img_buffer, format='PNG', optimize=False, compress_level=1)
                elif PDF_OPTIMIZATION_LEVEL == 'HIGH':
                    # High compression for smaller files
                    image.save(img_buffer, format='PNG', optimize=True, compress_level=9)
                else:
                    # Balanced compression
                    image.save(img_buffer, format='PNG', optimize=True, compress_level=6)
                
                img_bytes = img_buffer.getvalue()
                img_size = len(img_bytes)
                
                logger.info(f"Page {page_num}: Generated PNG ({img_size} bytes)")
                
                if return_base64:
                    # Return as base64 encoded string
                    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                    result_images.append({
                        'page': page_num,
                        'base64': img_base64,
                        'size_bytes': img_size
                    })
                else:
                    # Upload to S3
                    png_key = f"{output_prefix}/{base_filename}_page_{page_num}.png"
                    
                    try:
                        s3.put_object(
                            Bucket=bucket_name,
                            Key=png_key,
                            Body=img_bytes,
                            ContentType='image/png'
                        )
                        
                        logger.info(f"Page {page_num}: Uploaded to s3://{bucket_name}/{png_key}")
                        
                        result_images.append({
                            'page': page_num,
                            's3_key': png_key,
                            'size_bytes': img_size
                        })
                        
                    except Exception as e:
                        logger.error(f"Error uploading page {page_num} to S3: {str(e)}")
                        return {
                            'statusCode': 500,
                            'headers': {'Content-Type': 'application/json'},
                            'body': json.dumps({'error': f'Error uploading page {page_num} to S3: {str(e)}'})
                        }
                
            except Exception as e:
                logger.error(f"Error processing page {page_num}: {str(e)}")
                return {
                    'statusCode': 500,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': f'Error processing page {page_num}: {str(e)}'})
                }
        
        # Return success response
        response_body = {
            'success': True,
            'total_pages': total_pages,
            'dpi': dpi,
            'source_pdf': pdf_s3_key,
            'conversion_type': 'standard',
            'images': result_images
        }
        
        logger.info(f"Standard PDF to PNG conversion completed successfully: {total_pages} pages")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps(response_body)
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Unexpected error in standard conversion: {str(e)}\nStacktrace: {error_details}")
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'Internal server error: {str(e)}',
                'details': error_details
            })
        } 

def handle_async_conversion(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Initiate asynchronous PDF to PNG conversion.
    
    Expected input:
    {
        "pdf_s3_key": "path/to/document.pdf",
        "bucket_name": "optional-bucket-name",
        "output_prefix": "optional-output-prefix",
        "dpi": 300,
        "return_base64": false,
        "callback_url": "optional-webhook-url"
    }
    
    Returns:
    {
        "statusCode": 202,
        "body": {
            "success": true,
            "job_id": "uuid-string",
            "status": "submitted",
            "message": "Conversion job submitted successfully"
        }
    }
    """
    try:
        logger.info("Starting async PDF to PNG conversion")
        
        if not jobs_table:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'DynamoDB not configured for async processing'})
            }
        
        # Parse request body
        body = event.get('body', '')
        if event.get('isBase64Encoded', False):
            body = base64.b64decode(body).decode('utf-8')
        
        if isinstance(body, str):
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Invalid JSON in request body'})
                }
        else:
            data = body
        
        # Extract parameters
        pdf_s3_key = data.get('pdf_s3_key')
        bucket_name = data.get('bucket_name', BUCKET_NAME)
        output_prefix = data.get('output_prefix', 'converted')
        dpi = data.get('dpi', 300)
        return_base64 = data.get('return_base64', False)
        callback_url = data.get('callback_url')
        
        if not pdf_s3_key:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'pdf_s3_key is required'})
            }
        
        if not bucket_name:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'bucket_name is required'})
            }
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        current_time = datetime.utcnow()
        ttl = int((current_time + timedelta(days=7)).timestamp())
        
        # Create job record in DynamoDB
        job_item = {
            'job_id': job_id,
            'status': 'submitted',
            'created_at': current_time.isoformat(),
            'updated_at': current_time.isoformat(),
            'pdf_s3_key': pdf_s3_key,
            'bucket_name': bucket_name,
            'output_prefix': output_prefix,
            'dpi': dpi,
            'return_base64': return_base64,
            'callback_url': callback_url,
            'ttl': ttl
        }
        
        try:
            jobs_table.put_item(Item=job_item)
            logger.info(f"Created job record for job_id: {job_id}")
        except Exception as e:
            logger.error(f"Error creating job record: {str(e)}")
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': f'Error creating job record: {str(e)}'})
            }
        
        # Start background processing
        try:
            threading.Thread(
                target=process_async_conversion,
                args=(job_id, job_item),
                daemon=True
            ).start()
            logger.info(f"Started background processing for job_id: {job_id}")
        except Exception as e:
            logger.error(f"Error starting background processing: {str(e)}")
            # Update job status to failed
            try:
                jobs_table.update_item(
                    Key={'job_id': job_id},
                    UpdateExpression='SET #status = :status, updated_at = :updated_at, error_message = :error',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'failed',
                        ':updated_at': datetime.utcnow().isoformat(),
                        ':error': str(e)
                    }
                )
            except Exception:
                pass
            
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': f'Error starting background processing: {str(e)}'})
            }
        
        # Return success response
        return {
            'statusCode': 202,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'job_id': job_id,
                'status': 'submitted',
                'message': 'Conversion job submitted successfully'
            })
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Unexpected error in async conversion: {str(e)}\nStacktrace: {error_details}")
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'Internal server error: {str(e)}',
                'details': error_details
            })
        }

def handle_job_status(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Get the status of an async conversion job.
    
    Returns:
    {
        "statusCode": 200,
        "body": {
            "success": true,
            "job_id": "uuid-string",
            "status": "completed|processing|failed|submitted",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:05:00",
            "progress": 75,
            "total_pages": 3,
            "images": [...] // Only if completed
        }
    }
    """
    try:
        logger.info("Getting job status")
        
        if not jobs_table:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'DynamoDB not configured for async processing'})
            }
        
        # Extract job_id from path
        path = event.get('path', '')
        job_id = path.split('/')[-1]
        
        if not job_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'job_id is required'})
            }
        
        # Get job from DynamoDB
        try:
            response = jobs_table.get_item(Key={'job_id': job_id})
            job_item = response.get('Item')
            
            if not job_item:
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Job not found'})
                }
            
        except Exception as e:
            logger.error(f"Error getting job from DynamoDB: {str(e)}")
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': f'Error getting job status: {str(e)}'})
            }
        
        # Return job status
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'job_id': job_item['job_id'],
                'status': job_item['status'],
                'created_at': job_item['created_at'],
                'updated_at': job_item['updated_at'],
                'progress': job_item.get('progress', 0),
                'total_pages': job_item.get('total_pages'),
                'images': job_item.get('images', []),
                'error_message': job_item.get('error_message')
            })
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Unexpected error in job status: {str(e)}\nStacktrace: {error_details}")
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'Internal server error: {str(e)}',
                'details': error_details
            })
        }

def handle_jobs_list(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    List jobs with optional filtering.
    
    Query parameters:
    - status: Filter by status (submitted, processing, completed, failed)
    - limit: Maximum number of jobs to return (default: 50)
    
    Returns:
    {
        "statusCode": 200,
        "body": {
            "success": true,
            "jobs": [
                {
                    "job_id": "uuid-string",
                    "status": "completed",
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:05:00"
                }
            ],
            "count": 1
        }
    }
    """
    try:
        logger.info("Listing jobs")
        
        if not jobs_table:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'DynamoDB not configured for async processing'})
            }
        
        # Extract query parameters
        query_params = event.get('queryStringParameters', {}) or {}
        status_filter = query_params.get('status')
        limit = int(query_params.get('limit', '50'))
        
        try:
            if status_filter:
                # Use GSI to filter by status
                response = jobs_table.query(
                    IndexName='status-index',
                    KeyConditionExpression='#status = :status',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={':status': status_filter},
                    Limit=limit,
                    ScanIndexForward=False  # Latest first
                )
            else:
                # Scan all jobs
                response = jobs_table.scan(Limit=limit)
                
            jobs = response.get('Items', [])
            
            # Sort by created_at desc if not using GSI
            if not status_filter:
                jobs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            # Clean up job items for response
            clean_jobs = []
            for job in jobs:
                clean_job = {
                    'job_id': job['job_id'],
                    'status': job['status'],
                    'created_at': job['created_at'],
                    'updated_at': job['updated_at'],
                    'progress': job.get('progress', 0),
                    'total_pages': job.get('total_pages'),
                    'pdf_s3_key': job.get('pdf_s3_key')
                }
                if job.get('error_message'):
                    clean_job['error_message'] = job['error_message']
                clean_jobs.append(clean_job)
            
        except Exception as e:
            logger.error(f"Error listing jobs from DynamoDB: {str(e)}")
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': f'Error listing jobs: {str(e)}'})
            }
        
        # Return jobs list
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'jobs': clean_jobs,
                'count': len(clean_jobs)
            })
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Unexpected error in jobs list: {str(e)}\nStacktrace: {error_details}")
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'Internal server error: {str(e)}',
                'details': error_details
            })
        } 

def process_async_conversion(job_id: str, job_item: Dict[str, Any]) -> None:
    """
    Process async PDF conversion in background thread.
    Updates job status in DynamoDB as processing progresses.
    """
    try:
        logger.info(f"Starting background processing for job_id: {job_id}")
        
        # Update job status to processing
        jobs_table.update_item(
            Key={'job_id': job_id},
            UpdateExpression='SET #status = :status, updated_at = :updated_at, progress = :progress',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'processing',
                ':updated_at': datetime.utcnow().isoformat(),
                ':progress': 10
            }
        )
        
        # Extract job parameters
        pdf_s3_key = job_item['pdf_s3_key']
        bucket_name = job_item['bucket_name']
        output_prefix = job_item['output_prefix']
        dpi = job_item['dpi']
        return_base64 = job_item['return_base64']
        callback_url = job_item.get('callback_url')
        
        # Download PDF from S3
        logger.info(f"Downloading PDF from s3://{bucket_name}/{pdf_s3_key}")
        
        try:
            response = s3.get_object(Bucket=bucket_name, Key=pdf_s3_key)
            pdf_bytes = response['Body'].read()
            logger.info(f"Downloaded PDF: {len(pdf_bytes)} bytes")
            
            # Update progress
            jobs_table.update_item(
                Key={'job_id': job_id},
                UpdateExpression='SET updated_at = :updated_at, progress = :progress',
                ExpressionAttributeValues={
                    ':updated_at': datetime.utcnow().isoformat(),
                    ':progress': 20
                }
            )
            
        except Exception as e:
            logger.error(f"Error downloading PDF from S3: {str(e)}")
            jobs_table.update_item(
                Key={'job_id': job_id},
                UpdateExpression='SET #status = :status, updated_at = :updated_at, error_message = :error',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'failed',
                    ':updated_at': datetime.utcnow().isoformat(),
                    ':error': f'Error downloading PDF: {str(e)}'
                }
            )
            return
        
        # Convert PDF to PNG images with optimizations
        logger.info(f"Converting PDF to PNG images with DPI={dpi}")
        
        try:
            # Apply optimization settings
            thread_count = 1 if PDF_OPTIMIZATION_LEVEL == 'HIGH' else MAX_CONCURRENT_PAGES
            
            # Convert PDF bytes to PIL images
            images = convert_from_bytes(
                pdf_bytes,
                dpi=dpi,
                fmt='PNG',
                thread_count=thread_count
            )
            
            total_pages = len(images)
            logger.info(f"Successfully converted PDF to {total_pages} PNG images")
            
            # Update progress with total pages
            jobs_table.update_item(
                Key={'job_id': job_id},
                UpdateExpression='SET updated_at = :updated_at, progress = :progress, total_pages = :total_pages',
                ExpressionAttributeValues={
                    ':updated_at': datetime.utcnow().isoformat(),
                    ':progress': 40,
                    ':total_pages': total_pages
                }
            )
            
        except Exception as e:
            logger.error(f"Error converting PDF to PNG: {str(e)}")
            jobs_table.update_item(
                Key={'job_id': job_id},
                UpdateExpression='SET #status = :status, updated_at = :updated_at, error_message = :error',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'failed',
                    ':updated_at': datetime.utcnow().isoformat(),
                    ':error': f'Error converting PDF: {str(e)}'
                }
            )
            return
        
        # Process each image with progress updates
        result_images = []
        base_filename = os.path.splitext(os.path.basename(pdf_s3_key))[0]
        
        for page_num, image in enumerate(images, 1):
            try:
                # Convert PIL image to bytes with optimization
                img_buffer = BytesIO()
                
                # Apply compression based on optimization level
                if PDF_OPTIMIZATION_LEVEL == 'HIGH':
                    # High compression for smaller files
                    image.save(img_buffer, format='PNG', optimize=True, compress_level=9)
                else:
                    # Balanced compression
                    image.save(img_buffer, format='PNG', optimize=True, compress_level=6)
                
                img_bytes = img_buffer.getvalue()
                img_size = len(img_bytes)
                
                logger.info(f"Page {page_num}: Generated PNG ({img_size} bytes)")
                
                if return_base64:
                    # Return as base64 encoded string
                    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                    result_images.append({
                        'page': page_num,
                        'base64': img_base64,
                        'size_bytes': img_size
                    })
                else:
                    # Upload to S3
                    png_key = f"{output_prefix}/{base_filename}_page_{page_num}.png"
                    
                    try:
                        s3.put_object(
                            Bucket=bucket_name,
                            Key=png_key,
                            Body=img_bytes,
                            ContentType='image/png'
                        )
                        
                        logger.info(f"Page {page_num}: Uploaded to s3://{bucket_name}/{png_key}")
                        
                        result_images.append({
                            'page': page_num,
                            's3_key': png_key,
                            'size_bytes': img_size
                        })
                        
                    except Exception as e:
                        logger.error(f"Error uploading page {page_num} to S3: {str(e)}")
                        jobs_table.update_item(
                            Key={'job_id': job_id},
                            UpdateExpression='SET #status = :status, updated_at = :updated_at, error_message = :error',
                            ExpressionAttributeNames={'#status': 'status'},
                            ExpressionAttributeValues={
                                ':status': 'failed',
                                ':updated_at': datetime.utcnow().isoformat(),
                                ':error': f'Error uploading page {page_num}: {str(e)}'
                            }
                        )
                        return
                
                # Update progress for each page
                progress = 40 + int((page_num / total_pages) * 50)
                jobs_table.update_item(
                    Key={'job_id': job_id},
                    UpdateExpression='SET updated_at = :updated_at, progress = :progress',
                    ExpressionAttributeValues={
                        ':updated_at': datetime.utcnow().isoformat(),
                        ':progress': progress
                    }
                )
                
            except Exception as e:
                logger.error(f"Error processing page {page_num}: {str(e)}")
                jobs_table.update_item(
                    Key={'job_id': job_id},
                    UpdateExpression='SET #status = :status, updated_at = :updated_at, error_message = :error',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'failed',
                        ':updated_at': datetime.utcnow().isoformat(),
                        ':error': f'Error processing page {page_num}: {str(e)}'
                    }
                )
                return
        
        # Update job status to completed
        jobs_table.update_item(
            Key={'job_id': job_id},
            UpdateExpression='SET #status = :status, updated_at = :updated_at, progress = :progress, images = :images',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'completed',
                ':updated_at': datetime.utcnow().isoformat(),
                ':progress': 100,
                ':images': result_images
            }
        )
        
        logger.info(f"Async PDF to PNG conversion completed successfully for job_id: {job_id}")
        
        # Call webhook if provided
        if callback_url:
            try:
                import urllib.request
                import urllib.parse
                
                callback_data = {
                    'job_id': job_id,
                    'status': 'completed',
                    'total_pages': total_pages,
                    'images': result_images
                }
                
                data = urllib.parse.urlencode(callback_data).encode('utf-8')
                req = urllib.request.Request(callback_url, data=data)
                urllib.request.urlopen(req, timeout=10)
                
                logger.info(f"Callback sent successfully for job_id: {job_id}")
                
            except Exception as e:
                logger.warning(f"Error sending callback for job_id {job_id}: {str(e)}")
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Unexpected error in async processing for job_id {job_id}: {str(e)}\nStacktrace: {error_details}")
        
        # Update job status to failed
        try:
            jobs_table.update_item(
                Key={'job_id': job_id},
                UpdateExpression='SET #status = :status, updated_at = :updated_at, error_message = :error',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'failed',
                    ':updated_at': datetime.utcnow().isoformat(),
                    ':error': f'Unexpected error: {str(e)}'
                }
            )
        except Exception:
            pass 
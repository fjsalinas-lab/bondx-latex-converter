import os
import json
import boto3
import logging
from io import BytesIO
from pdf2image import convert_from_bytes
import base64
from typing import List, Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize S3 client
s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get('BUCKET_NAME')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Convert PDF to PNG images using pdf2image.
    
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
        logger.info(f"Starting PDF to PNG conversion with event: {json.dumps(event, default=str)}")
        
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
            # Convert PDF bytes to PIL images
            images = convert_from_bytes(
                pdf_bytes,
                dpi=dpi,
                fmt='PNG',
                thread_count=1  # Conservative for Lambda
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
                # Convert PIL image to bytes
                img_buffer = BytesIO()
                image.save(img_buffer, format='PNG', optimize=True)
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
            'images': result_images
        }
        
        logger.info(f"PDF to PNG conversion completed successfully: {total_pages} pages")
        
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
        logger.error(f"Unexpected error: {str(e)}\nStacktrace: {error_details}")
        
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
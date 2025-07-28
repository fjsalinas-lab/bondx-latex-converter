import os
import json
import boto3
import logging
import base64
import re
from requests_toolbelt.multipart import decoder
from typing import Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize S3 client
s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get('BUCKET_NAME')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Upload a document to S3, following the business logic described by the user.
    Expects multipart/form-data with fields:
      - file (required)
      - document_type (required)
      - id_pagare (optional)
      - user_id (optional, depending on auth)
    Returns JSON with S3 key, download URL, and metadata.
    """
    try:
        logger.info(f"Starting document upload with event: {json.dumps(event, default=str)}")

        # Parse multipart/form-data
        content_type = event['headers'].get('content-type') or event['headers'].get('Content-Type')
        body = event['body']
        if event.get('isBase64Encoded', False):
            body = base64.b64decode(body)
        else:
            body = body.encode() if isinstance(body, str) else body

        multipart_data = decoder.MultipartDecoder(body, content_type)

        file_content = None
        file_name = None
        file_type = None
        document_type = None
        id_pagare = None
        user_id = None

        for part in multipart_data.parts:
            content_disposition = part.headers[b'Content-Disposition'].decode()
            if 'name="file"' in content_disposition:
                file_content = part.content
                if 'filename="' in content_disposition:
                    file_name = content_disposition.split('filename="')[1].split('"')[0]
                file_type = part.headers.get(b'Content-Type', b'').decode()
            elif 'name="document_type"' in content_disposition:
                document_type = part.text
            elif 'name="id_pagare"' in content_disposition:
                id_pagare = part.text
            elif 'name="user_id"' in content_disposition:
                user_id = part.text

        if not file_content or not document_type:
            return {
                "statusCode": 400,
                "headers": {'Content-Type': 'application/json'},
                "body": json.dumps({"error": "Missing required fields"})
            }

        # Lógica para association_value (numero_pagare)
        association_value = None
        if id_pagare:
            match = re.search(r'PAGARE_(\d+)_', file_name or "")
            if match:
                association_value = match.group(1)
            else:
                association_value = id_pagare

        # Generar el key igual que en backend
        s3_key = f"documents/{'PAGARE_' + str(association_value) + '_' if association_value else ''}{file_name}"

        # Subir a S3
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=file_content,
            ContentType=file_type
        )

        # Generar URL de descarga (presignada)
        download_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=3600
        )

        response = {
            "s3_key": s3_key,
            "file_name": file_name,
            "file_type": file_type,
            "file_size": len(file_content),
            "document_type": document_type,
            "id_pagare": id_pagare,
            "association_value": association_value,
            "download_url": download_url
        }

        logger.info(f"Document uploaded successfully: {json.dumps(response)}")

        return {
            "statusCode": 200,
            "headers": {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            "body": json.dumps(response)
        }

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Unexpected error: {str(e)}\nStacktrace: {error_details}")
        return {
            "statusCode": 500,
            "headers": {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            "body": json.dumps({
                'error': f'Internal server error: {str(e)}',
                'details': error_details
            })
        } 
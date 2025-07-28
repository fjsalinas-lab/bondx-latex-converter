# upload-document-service

Microservicio para subir documentos a S3, siguiendo la lógica de negocio de BondX. Recibe archivos grandes vía multipart/form-data y devuelve la URL presignada y metadatos.

## Uso

- Endpoint: POST /upload-document
- Formato: multipart/form-data
- Campos:
  - file (archivo, requerido)
  - document_type (str, requerido)
  - id_pagare (opcional)
  - user_id (opcional)

## Despliegue

1. Construir la imagen Docker:
   ```sh
   docker build -t upload-document-service lambda/
   ```
2. Definir la variable de entorno `BUCKET_NAME`.
3. Desplegar en Lambda o ECS según tu infraestructura.

## Respuesta
```json
{
  "s3_key": "documents/PAGARE_1234_original.pdf",
  "file_name": "original.pdf",
  "file_type": "application/pdf",
  "file_size": 123456,
  "document_type": "pagare",
  "id_pagare": "1234",
  "association_value": "1234",
  "download_url": "https://..."
}
``` 
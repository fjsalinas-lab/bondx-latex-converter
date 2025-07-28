from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_apigateway as apigw,
    aws_iam as iam,
    RemovalPolicy,
    CfnOutput
)
from constructs import Construct

class UploadDocumentStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Referenciar el bucket existente (no creamos uno nuevo)
        storage_bucket = s3.Bucket.from_bucket_name(
            self, "ExistingBucket",
            bucket_name="bondx-bucket"
        )

        # Función Lambda para Upload Document con Docker
        upload_document_function = _lambda.DockerImageFunction(
            self, "UploadDocumentFunction",
            function_name="bondx-upload-document",  # Nombre único
            code=_lambda.DockerImageCode.from_image_asset("lambda"),
            memory_size=1024,  # Aumentado para archivos de hasta 10MB
            timeout=Duration.minutes(3),  # Aumentado para uploads grandes
            environment={
                "BUCKET_NAME": storage_bucket.bucket_name
            },
            architecture=_lambda.Architecture.X86_64
        )

        # Dar permisos completos a la Lambda para el bucket S3
        storage_bucket.grant_read_write(upload_document_function)

        # API Gateway REST API independiente
        upload_api = apigw.RestApi(
            self, "UploadDocumentApi",
            rest_api_name="upload-document-api",
            description="API independiente para subida de documentos",
            binary_media_types=["multipart/form-data", "*/*"],  # Crucial para uploads
        )

        # Endpoint /upload para subida de documentos
        upload_integration = apigw.LambdaIntegration(
            upload_document_function,
            proxy=True,
            timeout=Duration.seconds(29),  # Máximo permitido para API Gateway
        )
        
        upload_resource = upload_api.root.add_resource("upload")
        
        # Método POST para upload
        upload_resource.add_method("POST", upload_integration, 
            method_responses=[{
                'statusCode': '200',
                'responseParameters': {
                    'method.response.header.Access-Control-Allow-Origin': True,
                    'method.response.header.Access-Control-Allow-Headers': True,
                    'method.response.header.Access-Control-Allow-Methods': True
                }
            }, {
                'statusCode': '400',
                'responseParameters': {
                    'method.response.header.Access-Control-Allow-Origin': True
                }
            }, {
                'statusCode': '500',
                'responseParameters': {
                    'method.response.header.Access-Control-Allow-Origin': True
                }
            }]
        )
        
        # Método OPTIONS para CORS preflight
        upload_resource.add_method("OPTIONS", 
            apigw.MockIntegration(
                integration_responses=[{
                    'statusCode': '200',
                    'responseParameters': {
                        'method.response.header.Access-Control-Allow-Origin': "'*'",
                        'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                        'method.response.header.Access-Control-Allow-Methods': "'POST,OPTIONS'"
                    },
                    'responseTemplates': {
                        'application/json': ''
                    }
                }],
                request_templates={
                    'application/json': '{"statusCode": 200}'
                }
            ),
            method_responses=[{
                'statusCode': '200',
                'responseParameters': {
                    'method.response.header.Access-Control-Allow-Origin': True,
                    'method.response.header.Access-Control-Allow-Headers': True,
                    'method.response.header.Access-Control-Allow-Methods': True
                }
            }]
        )

        # Endpoint /health para health check
        health_integration = apigw.MockIntegration(
            integration_responses=[{
                'statusCode': '200',
                'responseTemplates': {
                    'application/json': '{"status": "healthy", "service": "upload-document"}'
                }
            }],
            request_templates={
                'application/json': '{"statusCode": 200}'
            }
        )
        
        health_resource = upload_api.root.add_resource("health")
        health_resource.add_method("GET", health_integration,
            method_responses=[{
                'statusCode': '200',
                'responseModels': {
                    'application/json': apigw.Model.EMPTY_MODEL
                }
            }]
        )

        # Outputs importantes
        CfnOutput(self, "UploadDocumentFunctionName",
            value=upload_document_function.function_name,
            description="Nombre de la función Lambda Upload Document",
            export_name="UploadDocumentFunctionName"
        )

        CfnOutput(self, "UploadDocumentApiUrl",
            value=upload_api.url,
            description="URL base del API Gateway Upload Document",
            export_name="UploadDocumentApiUrl"
        )
        
        CfnOutput(self, "UploadDocumentUploadEndpoint",
            value=f"{upload_api.url}upload",
            description="Endpoint completo para subida de documentos",
            export_name="UploadDocumentUploadEndpoint"
        )

        CfnOutput(self, "UploadDocumentHealthEndpoint",
            value=f"{upload_api.url}health",
            description="Endpoint de health check",
            export_name="UploadDocumentHealthEndpoint"
        ) 
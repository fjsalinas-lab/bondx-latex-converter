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

class PdfToPngStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Referenciar el bucket existente (no creamos uno nuevo)
        storage_bucket = s3.Bucket.from_bucket_name(
            self, "ExistingBucket",
            bucket_name="bondx-bucket"
        )

        # Función Lambda para PDF a PNG con Docker
        pdf_to_png_function = _lambda.DockerImageFunction(
            self, "PdfToPngConverterFunction",
            function_name="bondx-pdf-to-png-converter",  # Nombre único
            code=_lambda.DockerImageCode.from_image_asset("lambda"),
            memory_size=1536,  # 1.5GB de memoria para procesamiento de imágenes
            timeout=Duration.minutes(5),  # Timeout de 5 minutos para PDFs grandes
            environment={
                "BUCKET_NAME": storage_bucket.bucket_name
            },
            architecture=_lambda.Architecture.X86_64
        )

        # Dar permisos completos a la Lambda para el bucket S3
        storage_bucket.grant_read_write(pdf_to_png_function)

        # API Gateway REST API independiente
        pdf_api = apigw.RestApi(
            self, "PdfToPngApi",
            rest_api_name="pdf-to-png-api",
            description="API independiente para conversión PDF a PNG",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=["POST", "OPTIONS"],
                allow_headers=["Content-Type", "Authorization"]
            )
        )

        # Endpoint /convert para conversión PDF a PNG
        pdf_integration = apigw.LambdaIntegration(
            pdf_to_png_function,
            proxy=True,
            timeout=Duration.seconds(300),  # 5 minutos de timeout para la integración
            integration_responses=[{
                'statusCode': '200',
                'responseParameters': {
                    'method.response.header.Access-Control-Allow-Origin': "'*'"
                }
            }]
        )
        
        convert_resource = pdf_api.root.add_resource("convert")
        convert_resource.add_method("POST", pdf_integration, 
            method_responses=[{
                'statusCode': '200',
                'responseParameters': {
                    'method.response.header.Access-Control-Allow-Origin': True
                }
            }]
        )

        # Endpoint /health para health check
        health_integration = apigw.MockIntegration(
            integration_responses=[{
                'statusCode': '200',
                'responseTemplates': {
                    'application/json': '{"status": "healthy", "service": "pdf-to-png"}'
                }
            }],
            request_templates={
                'application/json': '{"statusCode": 200}'
            }
        )
        
        health_resource = pdf_api.root.add_resource("health")
        health_resource.add_method("GET", health_integration,
            method_responses=[{
                'statusCode': '200',
                'responseModels': {
                    'application/json': apigw.Model.EMPTY_MODEL
                }
            }]
        )

        # Outputs importantes
        CfnOutput(self, "PdfToPngFunctionName",
            value=pdf_to_png_function.function_name,
            description="Nombre de la función Lambda PDF to PNG",
            export_name="PdfToPngFunctionName"
        )

        CfnOutput(self, "PdfToPngApiUrl",
            value=pdf_api.url,
            description="URL base del API Gateway PDF to PNG",
            export_name="PdfToPngApiUrl"
        )
        
        CfnOutput(self, "PdfToPngConvertEndpoint",
            value=f"{pdf_api.url}convert",
            description="Endpoint completo para conversión PDF a PNG",
            export_name="PdfToPngConvertEndpoint"
        )

        CfnOutput(self, "PdfToPngHealthEndpoint",
            value=f"{pdf_api.url}health",
            description="Endpoint de health check",
            export_name="PdfToPngHealthEndpoint"
        ) 
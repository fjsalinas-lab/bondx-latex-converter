from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_apigateway as apigw,
    aws_iam as iam,
    aws_dynamodb as dynamodb,
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

        # Tabla DynamoDB para tracking de jobs de conversión asíncrona
        jobs_table = dynamodb.Table(
            self, "PdfToPngJobsTable",
            table_name="pdf-to-png-jobs",
            partition_key=dynamodb.Attribute(
                name="job_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery=True,
            # TTL para limpiar jobs antiguos automáticamente (7 días)
            time_to_live_attribute="ttl"
        )

        # Índice secundario para consultar jobs por estado
        jobs_table.add_global_secondary_index(
            index_name="status-index",
            partition_key=dynamodb.Attribute(
                name="status",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at",
                type=dynamodb.AttributeType.STRING
            )
        )

        # Función Lambda para PDF a PNG con Docker
        pdf_to_png_function = _lambda.DockerImageFunction(
            self, "PdfToPngConverterFunction",
            function_name="bondx-pdf-to-png-converter",  # Nombre único
            code=_lambda.DockerImageCode.from_image_asset("lambda"),
            memory_size=3008,  # 3GB de memoria para procesamiento de imágenes grandes
            timeout=Duration.minutes(15),  # Timeout de 15 minutos para PDFs muy grandes
            environment={
                "BUCKET_NAME": storage_bucket.bucket_name,
                "JOBS_TABLE_NAME": jobs_table.table_name,
                "PDF_OPTIMIZATION_LEVEL": "SPEED",  # SPEED para máxima velocidad
                "MAX_CONCURRENT_PAGES": "8",  # Más paralelización
                "COMPRESSION_QUALITY": "60"  # Menor calidad, más velocidad
            },
            architecture=_lambda.Architecture.X86_64,
            reserved_concurrent_executions=10  # Limitar concurrencia para evitar sobrecarga
        )

        # Dar permisos completos a la Lambda para el bucket S3
        storage_bucket.grant_read_write(pdf_to_png_function)

        # Dar permisos de lectura/escritura a la Lambda para la tabla DynamoDB
        jobs_table.grant_read_write_data(pdf_to_png_function)

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
            timeout=Duration.seconds(29),  # Máximo permitido por API Gateway
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

        # Endpoint /convert-fast para conversión rápida sin S3
        fast_integration = apigw.LambdaIntegration(
            pdf_to_png_function,
            proxy=True,
            timeout=Duration.seconds(29),  # Máximo permitido por API Gateway
            integration_responses=[{
                'statusCode': '200',
                'responseParameters': {
                    'method.response.header.Access-Control-Allow-Origin': "'*'"
                }
            }]
        )
        
        convert_fast_resource = pdf_api.root.add_resource("convert-fast")
        convert_fast_resource.add_method("POST", fast_integration,
            method_responses=[{
                'statusCode': '200',
                'responseParameters': {
                    'method.response.header.Access-Control-Allow-Origin': True
                }
            }]
        )

        # Endpoint /convert-async para conversión asíncrona
        async_integration = apigw.LambdaIntegration(
            pdf_to_png_function,
            proxy=True,
            timeout=Duration.seconds(29),  # Máximo permitido por API Gateway
            integration_responses=[{
                'statusCode': '200',
                'responseParameters': {
                    'method.response.header.Access-Control-Allow-Origin': "'*'"
                }
            }]
        )
        
        convert_async_resource = pdf_api.root.add_resource("convert-async")
        convert_async_resource.add_method("POST", async_integration,
            method_responses=[{
                'statusCode': '200',
                'responseParameters': {
                    'method.response.header.Access-Control-Allow-Origin': True
                }
            }]
        )

        # Endpoint /job-status/{job_id} para verificar estado de jobs
        job_status_resource = pdf_api.root.add_resource("job-status")
        job_id_resource = job_status_resource.add_resource("{job_id}")
        job_id_resource.add_method("GET", async_integration,
            method_responses=[{
                'statusCode': '200',
                'responseParameters': {
                    'method.response.header.Access-Control-Allow-Origin': True
                }
            }]
        )

        # Endpoint /jobs para listar jobs (opcional)
        jobs_resource = pdf_api.root.add_resource("jobs")
        jobs_resource.add_method("GET", async_integration,
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

        CfnOutput(self, "PdfToPngConvertFastEndpoint",
            value=f"{pdf_api.url}convert-fast",
            description="Endpoint rápido para conversión PDF a PNG sin S3",
            export_name="PdfToPngConvertFastEndpoint"
        )

        CfnOutput(self, "PdfToPngHealthEndpoint",
            value=f"{pdf_api.url}health",
            description="Endpoint de health check",
            export_name="PdfToPngHealthEndpoint"
        )

        CfnOutput(self, "PdfToPngConvertAsyncEndpoint",
            value=f"{pdf_api.url}convert-async",
            description="Endpoint para conversión asíncrona PDF a PNG",
            export_name="PdfToPngConvertAsyncEndpoint"
        )

        CfnOutput(self, "PdfToPngJobStatusEndpoint",
            value=f"{pdf_api.url}job-status/{{job_id}}",
            description="Endpoint para verificar estado de jobs",
            export_name="PdfToPngJobStatusEndpoint"
        )

        CfnOutput(self, "PdfToPngJobsEndpoint",
            value=f"{pdf_api.url}jobs",
            description="Endpoint para listar jobs",
            export_name="PdfToPngJobsEndpoint"
        )

        CfnOutput(self, "JobsTableName",
            value=jobs_table.table_name,
            description="Nombre de la tabla DynamoDB para jobs",
            export_name="PdfToPngJobsTableName"
        ) 
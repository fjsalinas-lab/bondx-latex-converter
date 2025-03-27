from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_apigateway as apigw,
    RemovalPolicy
)
from constructs import Construct

class BondxLatexConverterStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Usar el bucket existente
        storage_bucket = s3.Bucket.from_bucket_name(
            self, "ExistingBucket",
            bucket_name="bondx-bucket"
        )

        # Bucket para metadata (requerido por CDK)
        metadata_bucket = s3.Bucket(
            self, "LatexConverterMetadataBucket",
            removal_policy=RemovalPolicy.RETAIN,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL
        )

        # Función Lambda con Docker
        latex_function = _lambda.DockerImageFunction(
            self, "LatexConverterFunction",
            code=_lambda.DockerImageCode.from_image_asset("lambda"),
            memory_size=2048,  # 2GB de memoria para procesamiento de LaTeX
            timeout=Duration.minutes(5),  # Timeout de 5 minutos
            environment={
                "BUCKET_NAME": storage_bucket.bucket_name
            },
            architecture=_lambda.Architecture.X86_64  # Forzar arquitectura x86_64
        )

        # Dar permisos a la Lambda para acceder al bucket
        storage_bucket.grant_read_write(latex_function)

        # API Gateway REST API
        api = apigw.RestApi(
            self, "LatexConverterApi",
            rest_api_name="latex-converter-api",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,  # En producción, especificar dominio
                allow_methods=["POST", "OPTIONS"]
            )
        )

        # Endpoint /convert
        convert_integration = apigw.LambdaIntegration(latex_function)
        api.root.add_resource("convert").add_method("POST", convert_integration)

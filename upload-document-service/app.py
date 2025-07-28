#!/usr/bin/env python3
import os
import aws_cdk as cdk
from upload_document_stack.upload_document_stack import UploadDocumentStack

app = cdk.App()

UploadDocumentStack(app, "BondxUploadDocumentStack",
    description="Microservicio independiente para subida de documentos",
    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region='us-east-2'  # Misma región que tu stack actual
    ),
)

app.synth() 
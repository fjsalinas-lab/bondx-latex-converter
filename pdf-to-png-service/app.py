#!/usr/bin/env python3
import os
import aws_cdk as cdk
from pdf_to_png_stack.pdf_to_png_stack import PdfToPngStack

app = cdk.App()

PdfToPngStack(app, "BondxPdfToPngStack",
    description="Microservicio independiente para conversión PDF a PNG",
    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region='us-east-2'  # Misma región que tu stack actual
    ),
)

app.synth() 
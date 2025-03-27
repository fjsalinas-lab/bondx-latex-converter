import aws_cdk as core
import aws_cdk.assertions as assertions

from bondx_latex_converter.bondx_latex_converter_stack import BondxLatexConverterStack

# example tests. To run these tests, uncomment this file along with the example
# resource in bondx_latex_converter/bondx_latex_converter_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = BondxLatexConverterStack(app, "bondx-latex-converter")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })

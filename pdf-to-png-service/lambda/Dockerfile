# Use AWS Lambda Python 3.11 base image
FROM public.ecr.aws/lambda/python:3.11

# Install system dependencies required for pdf2image
RUN yum update -y && \
    yum install -y \
    poppler-utils \
    && yum clean all

# Copy requirements and install Python dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install --no-cache-dir -r requirements.txt

# Copy function code
COPY handler.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler
CMD [ "handler.lambda_handler" ] 
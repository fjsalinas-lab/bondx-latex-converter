FROM public.ecr.aws/lambda/python:3.11

# Install system dependencies
RUN yum update -y && \
    yum install -y \
    wget \
    tar \
    gzip \
    file \
    file-libs \
    && yum clean all && \
    rm -rf /var/cache/yum

# Install Python dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Install Pandoc
RUN wget https://github.com/jgm/pandoc/releases/download/3.1.11/pandoc-3.1.11-linux-amd64.tar.gz && \
    tar xvzf pandoc-3.1.11-linux-amd64.tar.gz --strip-components 1 -C /usr/local && \
    rm pandoc-3.1.11-linux-amd64.tar.gz

# Verify installations
RUN pandoc --version && \
    python -c "import magic; print('python-magic installed successfully')"

# Copy function code
COPY handler.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler
CMD [ "handler.lambda_handler" ]
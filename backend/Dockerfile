FROM nvidia/cuda:12.6.0-runtime-ubuntu22.04
# FROM python:3.12.10  
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Kathmandu
 
WORKDIR /app
 
# Add deadsnakes PPA and install Python 3.12
RUN apt-get update && apt-get install -y \
    software-properties-common \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    tesseract-ocr \
    libxrender1 \
    libxext6 \
    poppler-utils \ 
    && add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update && \
    apt-get install -y \
    python3.12 python3.12-venv python3-pip \
    libpq-dev gcc curl git \
    && rm -rf /var/lib/apt/lists/*
 
# Create virtualenv
RUN python3.12 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
 
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
 
RUN mkdir -p /app/.yolo_config

# COPY entrypoint.sh /usr/local/bin/entrypoint
# RUN chmod +x /usr/local/bin/entrypoint

COPY . .
RUN python manage.py collectstatic --noinput
# COPY entrypoint.sh /app/entrypoint.sh
# ENTRYPOINT ["/app/entrypoint.sh"]
# RUN chmod +x /app/entrypoint.sh
 
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
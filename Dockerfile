FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app
COPY . /app

# Install system libraries required for PDF/image processing (provides libGL.so.1)
RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
	   libgl1 \
	   libglib2.0-0 \
	   libsm6 \
	   libxrender1 \
	   libxext6 \
	   poppler-utils \
	&& rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt
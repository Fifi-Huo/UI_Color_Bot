# NVIDIA NIM Base Image for Color Extraction Service
# Using NVIDIA CUDA base image for GPU acceleration support
FROM nvcr.io/nvidia/cuda:12.2-devel-ubuntu22.04

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV CUDA_VISIBLE_DEVICES=0

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    cmake \
    git \
    wget \
    curl \
    libopencv-dev \
    python3-opencv \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install Python dependencies
RUN python3 -m pip install --upgrade pip setuptools wheel

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Install NVIDIA cuML and RAPIDS (for GPU acceleration)
# Note: This requires NVIDIA GPU and proper CUDA setup
RUN pip3 install --no-cache-dir \
    cuml-cu12==23.10.* \
    cudf-cu12==23.10.* \
    cupy-cuda12x==12.3.0 \
    || echo "Warning: cuML installation failed, will use CPU fallback"

# Copy application code
COPY app.py .
COPY nim_config.yaml .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash nim-user && \
    chown -R nim-user:nim-user /app
USER nim-user

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["python3", "app.py"]

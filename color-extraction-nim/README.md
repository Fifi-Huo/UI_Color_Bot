# Color Extraction NIM

NVIDIA NIM (NVIDIA Inference Microservice) for extracting dominant colors from images using cuML K-Means clustering with GPU acceleration.

## 🚀 Features

- **GPU-Accelerated**: Uses NVIDIA cuML K-Means for fast color clustering
- **Fallback Support**: Automatically falls back to sklearn if cuML is unavailable
- **RESTful API**: FastAPI-based HTTP endpoints
- **Docker Ready**: Complete containerization with NVIDIA GPU support
- **Production Ready**: Health checks, metrics, and error handling

## 📋 API Endpoints

### POST `/extract-colors`
Extract dominant colors from an image URL.

**Request Body:**
```json
{
  "image_url": "https://example.com/image.jpg",
  "num_colors": 5,
  "min_percentage": 0.05
}
```

**Response:**
```json
{
  "success": true,
  "colors": [
    {
      "hex_code": "#2962FF",
      "rgb": [41, 98, 255],
      "percentage": 0.35,
      "color_name": "Blue-ish"
    }
  ],
  "total_colors_found": 5,
  "processing_time_ms": 1250.5,
  "algorithm_used": "cuML K-Means",
  "image_dimensions": {"width": 800, "height": 600}
}
```

### GET `/health`
Health check endpoint.

### GET `/metrics`
Service metrics and status.

## 🛠 Installation & Setup

### Local Development

1. **Install Dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the Service:**
```bash
python app.py
```

3. **Test the Service:**
```bash
python test_client.py
```

### Docker Deployment

1. **Build the Container:**
```bash
docker build -t color-extraction-nim .
```

2. **Run with GPU Support:**
```bash
docker run --gpus all -p 8080:8080 color-extraction-nim
```

3. **Or use Docker Compose:**
```bash
docker-compose up -d
```

## 🔧 Configuration

### Environment Variables
- `PORT`: Service port (default: 8080)
- `CUDA_VISIBLE_DEVICES`: GPU device selection
- `PYTHONUNBUFFERED`: Python output buffering

### NIM Configuration
Edit `nim_config.yaml` to customize:
- Number of workers
- Request timeouts
- GPU settings
- Logging levels

## 🧪 Testing

The service includes a comprehensive test client:

```bash
python test_client.py
```

This will test:
- Health endpoint
- Color extraction with sample images
- Performance metrics
- Error handling

## 🏗 Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client App    │───▶│  Color Extract   │───▶│   cuML/GPU      │
│                 │    │      NIM         │    │   K-Means       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   FastAPI        │
                       │   + OpenCV       │
                       │   + PIL          │
                       └──────────────────┘
```

## 📊 Performance

- **GPU Acceleration**: 5-10x faster than CPU-only processing
- **Memory Efficient**: Automatic image resizing for large images
- **Concurrent Processing**: Supports multiple simultaneous requests
- **Optimized**: Uses efficient numpy operations and GPU memory pooling

## 🔒 Security

- Non-root container execution
- Input validation and sanitization
- Request size limits
- Timeout protection
- CORS configuration

## 🚀 NVIDIA LaunchPad Deployment

1. **Upload to LaunchPad:**
```bash
# Build and tag for registry
docker build -t nvcr.io/your-org/color-extraction-nim:v1.0.0 .
docker push nvcr.io/your-org/color-extraction-nim:v1.0.0
```

2. **Deploy on LaunchPad:**
- Use the provided `nim_config.yaml`
- Configure GPU resources
- Set up load balancing
- Monitor with built-in metrics

## 📈 Monitoring

The NIM provides several monitoring endpoints:
- `/health` - Service health status
- `/metrics` - Performance metrics
- Built-in logging with configurable levels
- Docker health checks

## 🔧 Troubleshooting

**cuML Installation Issues:**
- Ensure NVIDIA drivers are installed
- Check CUDA compatibility
- Service will fallback to sklearn automatically

**Memory Issues:**
- Adjust `max_image_size` in config
- Monitor GPU memory usage
- Consider batch processing for multiple images

**Performance Optimization:**
- Use GPU instances on LaunchPad
- Enable cuML memory pooling
- Optimize image preprocessing pipeline

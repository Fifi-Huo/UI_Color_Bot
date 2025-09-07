#!/usr/bin/env python3
"""
Color Extraction NIM Service
NVIDIA NIM for extracting dominant colors from images using cuML K-Means clustering
"""

import os
import io
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import numpy as np
import cv2
import requests
from PIL import Image
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, validator
import uvicorn

# Try to import cuML, fallback to sklearn if not available
try:
    from cuml.cluster import KMeans as cuMLKMeans
    CUML_AVAILABLE = True
    print("✅ cuML available - using GPU acceleration")
except ImportError:
    from sklearn.cluster import KMeans as SklearnKMeans
    CUML_AVAILABLE = False
    print("⚠️  cuML not available - using sklearn CPU fallback")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(
    title="Color Extraction NIM",
    description="NVIDIA NIM for extracting dominant colors from images using cuML K-Means clustering",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ColorExtractionRequest(BaseModel):
    image_url: HttpUrl
    num_colors: int = 5
    min_percentage: float = 0.05  # Minimum percentage to include a color
    
    @validator('num_colors')
    def validate_num_colors(cls, v):
        if v < 1 or v > 20:
            raise ValueError('num_colors must be between 1 and 20')
        return v
    
    @validator('min_percentage')
    def validate_min_percentage(cls, v):
        if v < 0.01 or v > 0.5:
            raise ValueError('min_percentage must be between 0.01 and 0.5')
        return v

class ColorInfo(BaseModel):
    hex_code: str
    rgb: List[int]
    percentage: float
    color_name: Optional[str] = None

class ColorExtractionResponse(BaseModel):
    success: bool
    colors: List[ColorInfo]
    total_colors_found: int
    processing_time_ms: float
    algorithm_used: str
    image_dimensions: Dict[str, int]

class HealthResponse(BaseModel):
    status: str
    version: str
    gpu_available: bool
    cuml_available: bool

# Color extraction utilities
class ColorExtractor:
    def __init__(self):
        self.algorithm = "cuML K-Means" if CUML_AVAILABLE else "sklearn K-Means"
    
    def rgb_to_hex(self, rgb: np.ndarray) -> str:
        """Convert RGB values to hex code"""
        return "#{:02x}{:02x}{:02x}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))
    
    def get_color_name(self, rgb: np.ndarray) -> str:
        """Get approximate color name based on RGB values"""
        r, g, b = int(rgb[0]), int(rgb[1]), int(rgb[2])
        
        # Simple color naming logic
        if r > 200 and g > 200 and b > 200:
            return "Light"
        elif r < 50 and g < 50 and b < 50:
            return "Dark"
        elif r > g and r > b:
            return "Red-ish"
        elif g > r and g > b:
            return "Green-ish"
        elif b > r and b > g:
            return "Blue-ish"
        elif r > 150 and g > 150 and b < 100:
            return "Yellow-ish"
        elif r > 150 and g < 100 and b > 150:
            return "Purple-ish"
        elif r < 100 and g > 150 and b > 150:
            return "Cyan-ish"
        else:
            return "Mixed"
    
    async def download_image(self, image_url: str) -> np.ndarray:
        """Download and preprocess image from URL with proper color space conversion"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Download image
            response = requests.get(str(image_url), headers=headers, timeout=30)
            response.raise_for_status()
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(response.content))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to numpy array (PIL uses RGB format)
            image_array = np.array(image)
            
            # Resize if too large (for performance)
            height, width = image_array.shape[:2]
            if width > 800 or height > 800:
                scale = min(800/width, 800/height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image_array = cv2.resize(image_array, (new_width, new_height))
            
            # Convert RGB to BGR for OpenCV processing
            # PIL uses RGB format, but OpenCV expects BGR
            image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            
            return image_bgr
            
        except Exception as e:
            logger.error(f"Error downloading image: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Failed to download image: {str(e)}")
    
    def extract_colors_cuml(self, image: np.ndarray, num_colors: int) -> tuple:
        """Extract colors using cuML K-Means (GPU accelerated) with HSV color space"""
        # Convert BGR to HSV for better color perception
        image_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Reshape image to 2D array of pixels
        pixels_hsv = image_hsv.reshape(-1, 3).astype(np.float32)
        
        # Apply K-Means clustering in HSV space
        kmeans = cuMLKMeans(n_clusters=num_colors, random_state=42)
        labels = kmeans.fit_predict(pixels_hsv)
        
        # Get cluster centers (dominant colors in HSV)
        colors_hsv = kmeans.cluster_centers_
        
        # Convert HSV cluster centers back to BGR for display
        colors_bgr = []
        for hsv_color in colors_hsv:
            # Create single pixel HSV image
            hsv_pixel = np.uint8([[hsv_color]])
            # Convert to BGR
            bgr_pixel = cv2.cvtColor(hsv_pixel, cv2.COLOR_HSV2BGR)
            colors_bgr.append(bgr_pixel[0][0])
        
        colors_bgr = np.array(colors_bgr)
        
        # Convert BGR to RGB for final output (web standard)
        colors_rgb = []
        for bgr_color in colors_bgr:
            rgb_color = cv2.cvtColor(np.uint8([[bgr_color]]), cv2.COLOR_BGR2RGB)[0][0]
            colors_rgb.append(rgb_color)
        
        colors_rgb = np.array(colors_rgb)
        
        # Calculate color percentages
        unique_labels, counts = np.unique(labels, return_counts=True)
        percentages = counts / len(pixels_hsv)
        
        return colors_rgb, percentages
    
    def extract_colors_sklearn(self, image: np.ndarray, num_colors: int) -> tuple:
        """Extract colors using sklearn K-Means (CPU fallback) with HSV color space"""
        # Convert BGR to HSV for better color perception
        image_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Reshape image to 2D array of pixels
        pixels_hsv = image_hsv.reshape(-1, 3)
        
        # Apply K-Means clustering in HSV space
        kmeans = SklearnKMeans(n_clusters=num_colors, random_state=42, n_init=10)
        labels = kmeans.fit_predict(pixels_hsv)
        
        # Get cluster centers (dominant colors in HSV)
        colors_hsv = kmeans.cluster_centers_
        
        # Convert HSV cluster centers back to BGR for display
        colors_bgr = []
        for hsv_color in colors_hsv:
            # Create single pixel HSV image
            hsv_pixel = np.uint8([[hsv_color]])
            # Convert to BGR
            bgr_pixel = cv2.cvtColor(hsv_pixel, cv2.COLOR_HSV2BGR)
            colors_bgr.append(bgr_pixel[0][0])
        
        colors_bgr = np.array(colors_bgr)
        
        # Convert BGR to RGB for final output (web standard)
        colors_rgb = []
        for bgr_color in colors_bgr:
            rgb_color = cv2.cvtColor(np.uint8([[bgr_color]]), cv2.COLOR_BGR2RGB)[0][0]
            colors_rgb.append(rgb_color)
        
        colors_rgb = np.array(colors_rgb)
        
        # Calculate color percentages
        unique_labels, counts = np.unique(labels, return_counts=True)
        percentages = counts / len(pixels_hsv)
        
        return colors_rgb, percentages
    
    async def extract_dominant_colors(
        self, 
        image_url: str, 
        num_colors: int = 5, 
        min_percentage: float = 0.05
    ) -> ColorExtractionResponse:
        """Main color extraction function"""
        import time
        start_time = time.time()
        
        try:
            # Download and preprocess image
            image = await self.download_image(image_url)
            height, width = image.shape[:2]
            
            # Extract colors using appropriate algorithm
            if CUML_AVAILABLE:
                colors, percentages = self.extract_colors_cuml(image, num_colors)
            else:
                colors, percentages = self.extract_colors_sklearn(image, num_colors)
            
            # Sort by percentage (descending)
            sorted_indices = np.argsort(percentages)[::-1]
            colors = colors[sorted_indices]
            percentages = percentages[sorted_indices]
            
            # Filter colors by minimum percentage and create response
            color_info_list = []
            for i, (color, percentage) in enumerate(zip(colors, percentages)):
                if percentage >= min_percentage:
                    color_rgb = [int(c) for c in color]
                    color_info = ColorInfo(
                        hex_code=self.rgb_to_hex(color),
                        rgb=color_rgb,
                        percentage=float(percentage),
                        color_name=self.get_color_name(color)
                    )
                    color_info_list.append(color_info)
            
            processing_time = (time.time() - start_time) * 1000
            
            return ColorExtractionResponse(
                success=True,
                colors=color_info_list,
                total_colors_found=len(color_info_list),
                processing_time_ms=processing_time,
                algorithm_used=self.algorithm,
                image_dimensions={"width": width, "height": height}
            )
            
        except Exception as e:
            logger.error(f"Color extraction failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Color extraction failed: {str(e)}")

# Initialize color extractor
color_extractor = ColorExtractor()

# API endpoints
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "service": "Color Extraction NIM",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        gpu_available=CUML_AVAILABLE,
        cuml_available=CUML_AVAILABLE
    )

@app.post("/extract-colors", response_model=ColorExtractionResponse)
async def extract_colors(request: ColorExtractionRequest, background_tasks: BackgroundTasks):
    """
    Extract dominant colors from an image URL using K-Means clustering
    
    - **image_url**: URL of the image to process
    - **num_colors**: Number of dominant colors to extract (1-20)
    - **min_percentage**: Minimum percentage threshold for including colors (0.01-0.5)
    """
    logger.info(f"Processing color extraction for: {request.image_url}")
    
    result = await color_extractor.extract_dominant_colors(
        str(request.image_url),
        request.num_colors,
        request.min_percentage
    )
    
    logger.info(f"Color extraction completed: {result.total_colors_found} colors found")
    return result

@app.get("/metrics")
async def get_metrics():
    """Get service metrics"""
    return {
        "algorithm": color_extractor.algorithm,
        "gpu_acceleration": CUML_AVAILABLE,
        "service_status": "running"
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {
        "success": False,
        "error": exc.detail,
        "status_code": exc.status_code
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )

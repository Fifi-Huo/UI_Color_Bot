#!/usr/bin/env python3
"""
Palette Generation NIM Service
NVIDIA NIM for generating color palettes using color theory algorithms
"""

import os
import json
import logging
import asyncio
import colorsys
import math
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import numpy as np
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(
    title="Palette Generation NIM",
    description="NVIDIA NIM for generating color palettes using color theory algorithms",
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

# Enums and Models
class PaletteType(str, Enum):
    MONOCHROMATIC = "monochromatic"
    ANALOGOUS = "analogous"
    COMPLEMENTARY = "complementary"
    TRIADIC = "triadic"
    TETRADIC = "tetradic"
    SPLIT_COMPLEMENTARY = "split_complementary"
    COMPOUND = "compound"

class ColorSpace(str, Enum):
    RGB = "rgb"
    HSV = "hsv"
    HSL = "hsl"
    LAB = "lab"

class PaletteRequest(BaseModel):
    base_color: str  # Hex color like "#FF5733"
    palette_type: PaletteType
    num_colors: int = 5
    saturation_range: Tuple[float, float] = (0.3, 0.9)
    lightness_range: Tuple[float, float] = (0.2, 0.8)
    
    @validator('base_color')
    def validate_hex_color(cls, v):
        if not v.startswith('#') or len(v) != 7:
            raise ValueError('base_color must be a valid hex color (e.g., #FF5733)')
        try:
            int(v[1:], 16)
        except ValueError:
            raise ValueError('Invalid hex color format')
        return v
    
    @validator('num_colors')
    def validate_num_colors(cls, v):
        if v < 2 or v > 12:
            raise ValueError('num_colors must be between 2 and 12')
        return v

class ColorInfo(BaseModel):
    hex_code: str
    rgb: List[int]
    hsv: List[float]
    hsl: List[float]
    color_name: str
    role: str  # primary, secondary, accent, etc.

class PaletteResponse(BaseModel):
    success: bool
    palette_type: str
    base_color: str
    colors: List[ColorInfo]
    total_colors: int
    processing_time_ms: float
    harmony_score: float
    usage_suggestions: List[str]

class HealthResponse(BaseModel):
    status: str
    version: str
    supported_palettes: List[str]

# Color utilities
class ColorUtils:
    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    @staticmethod
    def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
        """Convert RGB to hex color"""
        return "#{:02x}{:02x}{:02x}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))
    
    @staticmethod
    def rgb_to_hsv(rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
        """Convert RGB to HSV"""
        r, g, b = [x / 255.0 for x in rgb]
        return colorsys.rgb_to_hsv(r, g, b)
    
    @staticmethod
    def hsv_to_rgb(hsv: Tuple[float, float, float]) -> Tuple[int, int, int]:
        """Convert HSV to RGB"""
        r, g, b = colorsys.hsv_to_rgb(hsv[0], hsv[1], hsv[2])
        return (int(r * 255), int(g * 255), int(b * 255))
    
    @staticmethod
    def rgb_to_hsl(rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
        """Convert RGB to HSL"""
        r, g, b = [x / 255.0 for x in rgb]
        return colorsys.rgb_to_hls(r, g, b)
    
    @staticmethod
    def hsl_to_rgb(hsl: Tuple[float, float, float]) -> Tuple[int, int, int]:
        """Convert HSL to RGB"""
        r, g, b = colorsys.hls_to_rgb(hsl[0], hsl[1], hsl[2])
        return (int(r * 255), int(g * 255), int(b * 255))
    
    @staticmethod
    def get_color_name(rgb: Tuple[int, int, int]) -> str:
        """Get approximate color name"""
        r, g, b = rgb
        
        # Convert to HSV for better color classification
        h, s, v = ColorUtils.rgb_to_hsv(rgb)
        h_deg = h * 360
        
        if s < 0.1:
            if v > 0.9:
                return "White"
            elif v < 0.1:
                return "Black"
            else:
                return "Gray"
        
        if h_deg < 15 or h_deg >= 345:
            return "Red"
        elif h_deg < 45:
            return "Orange"
        elif h_deg < 75:
            return "Yellow"
        elif h_deg < 150:
            return "Green"
        elif h_deg < 210:
            return "Cyan"
        elif h_deg < 270:
            return "Blue"
        elif h_deg < 330:
            return "Purple"
        else:
            return "Pink"

# Palette generator
class PaletteGenerator:
    def __init__(self):
        self.color_utils = ColorUtils()
    
    def calculate_harmony_score(self, colors: List[Tuple[int, int, int]]) -> float:
        """Calculate harmony score based on color relationships"""
        if len(colors) < 2:
            return 1.0
        
        # Convert to HSV for analysis
        hsv_colors = [self.color_utils.rgb_to_hsv(color) for color in colors]
        
        # Calculate hue differences
        hue_diffs = []
        for i in range(len(hsv_colors)):
            for j in range(i + 1, len(hsv_colors)):
                h1, h2 = hsv_colors[i][0], hsv_colors[j][0]
                diff = min(abs(h1 - h2), 1 - abs(h1 - h2))
                hue_diffs.append(diff)
        
        # Score based on hue relationships
        avg_hue_diff = sum(hue_diffs) / len(hue_diffs)
        harmony_score = 1.0 - (abs(avg_hue_diff - 0.33) / 0.33)  # Optimal around 120 degrees
        
        return max(0.0, min(1.0, harmony_score))
    
    def generate_monochromatic(self, base_rgb: Tuple[int, int, int], num_colors: int, 
                             sat_range: Tuple[float, float], light_range: Tuple[float, float]) -> List[Tuple[int, int, int]]:
        """Generate monochromatic palette"""
        h, s, v = self.color_utils.rgb_to_hsv(base_rgb)
        colors = []
        
        for i in range(num_colors):
            # Vary saturation and value while keeping hue constant
            new_s = sat_range[0] + (sat_range[1] - sat_range[0]) * (i / (num_colors - 1))
            new_v = light_range[0] + (light_range[1] - light_range[0]) * (i / (num_colors - 1))
            colors.append(self.color_utils.hsv_to_rgb((h, new_s, new_v)))
        
        return colors
    
    def generate_analogous(self, base_rgb: Tuple[int, int, int], num_colors: int,
                          sat_range: Tuple[float, float], light_range: Tuple[float, float]) -> List[Tuple[int, int, int]]:
        """Generate analogous palette"""
        h, s, v = self.color_utils.rgb_to_hsv(base_rgb)
        colors = []
        
        # Spread colors within 60 degrees
        hue_range = 60 / 360
        for i in range(num_colors):
            offset = (i - num_colors // 2) * (hue_range / num_colors)
            new_h = (h + offset) % 1.0
            new_s = sat_range[0] + (sat_range[1] - sat_range[0]) * np.random.random()
            new_v = light_range[0] + (light_range[1] - light_range[0]) * np.random.random()
            colors.append(self.color_utils.hsv_to_rgb((new_h, new_s, new_v)))
        
        return colors
    
    def generate_complementary(self, base_rgb: Tuple[int, int, int], num_colors: int,
                              sat_range: Tuple[float, float], light_range: Tuple[float, float]) -> List[Tuple[int, int, int]]:
        """Generate complementary palette"""
        h, s, v = self.color_utils.rgb_to_hsv(base_rgb)
        colors = [base_rgb]
        
        # Add complementary color (180 degrees opposite)
        comp_h = (h + 0.5) % 1.0
        comp_rgb = self.color_utils.hsv_to_rgb((comp_h, s, v))
        colors.append(comp_rgb)
        
        # Add variations
        for i in range(num_colors - 2):
            base_h = h if i % 2 == 0 else comp_h
            new_s = sat_range[0] + (sat_range[1] - sat_range[0]) * np.random.random()
            new_v = light_range[0] + (light_range[1] - light_range[0]) * np.random.random()
            colors.append(self.color_utils.hsv_to_rgb((base_h, new_s, new_v)))
        
        return colors
    
    def generate_triadic(self, base_rgb: Tuple[int, int, int], num_colors: int,
                        sat_range: Tuple[float, float], light_range: Tuple[float, float]) -> List[Tuple[int, int, int]]:
        """Generate triadic palette"""
        h, s, v = self.color_utils.rgb_to_hsv(base_rgb)
        colors = [base_rgb]
        
        # Add triadic colors (120 degrees apart)
        for offset in [1/3, 2/3]:
            tri_h = (h + offset) % 1.0
            tri_rgb = self.color_utils.hsv_to_rgb((tri_h, s, v))
            colors.append(tri_rgb)
        
        # Add variations
        for i in range(num_colors - 3):
            base_h = h + (i % 3) * (1/3)
            new_s = sat_range[0] + (sat_range[1] - sat_range[0]) * np.random.random()
            new_v = light_range[0] + (light_range[1] - light_range[0]) * np.random.random()
            colors.append(self.color_utils.hsv_to_rgb((base_h % 1.0, new_s, new_v)))
        
        return colors
    
    def generate_tetradic(self, base_rgb: Tuple[int, int, int], num_colors: int,
                         sat_range: Tuple[float, float], light_range: Tuple[float, float]) -> List[Tuple[int, int, int]]:
        """Generate tetradic (square) palette"""
        h, s, v = self.color_utils.rgb_to_hsv(base_rgb)
        colors = [base_rgb]
        
        # Add tetradic colors (90 degrees apart)
        for offset in [0.25, 0.5, 0.75]:
            tet_h = (h + offset) % 1.0
            tet_rgb = self.color_utils.hsv_to_rgb((tet_h, s, v))
            colors.append(tet_rgb)
        
        # Add variations
        for i in range(num_colors - 4):
            base_h = h + (i % 4) * 0.25
            new_s = sat_range[0] + (sat_range[1] - sat_range[0]) * np.random.random()
            new_v = light_range[0] + (light_range[1] - light_range[0]) * np.random.random()
            colors.append(self.color_utils.hsv_to_rgb((base_h % 1.0, new_s, new_v)))
        
        return colors
    
    def generate_split_complementary(self, base_rgb: Tuple[int, int, int], num_colors: int,
                                   sat_range: Tuple[float, float], light_range: Tuple[float, float]) -> List[Tuple[int, int, int]]:
        """Generate split complementary palette"""
        h, s, v = self.color_utils.rgb_to_hsv(base_rgb)
        colors = [base_rgb]
        
        # Add split complementary colors (150 and 210 degrees)
        for offset in [150/360, 210/360]:
            split_h = (h + offset) % 1.0
            split_rgb = self.color_utils.hsv_to_rgb((split_h, s, v))
            colors.append(split_rgb)
        
        # Add variations
        for i in range(num_colors - 3):
            if i % 3 == 0:
                base_h = h
            elif i % 3 == 1:
                base_h = (h + 150/360) % 1.0
            else:
                base_h = (h + 210/360) % 1.0
            
            new_s = sat_range[0] + (sat_range[1] - sat_range[0]) * np.random.random()
            new_v = light_range[0] + (light_range[1] - light_range[0]) * np.random.random()
            colors.append(self.color_utils.hsv_to_rgb((base_h, new_s, new_v)))
        
        return colors
    
    def get_usage_suggestions(self, palette_type: PaletteType, colors: List[Tuple[int, int, int]]) -> List[str]:
        """Get usage suggestions for the palette in Chinese"""
        suggestions = []
        
        if palette_type == PaletteType.MONOCHROMATIC:
            suggestions = [
                "使用最浅的颜色作为背景",
                "中等色调用于次要元素",
                "最深的颜色用于文字和强调",
                "适合极简主义设计"
            ]
        elif palette_type == PaletteType.COMPLEMENTARY:
            suggestions = [
                "使用一种颜色作为主色调 (60%)",
                "互补色用于强调元素 (10%)",
                "中性变化用于平衡 (30%)",
                "高对比度适合行动号召元素"
            ]
        elif palette_type == PaletteType.TRIADIC:
            suggestions = [
                "选择一种颜色作为主色",
                "其他两种颜色谨慎用作强调色",
                "用中性色调平衡",
                "适合充满活力的设计"
            ]
        elif palette_type == PaletteType.ANALOGOUS:
            suggestions = [
                "创造和谐、平静的感觉",
                "用于渐变和过渡效果",
                "一种颜色应占主导地位",
                "完美适合自然主题设计"
            ]
        elif palette_type == PaletteType.TETRADIC:
            suggestions = [
                "选择一种主色调",
                "其他三种颜色用作强调",
                "保持色彩平衡很重要",
                "适合丰富多彩的设计"
            ]
        elif palette_type == PaletteType.SPLIT_COMPLEMENTARY:
            suggestions = [
                "基础色作为主色调",
                "分裂互补色用于强调",
                "比纯互补色更柔和",
                "适合需要对比但不过于强烈的设计"
            ]
        
        return suggestions
    
    async def generate_palette(self, request: PaletteRequest) -> PaletteResponse:
        """Main palette generation function"""
        import time
        start_time = time.time()
        
        try:
            # Convert base color to RGB
            base_rgb = self.color_utils.hex_to_rgb(request.base_color)
            
            # Generate colors based on palette type
            if request.palette_type == PaletteType.MONOCHROMATIC:
                colors = self.generate_monochromatic(base_rgb, request.num_colors, 
                                                   request.saturation_range, request.lightness_range)
            elif request.palette_type == PaletteType.ANALOGOUS:
                colors = self.generate_analogous(base_rgb, request.num_colors,
                                               request.saturation_range, request.lightness_range)
            elif request.palette_type == PaletteType.COMPLEMENTARY:
                colors = self.generate_complementary(base_rgb, request.num_colors,
                                                   request.saturation_range, request.lightness_range)
            elif request.palette_type == PaletteType.TRIADIC:
                colors = self.generate_triadic(base_rgb, request.num_colors,
                                             request.saturation_range, request.lightness_range)
            elif request.palette_type == PaletteType.TETRADIC:
                colors = self.generate_tetradic(base_rgb, request.num_colors,
                                              request.saturation_range, request.lightness_range)
            elif request.palette_type == PaletteType.SPLIT_COMPLEMENTARY:
                colors = self.generate_split_complementary(base_rgb, request.num_colors,
                                                         request.saturation_range, request.lightness_range)
            else:
                raise ValueError(f"Unsupported palette type: {request.palette_type}")
            
            # Create color info objects
            color_infos = []
            roles = ["primary", "secondary", "accent", "highlight", "neutral"]
            
            for i, color in enumerate(colors):
                hex_code = self.color_utils.rgb_to_hex(color)
                hsv = self.color_utils.rgb_to_hsv(color)
                hsl = self.color_utils.rgb_to_hsl(color)
                color_name = self.color_utils.get_color_name(color)
                role = roles[i % len(roles)]
                
                color_info = ColorInfo(
                    hex_code=hex_code,
                    rgb=list(color),
                    hsv=list(hsv),
                    hsl=list(hsl),
                    color_name=color_name,
                    role=role
                )
                color_infos.append(color_info)
            
            # Calculate harmony score
            harmony_score = self.calculate_harmony_score(colors)
            
            # Get usage suggestions
            usage_suggestions = self.get_usage_suggestions(request.palette_type, colors)
            
            processing_time = (time.time() - start_time) * 1000
            
            return PaletteResponse(
                success=True,
                palette_type=request.palette_type.value,
                base_color=request.base_color,
                colors=color_infos,
                total_colors=len(colors),
                processing_time_ms=processing_time,
                harmony_score=harmony_score,
                usage_suggestions=usage_suggestions
            )
            
        except Exception as e:
            logger.error(f"Palette generation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Palette generation failed: {str(e)}")

# Initialize palette generator
palette_generator = PaletteGenerator()

# API endpoints
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "service": "Palette Generation NIM",
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
        supported_palettes=[palette_type.value for palette_type in PaletteType]
    )

@app.post("/generate-palette", response_model=PaletteResponse)
async def generate_palette(request: PaletteRequest, background_tasks: BackgroundTasks):
    """
    Generate a color palette based on color theory
    
    - **base_color**: Base hex color (e.g., #FF5733)
    - **palette_type**: Type of palette to generate
    - **num_colors**: Number of colors in the palette (2-12)
    - **saturation_range**: Range of saturation values (0.0-1.0)
    - **lightness_range**: Range of lightness values (0.0-1.0)
    """
    logger.info(f"Generating {request.palette_type} palette from {request.base_color}")
    
    result = await palette_generator.generate_palette(request)
    
    logger.info(f"Palette generation completed: {result.total_colors} colors, harmony score: {result.harmony_score:.2f}")
    return result

@app.get("/palette-types")
async def get_palette_types():
    """Get supported palette types"""
    return {
        "palette_types": [
            {
                "type": palette_type.value,
                "description": {
                    "monochromatic": "Single hue with varying saturation and lightness",
                    "analogous": "Colors adjacent on the color wheel",
                    "complementary": "Colors opposite on the color wheel",
                    "triadic": "Three colors evenly spaced on the color wheel",
                    "tetradic": "Four colors forming a square on the color wheel",
                    "split_complementary": "Base color plus two colors adjacent to its complement",
                    "compound": "Complex palette with multiple harmony rules"
                }.get(palette_type.value, "Color harmony palette")
            }
            for palette_type in PaletteType
        ]
    }

@app.get("/metrics")
async def get_metrics():
    """Get service metrics"""
    return {
        "service": "palette-generation-nim",
        "supported_palette_types": len(PaletteType),
        "color_spaces_supported": ["RGB", "HSV", "HSL"],
        "service_status": "running"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8081))
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )

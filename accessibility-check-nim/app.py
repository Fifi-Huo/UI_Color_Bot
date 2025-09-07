#!/usr/bin/env python3
"""
Accessibility Check NIM Service
NVIDIA NIM for checking color accessibility and WCAG compliance
"""

import os
import json
import logging
import asyncio
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
    title="Accessibility Check NIM",
    description="NVIDIA NIM for checking color accessibility and WCAG compliance",
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
class WCAGLevel(str, Enum):
    AA = "AA"
    AAA = "AAA"

class TextSize(str, Enum):
    NORMAL = "normal"
    LARGE = "large"

class ColorBlindnessType(str, Enum):
    PROTANOPIA = "protanopia"
    DEUTERANOPIA = "deuteranopia"
    TRITANOPIA = "tritanopia"
    ACHROMATOPSIA = "achromatopsia"

class AccessibilityRequest(BaseModel):
    foreground_color: str  # Hex color
    background_color: str  # Hex color
    text_size: TextSize = TextSize.NORMAL
    wcag_level: WCAGLevel = WCAGLevel.AA
    check_colorblind: bool = True
    
    @validator('foreground_color', 'background_color')
    def validate_hex_color(cls, v):
        if not v.startswith('#') or len(v) != 7:
            raise ValueError('Color must be a valid hex color (e.g., #FF5733)')
        try:
            int(v[1:], 16)
        except ValueError:
            raise ValueError('Invalid hex color format')
        return v

class ContrastResult(BaseModel):
    ratio: float
    passes_aa_normal: bool
    passes_aa_large: bool
    passes_aaa_normal: bool
    passes_aaa_large: bool
    grade: str

class ColorBlindnessResult(BaseModel):
    type: str
    simulated_foreground: str
    simulated_background: str
    contrast_ratio: float
    passes_wcag: bool

class AccessibilityResponse(BaseModel):
    success: bool
    foreground_color: str
    background_color: str
    contrast_result: ContrastResult
    colorblindness_results: List[ColorBlindnessResult]
    recommendations: List[str]
    processing_time_ms: float

class PaletteAccessibilityRequest(BaseModel):
    colors: List[str]  # List of hex colors
    wcag_level: WCAGLevel = WCAGLevel.AA
    
    @validator('colors')
    def validate_colors(cls, v):
        if len(v) < 2:
            raise ValueError('At least 2 colors required')
        for color in v:
            if not color.startswith('#') or len(color) != 7:
                raise ValueError('All colors must be valid hex colors')
        return v

class PaletteAccessibilityResponse(BaseModel):
    success: bool
    total_combinations: int
    accessible_combinations: int
    accessibility_score: float
    color_pairs: List[Dict[str, Any]]
    recommendations: List[str]
    processing_time_ms: float

class HealthResponse(BaseModel):
    status: str
    version: str
    wcag_levels: List[str]
    colorblindness_types: List[str]

# Accessibility utilities
class AccessibilityChecker:
    def __init__(self):
        # WCAG contrast ratio requirements
        self.wcag_requirements = {
            WCAGLevel.AA: {"normal": 4.5, "large": 3.0},
            WCAGLevel.AAA: {"normal": 7.0, "large": 4.5}
        }
        
        # Color blindness simulation matrices
        self.colorblind_matrices = {
            ColorBlindnessType.PROTANOPIA: np.array([
                [0.567, 0.433, 0.000],
                [0.558, 0.442, 0.000],
                [0.000, 0.242, 0.758]
            ]),
            ColorBlindnessType.DEUTERANOPIA: np.array([
                [0.625, 0.375, 0.000],
                [0.700, 0.300, 0.000],
                [0.000, 0.300, 0.700]
            ]),
            ColorBlindnessType.TRITANOPIA: np.array([
                [0.950, 0.050, 0.000],
                [0.000, 0.433, 0.567],
                [0.000, 0.475, 0.525]
            ]),
            ColorBlindnessType.ACHROMATOPSIA: np.array([
                [0.299, 0.587, 0.114],
                [0.299, 0.587, 0.114],
                [0.299, 0.587, 0.114]
            ])
        }
    
    def hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB to hex color"""
        return "#{:02x}{:02x}{:02x}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))
    
    def get_relative_luminance(self, rgb: Tuple[int, int, int]) -> float:
        """Calculate relative luminance according to WCAG guidelines"""
        def linearize(channel):
            channel = channel / 255.0
            if channel <= 0.03928:
                return channel / 12.92
            else:
                return math.pow((channel + 0.055) / 1.055, 2.4)
        
        r, g, b = rgb
        r_lin = linearize(r)
        g_lin = linearize(g)
        b_lin = linearize(b)
        
        return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin
    
    def calculate_contrast_ratio(self, color1: str, color2: str) -> float:
        """Calculate contrast ratio between two colors"""
        rgb1 = self.hex_to_rgb(color1)
        rgb2 = self.hex_to_rgb(color2)
        
        lum1 = self.get_relative_luminance(rgb1)
        lum2 = self.get_relative_luminance(rgb2)
        
        # Ensure lighter color is in numerator
        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)
        
        return (lighter + 0.05) / (darker + 0.05)
    
    def check_wcag_compliance(self, contrast_ratio: float, text_size: TextSize, wcag_level: WCAGLevel) -> Dict[str, bool]:
        """Check WCAG compliance for given contrast ratio"""
        requirements = self.wcag_requirements
        
        return {
            "passes_aa_normal": contrast_ratio >= requirements[WCAGLevel.AA]["normal"],
            "passes_aa_large": contrast_ratio >= requirements[WCAGLevel.AA]["large"],
            "passes_aaa_normal": contrast_ratio >= requirements[WCAGLevel.AAA]["normal"],
            "passes_aaa_large": contrast_ratio >= requirements[WCAGLevel.AAA]["large"]
        }
    
    def get_contrast_grade(self, contrast_ratio: float) -> str:
        """Get letter grade for contrast ratio"""
        if contrast_ratio >= 7.0:
            return "AAA"
        elif contrast_ratio >= 4.5:
            return "AA"
        elif contrast_ratio >= 3.0:
            return "AA Large"
        else:
            return "Fail"
    
    def simulate_colorblindness(self, rgb: Tuple[int, int, int], cb_type: ColorBlindnessType) -> Tuple[int, int, int]:
        """Simulate color blindness for given RGB color"""
        # Convert to 0-1 range
        rgb_normalized = np.array(rgb) / 255.0
        
        # Apply color blindness transformation matrix
        matrix = self.colorblind_matrices[cb_type]
        transformed = np.dot(matrix, rgb_normalized)
        
        # Convert back to 0-255 range and clamp
        result = np.clip(transformed * 255, 0, 255).astype(int)
        return tuple(result)
    
    def generate_recommendations(self, contrast_ratio: float, wcag_level: WCAGLevel, 
                               text_size: TextSize, passes_wcag: bool) -> List[str]:
        """Generate accessibility recommendations in Chinese"""
        recommendations = []
        
        required_ratio = self.wcag_requirements[wcag_level][text_size.value]
        text_size_cn = "普通" if text_size == TextSize.NORMAL else "大"
        wcag_level_cn = "AA" if wcag_level == WCAGLevel.AA else "AAA"
        
        if not passes_wcag:
            recommendations.append(f"当前对比度 {contrast_ratio:.2f} 不符合 WCAG {wcag_level_cn} {text_size_cn}文字要求 (需要 {required_ratio})")
            
            if contrast_ratio < 3.0:
                recommendations.append("建议使用对比度更高的完全不同颜色")
            elif contrast_ratio < 4.5:
                recommendations.append("尝试加深文字颜色或减淡背景颜色")
            
            recommendations.append("建议与有视觉障碍的实际用户进行测试")
        else:
            recommendations.append(f"✅ 符合 WCAG {wcag_level_cn} {text_size_cn}文字要求")
            
            if wcag_level == WCAGLevel.AA and contrast_ratio >= 7.0:
                recommendations.append("✅ 同时符合 AAA 要求 - 优秀的可访问性！")
        
        recommendations.append("建议在不同光照条件下测试颜色")
        recommendations.append("考虑提供高对比度模式选项")
        
        return recommendations
    
    async def check_accessibility(self, request: AccessibilityRequest) -> AccessibilityResponse:
        """Main accessibility checking function"""
        import time
        start_time = time.time()
        
        try:
            # Calculate contrast ratio
            contrast_ratio = self.calculate_contrast_ratio(
                request.foreground_color, 
                request.background_color
            )
            
            # Check WCAG compliance
            wcag_results = self.check_wcag_compliance(
                contrast_ratio, 
                request.text_size, 
                request.wcag_level
            )
            
            # Create contrast result
            contrast_result = ContrastResult(
                ratio=contrast_ratio,
                passes_aa_normal=wcag_results["passes_aa_normal"],
                passes_aa_large=wcag_results["passes_aa_large"],
                passes_aaa_normal=wcag_results["passes_aaa_normal"],
                passes_aaa_large=wcag_results["passes_aaa_large"],
                grade=self.get_contrast_grade(contrast_ratio)
            )
            
            # Check color blindness if requested
            colorblindness_results = []
            if request.check_colorblind:
                fg_rgb = self.hex_to_rgb(request.foreground_color)
                bg_rgb = self.hex_to_rgb(request.background_color)
                
                for cb_type in ColorBlindnessType:
                    sim_fg = self.simulate_colorblindness(fg_rgb, cb_type)
                    sim_bg = self.simulate_colorblindness(bg_rgb, cb_type)
                    
                    sim_fg_hex = self.rgb_to_hex(sim_fg)
                    sim_bg_hex = self.rgb_to_hex(sim_bg)
                    
                    sim_contrast = self.calculate_contrast_ratio(sim_fg_hex, sim_bg_hex)
                    required_ratio = self.wcag_requirements[request.wcag_level][request.text_size.value]
                    
                    colorblindness_results.append(ColorBlindnessResult(
                        type=cb_type.value,
                        simulated_foreground=sim_fg_hex,
                        simulated_background=sim_bg_hex,
                        contrast_ratio=sim_contrast,
                        passes_wcag=sim_contrast >= required_ratio
                    ))
            
            # Generate recommendations
            passes_wcag = getattr(contrast_result, f"passes_{request.wcag_level.value.lower()}_{request.text_size.value}")
            recommendations = self.generate_recommendations(
                contrast_ratio, 
                request.wcag_level, 
                request.text_size, 
                passes_wcag
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            return AccessibilityResponse(
                success=True,
                foreground_color=request.foreground_color,
                background_color=request.background_color,
                contrast_result=contrast_result,
                colorblindness_results=colorblindness_results,
                recommendations=recommendations,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Accessibility check failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Accessibility check failed: {str(e)}")
    
    async def check_palette_accessibility(self, request: PaletteAccessibilityRequest) -> PaletteAccessibilityResponse:
        """Check accessibility for all color combinations in a palette"""
        import time
        start_time = time.time()
        
        try:
            colors = request.colors
            total_combinations = 0
            accessible_combinations = 0
            color_pairs = []
            
            # Check all color pair combinations
            for i in range(len(colors)):
                for j in range(len(colors)):
                    if i != j:
                        fg_color = colors[i]
                        bg_color = colors[j]
                        
                        contrast_ratio = self.calculate_contrast_ratio(fg_color, bg_color)
                        required_ratio = self.wcag_requirements[request.wcag_level]["normal"]
                        passes_wcag = contrast_ratio >= required_ratio
                        
                        if passes_wcag:
                            accessible_combinations += 1
                        
                        color_pairs.append({
                            "foreground": fg_color,
                            "background": bg_color,
                            "contrast_ratio": contrast_ratio,
                            "passes_wcag": passes_wcag,
                            "grade": self.get_contrast_grade(contrast_ratio)
                        })
                        
                        total_combinations += 1
            
            # Calculate accessibility score
            accessibility_score = accessible_combinations / total_combinations if total_combinations > 0 else 0
            
            # Generate recommendations
            recommendations = []
            if accessibility_score < 0.3:
                recommendations.append("⚠️ Low accessibility score - consider revising color choices")
                recommendations.append("Add more contrast between colors")
                recommendations.append("Consider including neutral colors (white, black, grays)")
            elif accessibility_score < 0.6:
                recommendations.append("Moderate accessibility - some improvements possible")
                recommendations.append("Test critical text/background combinations")
            else:
                recommendations.append("✅ Good accessibility score!")
                recommendations.append("Most color combinations meet WCAG guidelines")
            
            recommendations.append("Always test with real users and assistive technologies")
            
            processing_time = (time.time() - start_time) * 1000
            
            return PaletteAccessibilityResponse(
                success=True,
                total_combinations=total_combinations,
                accessible_combinations=accessible_combinations,
                accessibility_score=accessibility_score,
                color_pairs=color_pairs,
                recommendations=recommendations,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Palette accessibility check failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Palette accessibility check failed: {str(e)}")

# Initialize accessibility checker
accessibility_checker = AccessibilityChecker()

# API endpoints
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "service": "Accessibility Check NIM",
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
        wcag_levels=[level.value for level in WCAGLevel],
        colorblindness_types=[cb_type.value for cb_type in ColorBlindnessType]
    )

@app.post("/check-accessibility", response_model=AccessibilityResponse)
async def check_accessibility(request: AccessibilityRequest, background_tasks: BackgroundTasks):
    """
    Check color accessibility and WCAG compliance
    
    - **foreground_color**: Text/foreground hex color
    - **background_color**: Background hex color  
    - **text_size**: Normal or large text size
    - **wcag_level**: AA or AAA compliance level
    - **check_colorblind**: Include color blindness simulation
    """
    logger.info(f"Checking accessibility: {request.foreground_color} on {request.background_color}")
    
    result = await accessibility_checker.check_accessibility(request)
    
    logger.info(f"Accessibility check completed: contrast ratio {result.contrast_result.ratio:.2f}")
    return result

@app.post("/check-palette-accessibility", response_model=PaletteAccessibilityResponse)
async def check_palette_accessibility(request: PaletteAccessibilityRequest, background_tasks: BackgroundTasks):
    """
    Check accessibility for all color combinations in a palette
    
    - **colors**: List of hex colors to analyze
    - **wcag_level**: AA or AAA compliance level
    """
    logger.info(f"Checking palette accessibility for {len(request.colors)} colors")
    
    result = await accessibility_checker.check_palette_accessibility(request)
    
    logger.info(f"Palette accessibility check completed: {result.accessibility_score:.1%} accessible combinations")
    return result

@app.get("/wcag-requirements")
async def get_wcag_requirements():
    """Get WCAG contrast ratio requirements"""
    return {
        "wcag_requirements": {
            "AA": {
                "normal_text": 4.5,
                "large_text": 3.0,
                "description": "Minimum accessibility standard"
            },
            "AAA": {
                "normal_text": 7.0,
                "large_text": 4.5,
                "description": "Enhanced accessibility standard"
            }
        },
        "text_sizes": {
            "normal": "Less than 18pt regular or 14pt bold",
            "large": "18pt+ regular or 14pt+ bold"
        }
    }

@app.get("/metrics")
async def get_metrics():
    """Get service metrics"""
    return {
        "service": "accessibility-check-nim",
        "wcag_levels_supported": len(WCAGLevel),
        "colorblindness_types_supported": len(ColorBlindnessType),
        "service_status": "running"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8082))
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )

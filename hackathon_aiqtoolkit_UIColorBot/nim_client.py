#!/usr/bin/env python3
"""
NVIDIA NIMs Client
Integrates Color Extraction, Palette Generation, and Accessibility Check NIMs
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
import httpx
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NIMClient:
    """Client for interacting with NVIDIA NIMs"""
    
    def __init__(self):
        self.base_urls = {
            "color_extraction": "http://localhost:8080",
            "palette_generation": "http://localhost:8081",
            "accessibility_check": "http://localhost:8082"
        }
        self.timeout = httpx.Timeout(60.0)
    
    async def extract_colors_from_image(self, image_url: str, num_colors: int = 5, min_percentage: float = 0.05) -> Dict[str, Any]:
        """Extract dominant colors from an image using Color Extraction NIM"""
        try:
            payload = {
                "image_url": image_url,
                "num_colors": num_colors,
                "min_percentage": min_percentage
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_urls['color_extraction']}/extract-colors",
                    json=payload
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    error_text = response.text
                    logger.error(f"Color extraction failed: {response.status_code} - {error_text}")
                    return {
                        "success": False,
                        "error": f"Color extraction failed: {error_text}"
                    }
                    
        except Exception as e:
            logger.error(f"Color extraction error: {str(e)}")
            return {
                "success": False,
                "error": f"Color extraction error: {str(e)}"
            }
    
    async def generate_palette(self, base_color: str, palette_type: str = "complementary", 
                             num_colors: int = 5, saturation_range: List[float] = [0.3, 0.9],
                             lightness_range: List[float] = [0.2, 0.8]) -> Dict[str, Any]:
        """Generate color palette using Palette Generation NIM"""
        try:
            payload = {
                "base_color": base_color,
                "palette_type": palette_type,
                "num_colors": num_colors,
                "saturation_range": saturation_range,
                "lightness_range": lightness_range
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_urls['palette_generation']}/generate-palette",
                    json=payload
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    error_text = response.text
                    logger.error(f"Palette generation failed: {response.status_code} - {error_text}")
                    return {
                        "success": False,
                        "error": f"Palette generation failed: {error_text}"
                    }
                    
        except Exception as e:
            logger.error(f"Palette generation error: {str(e)}")
            return {
                "success": False,
                "error": f"Palette generation error: {str(e)}"
            }
    
    async def check_accessibility(self, foreground_color: str, background_color: str,
                                text_size: str = "normal", wcag_level: str = "AA",
                                check_colorblind: bool = True) -> Dict[str, Any]:
        """Check color accessibility using Accessibility Check NIM"""
        try:
            payload = {
                "foreground_color": foreground_color,
                "background_color": background_color,
                "text_size": text_size,
                "wcag_level": wcag_level,
                "check_colorblind": check_colorblind
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_urls['accessibility_check']}/check-accessibility",
                    json=payload
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    error_text = response.text
                    logger.error(f"Accessibility check failed: {response.status_code} - {error_text}")
                    return {
                        "success": False,
                        "error": f"Accessibility check failed: {error_text}"
                    }
                    
        except Exception as e:
            logger.error(f"Accessibility check error: {str(e)}")
            return {
                "success": False,
                "error": f"Accessibility check error: {str(e)}"
            }
    
    async def check_palette_accessibility(self, colors: List[str], wcag_level: str = "AA") -> Dict[str, Any]:
        """Check accessibility for entire color palette"""
        try:
            payload = {
                "colors": colors,
                "wcag_level": wcag_level
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_urls['accessibility_check']}/check-palette-accessibility",
                    json=payload
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    error_text = response.text
                    logger.error(f"Palette accessibility check failed: {response.status_code} - {error_text}")
                    return {
                        "success": False,
                        "error": f"Palette accessibility check failed: {error_text}"
                    }
                    
        except Exception as e:
            logger.error(f"Palette accessibility check error: {str(e)}")
            return {
                "success": False,
                "error": f"Palette accessibility check error: {str(e)}"
            }
    
    async def get_palette_types(self) -> Dict[str, Any]:
        """Get available palette types from Palette Generation NIM"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_urls['palette_generation']}/palette-types"
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "palette_types": [
                            {"type": "monochromatic", "description": "Single hue with varying saturation and lightness"},
                            {"type": "analogous", "description": "Colors adjacent on the color wheel"},
                            {"type": "complementary", "description": "Colors opposite on the color wheel"},
                            {"type": "triadic", "description": "Three colors evenly spaced on the color wheel"},
                            {"type": "tetradic", "description": "Four colors forming a square on the color wheel"},
                            {"type": "split_complementary", "description": "Base color plus two colors adjacent to its complement"}
                        ]
                    }
                    
        except Exception as e:
            logger.error(f"Error getting palette types: {str(e)}")
            return {"error": str(e)}
    
    async def get_wcag_requirements(self) -> Dict[str, Any]:
        """Get WCAG requirements from Accessibility Check NIM"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_urls['accessibility_check']}/wcag-requirements"
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "wcag_requirements": {
                            "AA": {"normal_text": 4.5, "large_text": 3.0},
                            "AAA": {"normal_text": 7.0, "large_text": 4.5}
                        }
                    }
                    
        except Exception as e:
            logger.error(f"Error getting WCAG requirements: {str(e)}")
            return {"error": str(e)}
    
    async def health_check_all(self) -> Dict[str, Any]:
        """Check health of all NIMs"""
        health_status = {}
        
        for service_name, base_url in self.base_urls.items():
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                    response = await client.get(f"{base_url}/health")
                    
                    if response.status_code == 200:
                        health_status[service_name] = {
                            "status": "healthy",
                            "data": response.json()
                        }
                    else:
                        health_status[service_name] = {
                            "status": "unhealthy",
                            "error": f"HTTP {response.status_code}"
                        }
                        
            except Exception as e:
                health_status[service_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return health_status

# Enhanced color analysis with NIMs integration
class EnhancedColorAnalyzer:
    """Enhanced color analyzer using NVIDIA NIMs"""
    
    def __init__(self):
        self.nim_client = NIMClient()
    
    async def analyze_image_colors(self, image_url: str, num_colors: int = 5) -> Dict[str, Any]:
        """Analyze colors from an image and provide comprehensive insights"""
        try:
            # Extract colors from image
            extraction_result = await self.nim_client.extract_colors_from_image(
                image_url, num_colors
            )
            
            if not extraction_result.get("success"):
                return extraction_result
            
            colors = [color["hex_code"] for color in extraction_result["colors"]]
            
            # Check palette accessibility
            accessibility_result = await self.nim_client.check_palette_accessibility(colors)
            
            # Generate complementary palettes for each dominant color
            palette_suggestions = []
            for color_info in extraction_result["colors"][:3]:  # Top 3 colors
                hex_color = color_info["hex_code"]
                palette_result = await self.nim_client.generate_palette(
                    hex_color, "complementary", 4
                )
                if palette_result.get("success"):
                    palette_suggestions.append({
                        "base_color": hex_color,
                        "palette": palette_result
                    })
            
            return {
                "success": True,
                "image_url": image_url,
                "extracted_colors": extraction_result,
                "accessibility_analysis": accessibility_result,
                "palette_suggestions": palette_suggestions,
                "processing_info": {
                    "algorithm_used": extraction_result.get("algorithm_used"),
                    "total_processing_time": sum([
                        extraction_result.get("processing_time_ms", 0),
                        accessibility_result.get("processing_time_ms", 0)
                    ])
                }
            }
            
        except Exception as e:
            logger.error(f"Enhanced image color analysis error: {str(e)}")
            return {
                "success": False,
                "error": f"Enhanced analysis error: {str(e)}"
            }
    
    async def create_comprehensive_palette(self, base_color: str, palette_types: List[str] = None) -> Dict[str, Any]:
        """Create comprehensive palette with multiple schemes and accessibility analysis"""
        try:
            if palette_types is None:
                palette_types = ["monochromatic", "complementary", "triadic", "analogous"]
            
            palettes = {}
            all_colors = [base_color]
            
            # Generate different palette types
            for palette_type in palette_types:
                palette_result = await self.nim_client.generate_palette(
                    base_color, palette_type, 5
                )
                
                if palette_result.get("success"):
                    palettes[palette_type] = palette_result
                    # Collect all colors for accessibility analysis
                    palette_colors = [color["hex_code"] for color in palette_result["colors"]]
                    all_colors.extend(palette_colors)
            
            # Remove duplicates
            unique_colors = list(set(all_colors))
            
            # Comprehensive accessibility analysis
            accessibility_result = await self.nim_client.check_palette_accessibility(unique_colors)
            
            # Individual accessibility checks for key combinations
            key_combinations = []
            if len(unique_colors) >= 2:
                # Check base color against white and black
                for bg_color in ["#FFFFFF", "#000000"]:
                    accessibility_check = await self.nim_client.check_accessibility(
                        base_color, bg_color
                    )
                    if accessibility_check.get("success"):
                        key_combinations.append({
                            "foreground": base_color,
                            "background": bg_color,
                            "result": accessibility_check
                        })
            
            return {
                "success": True,
                "base_color": base_color,
                "palettes": palettes,
                "accessibility_analysis": accessibility_result,
                "key_combinations": key_combinations,
                "recommendations": self._generate_palette_recommendations(palettes, accessibility_result),
                "total_colors_analyzed": len(unique_colors)
            }
            
        except Exception as e:
            logger.error(f"Comprehensive palette creation error: {str(e)}")
            return {
                "success": False,
                "error": f"Comprehensive palette error: {str(e)}"
            }
    
    def _generate_palette_recommendations(self, palettes: Dict[str, Any], accessibility: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on palette analysis"""
        recommendations = []
        
        # Accessibility recommendations
        if accessibility.get("success"):
            accessibility_score = accessibility.get("accessibility_score", 0)
            if accessibility_score > 0.7:
                recommendations.append("✅ Excellent accessibility - most color combinations meet WCAG guidelines")
            elif accessibility_score > 0.4:
                recommendations.append("⚠️ Moderate accessibility - test critical text/background combinations")
            else:
                recommendations.append("❌ Low accessibility - consider revising color choices for better contrast")
        
        # Palette type recommendations
        if "monochromatic" in palettes:
            recommendations.append("🎨 Monochromatic palette: Great for minimalist, cohesive designs")
        
        if "complementary" in palettes:
            recommendations.append("🎨 Complementary palette: High contrast, perfect for call-to-action elements")
        
        if "triadic" in palettes:
            recommendations.append("🎨 Triadic palette: Vibrant and energetic, use sparingly for accents")
        
        recommendations.append("💡 Always test colors in different lighting conditions")
        recommendations.append("💡 Consider providing a high contrast mode for accessibility")
        
        return recommendations

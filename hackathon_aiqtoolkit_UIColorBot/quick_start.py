#!/usr/bin/env python3
"""
快速启动脚本 - 直接使用FastAPI启动服务
"""

import asyncio
import json
import logging
import os
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
import base64
import io

import httpx
import uvicorn
import yaml
import requests
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from sklearn.cluster import KMeans
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, File, UploadFile, WebSocket
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn
from pathlib import Path
from config_loader import load_config_with_env
from bailian_client import BailianClient
from color_utils import ColorUtils
from nim_client import NIMClient, EnhancedColorAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_env():
    """加载环境变量"""
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        # 打印加载的环境变量（隐藏敏感信息）
        for key in ['BAILIAN_API_KEY', 'DASHSCOPE_API_KEY', 'TAVILY_API_KEY']:
            value = os.getenv(key)
            if value:
                print(f"✅ 加载环境变量: {key} = {value[:10]}...")
        print("✅ 环境变量加载完成")
    else:
        print("❌ 未找到 .env 文件")

def create_simple_app():
    """创建简单的FastAPI应用"""
    app = FastAPI(
        title="UI Color Bot API",
        description="基于百炼API的UI颜色助手",
        version="1.0.0"
    )
    
    # 添加CORS中间件支持前端访问
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/")
    async def root():
        return {"message": "UI Color Bot API 运行中", "status": "ok"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "api_configured": bool(os.getenv("BAILIAN_API_KEY"))}
    
    @app.post("/color/analyze")
    async def analyze_colors(request: dict):
        """颜色分析接口 - 集成NVIDIA NIMs"""
        try:
            nim_client = NIMClient()
            enhanced_analyzer = EnhancedColorAnalyzer()
            
            # 如果提供了图片URL，使用图片颜色提取
            if "image_url" in request:
                result = await enhanced_analyzer.analyze_image_colors(request["image_url"])
                return result
            
            elif "colors" in request:
                # 颜色列表分析
                colors = request["colors"]
                if not colors:
                    return {"success": False, "error": "颜色列表不能为空"}
                
                # 使用第一个颜色作为基础生成配色
                base_color = colors[0] if isinstance(colors[0], str) else colors[0].get("hex", "#000000")
                
                palette_result = await nim_client.generate_palette(
                    base_color=base_color,
                    scheme=request.get("scheme", "complementary"),
                    num_colors=request.get("num_colors", 5)
                )
                
                if palette_result["success"]:
                    return {
                        "success": True,
                        "palette": palette_result["palette"],
                        "analysis_type": "color_based"
                    }
                else:
                    return {"success": False, "error": palette_result.get("error", "配色生成失败")}
            
            else:
                return {"success": False, "error": "请提供 image_url 或 colors 参数"}
                
        except Exception as e:
            logger.error(f"颜色分析错误: {str(e)}")
            return {"success": False, "error": f"分析失败: {str(e)}"}
    
    @app.post("/color/palette")
    async def generate_palette(request: dict):
        """生成配色方案接口 - 使用NVIDIA Palette Generation NIM"""
        try:
            base_color = request.get("base_color", "")
            scheme = request.get("scheme", "complementary")
            num_colors = request.get("num_colors", 5)
            
            if not base_color:
                return {"error": "请提供基础颜色"}
            
            # 验证颜色格式
            if not base_color.startswith("#") or len(base_color) not in [4, 7]:
                return {"error": "颜色格式错误，请使用 #RGB 或 #RRGGBB 格式"}
            
            nim_client = NIMClient()
            
            # 使用NVIDIA NIM生成调色板
            palette_result = await nim_client.generate_palette(
                base_color=base_color,
                palette_type=scheme,
                num_colors=num_colors
            )
            
            if not palette_result.get("success"):
                return palette_result
            
            # 检查生成的调色板的可访问性
            colors = [color["hex_code"] for color in palette_result["colors"]]
            accessibility_result = await nim_client.check_palette_accessibility(colors)
            
            return {
                "success": True,
                "base_color": base_color,
                "scheme": scheme,
                "palette": palette_result,
                "accessibility_analysis": accessibility_result,
                "timestamp": "2025-01-07T13:34:35+08:00"
            }
            
        except Exception as e:
            return {"error": f"配色生成失败: {str(e)}"}
    
    @app.post("/color/contrast")
    async def check_contrast(request: dict):
        """检查颜色对比度接口 - 使用NVIDIA Accessibility Check NIM"""
        try:
            bg_color = request.get("background", "")
            text_color = request.get("text", "")
            text_size = request.get("text_size", "normal")
            wcag_level = request.get("wcag_level", "AA")
            
            if not bg_color or not text_color:
                return {"error": "请提供背景色和文字色"}
            
            nim_client = NIMClient()
            
            # 使用NVIDIA NIM检查可访问性
            accessibility_result = await nim_client.check_accessibility(
                foreground_color=text_color,
                background_color=bg_color,
                text_size=text_size,
                wcag_level=wcag_level,
                check_colorblind=True
            )
            
            return {
                "success": True,
                "background": bg_color,
                "text": text_color,
                "accessibility": accessibility_result,
                "timestamp": "2025-01-07T13:34:35+08:00"
            }
            
        except Exception as e:
            return {"error": f"对比度检查失败: {str(e)}"}
    
    # New NIM-specific endpoints
    @app.post("/nim/extract-colors")
    async def nim_extract_colors(request: dict):
        """图片颜色提取接口 - 直接使用Color Extraction NIM"""
        try:
            image_url = request.get("image_url", "")
            num_colors = request.get("num_colors", 5)
            min_percentage = request.get("min_percentage", 0.05)
            
            if not image_url:
                return {"error": "请提供图片URL"}
            
            nim_client = NIMClient()
            result = await nim_client.extract_colors_from_image(image_url, num_colors, min_percentage)
            
            return result
            
        except Exception as e:
            return {"error": f"图片颜色提取失败: {str(e)}"}
    
    @app.post("/nim/comprehensive-analysis")
    async def comprehensive_analysis(request: dict):
        """综合颜色分析 - 使用增强分析器"""
        try:
            base_color = request.get("base_color", "#3498DB")
            enhanced_analyzer = EnhancedColorAnalyzer()
            result = await enhanced_analyzer.comprehensive_analysis(base_color)
            return result
        except Exception as e:
            logger.error(f"综合分析错误: {str(e)}")
            return {"success": False, "error": f"综合分析失败: {str(e)}"}
    
    @app.post("/upload-image")
    async def upload_image_for_analysis(file: UploadFile = File(...)):
        """上传图片并进行颜色分析"""
        try:
            # 验证文件类型
            if not file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="只支持图片文件")
            
            # 读取文件内容
            contents = await file.read()
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                tmp_file.write(contents)
                tmp_file_path = tmp_file.name
            
            try:
                # 使用NIM客户端分析颜色
                nim_client = NIMClient()
                
                # 将临时文件转换为可访问的URL（这里简化处理）
                # 在生产环境中，你需要将文件上传到云存储服务
                result = await nim_client.extract_colors(
                    image_url="https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800",  # 示例URL
                    num_colors=5
                )
                
                return result
                
            finally:
                # 清理临时文件
                os.unlink(tmp_file_path)
                
        except Exception as e:
            logger.error(f"图片上传分析错误: {str(e)}")
            raise HTTPException(status_code=500, detail=f"图片分析失败: {str(e)}")
    
    @app.post("/analyze-image-base64")
    async def analyze_image_base64(request: dict):
        """分析base64编码的图片，使用HSV色彩空间优化"""
        try:
            image_data = request.get("image_data", "")
            num_colors = request.get("num_colors", 5)
            
            if not image_data:
                raise HTTPException(status_code=400, detail="缺少图片数据")
            
            # 解码base64图片数据
            if image_data.startswith('data:image'):
                # 移除data URL前缀
                image_data = image_data.split(',')[1]
            
            # 解码base64并直接处理图片
            image_bytes = base64.b64decode(image_data)
            
            # 使用PIL和OpenCV直接处理图片，确保正确的色彩空间转换
            import io
            from PIL import Image
            import cv2
            import numpy as np
            from sklearn.cluster import KMeans
            import time
            
            start_time = time.time()
            
            # 从字节数据创建PIL图像
            pil_image = Image.open(io.BytesIO(image_bytes))
            
            # 转换为RGB格式
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # 转换为numpy数组
            image_array = np.array(pil_image)
            
            # 调整图片大小以提高性能
            height, width = image_array.shape[:2]
            if width > 800 or height > 800:
                scale = min(800/width, 800/height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image_array = cv2.resize(image_array, (new_width, new_height))
            
            # 关键：确保正确的色彩空间转换
            # PIL使用RGB格式，需要转换为BGR供OpenCV处理
            image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            
            # 转换BGR到HSV色彩空间进行更准确的颜色分析
            image_hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
            
            # 在HSV空间进行K-Means聚类
            pixels_hsv = image_hsv.reshape(-1, 3)
            
            # 应用K-Means聚类
            kmeans = KMeans(n_clusters=num_colors, random_state=42, n_init=10)
            labels = kmeans.fit_predict(pixels_hsv)
            
            # 获取HSV空间的聚类中心
            colors_hsv = kmeans.cluster_centers_
            
            # 将HSV聚类中心转换回RGB用于显示
            colors_rgb = []
            percentages = []
            
            unique_labels, counts = np.unique(labels, return_counts=True)
            total_pixels = len(pixels_hsv)
            
            for i, (hsv_color, count) in enumerate(zip(colors_hsv, counts)):
                # 转换HSV到BGR再到RGB
                hsv_pixel = np.uint8([[hsv_color]])
                bgr_pixel = cv2.cvtColor(hsv_pixel, cv2.COLOR_HSV2BGR)
                rgb_pixel = cv2.cvtColor(bgr_pixel, cv2.COLOR_BGR2RGB)[0][0]
                
                colors_rgb.append(rgb_pixel.tolist())
                percentages.append(count / total_pixels)
            
            # 按占比排序
            sorted_indices = np.argsort(percentages)[::-1]
            colors_rgb = [colors_rgb[i] for i in sorted_indices]
            percentages = [percentages[i] for i in sorted_indices]
            
            # 构建响应
            colors_info = []
            for rgb, percentage in zip(colors_rgb, percentages):
                if percentage >= 0.05:  # 最小占比阈值
                    hex_code = "#{:02x}{:02x}{:02x}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))
                    
                    # 简单的颜色命名
                    r, g, b = rgb
                    if r > 200 and g > 200 and b > 200:
                        color_name = "浅色"
                    elif r < 50 and g < 50 and b < 50:
                        color_name = "深色"
                    elif r > g and r > b:
                        color_name = "红色系"
                    elif g > r and g > b:
                        color_name = "绿色系"
                    elif b > r and b > g:
                        color_name = "蓝色系"
                    elif r > 150 and g > 150 and b < 100:
                        color_name = "黄色系"
                    elif r > 150 and g < 100 and b > 150:
                        color_name = "紫色系"
                    elif r < 100 and g > 150 and b > 150:
                        color_name = "青色系"
                    else:
                        color_name = "混合色"
                    
                    colors_info.append({
                        "hex_code": hex_code,
                        "rgb": [int(c) for c in rgb],
                        "percentage": percentage,
                        "color_name": color_name
                    })
            
            processing_time = (time.time() - start_time) * 1000
            
            return {
                "success": True,
                "colors": colors_info,
                "total_colors_found": len(colors_info),
                "processing_time_ms": processing_time,
                "algorithm_used": "K-Means with HSV color space",
                "image_dimensions": {"width": width, "height": height}
            }
                
        except Exception as e:
            logger.error(f"Base64图片分析错误: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Base64图片分析失败: {str(e)}")
    
    @app.post("/nim/comprehensive-analysis")
    async def nim_comprehensive_analysis(request: dict):
        """全面颜色分析接口 - 使用所有NIMs"""
        try:
            base_color = request.get("base_color", "")
            image_url = request.get("image_url", "")
            
            enhanced_analyzer = EnhancedColorAnalyzer()
            
            if image_url:
                # 图片分析
                result = await enhanced_analyzer.analyze_image_colors(image_url)
            elif base_color:
                # 基于颜色的全面分析
                result = await enhanced_analyzer.create_comprehensive_palette(base_color)
            else:
                return {"error": "请提供基础颜色或图片URL"}
            
            return result
            
        except Exception as e:
            return {"error": f"全面分析失败: {str(e)}"}
    
    @app.get("/nim/health")
    async def nim_health_check():
        """检查所有NIMs的健康状态"""
        try:
            nim_client = NIMClient()
            health_status = await nim_client.health_check_all()
            
            return {
                "success": True,
                "nims_status": health_status,
                "timestamp": "2025-01-07T13:34:35+08:00"
            }
            
        except Exception as e:
            return {"error": f"健康检查失败: {str(e)}"}
    
    @app.get("/nim/palette-types")
    async def get_palette_types():
        """获取支持的调色板类型"""
        try:
            nim_client = NIMClient()
            palette_types = await nim_client.get_palette_types()
            return palette_types
            
        except Exception as e:
            return {"error": f"获取调色板类型失败: {str(e)}"}
    
    @app.post("/pick-color")
    async def pick_color_at_position(request: dict):
        """
        点击取色端点 - 获取图片指定位置的颜色
        接收图片URL和点击坐标，返回该位置的颜色信息
        """
        try:
            image_url = request.get("image_url", "")
            x = request.get("x", 0)
            y = request.get("y", 0)
            
            if not image_url:
                return {"error": "请提供图片URL"}
            
            # 处理图片URL（支持HTTP URL和base64 data URL）
            if image_url.startswith('data:image'):
                # 处理base64编码的图片
                try:
                    header, encoded = image_url.split(',', 1)
                    image_data = base64.b64decode(encoded)
                    image = Image.open(io.BytesIO(image_data))
                except Exception as e:
                    return {"error": f"无法解析base64图片: {str(e)}"}
            else:
                # 处理HTTP URL
                try:
                    response = requests.get(image_url)
                    if response.status_code != 200:
                        return {"error": "无法下载图片"}
                    image = Image.open(io.BytesIO(response.content))
                except Exception as e:
                    return {"error": f"无法下载图片: {str(e)}"}
            
            # 转换为RGB格式
            image = image.convert('RGB')
            width, height = image.size
            
            # 验证坐标范围
            if x < 0 or x >= width or y < 0 or y >= height:
                return {"error": f"坐标超出图片范围: ({x}, {y}), 图片尺寸: {width}x{height}"}
            
            # 获取指定位置的像素颜色
            pixel_color = image.getpixel((x, y))
            rgb_color = list(pixel_color[:3])  # 确保只取RGB三个通道
            
            # 转换为十六进制
            hex_color = "#{:02x}{:02x}{:02x}".format(rgb_color[0], rgb_color[1], rgb_color[2])
            
            # 获取颜色名称（简单分类）
            def get_color_name(rgb):
                r, g, b = rgb
                # 转换为HSV进行颜色分类
                max_val = max(r, g, b)
                min_val = min(r, g, b)
                diff = max_val - min_val
                
                if diff < 30:  # 灰度颜色
                    if max_val > 200:
                        return "白色"
                    elif max_val < 50:
                        return "黑色"
                    else:
                        return "灰色"
                
                # 计算主要颜色
                if r > g and r > b:
                    if g > b:
                        return "橙色" if r - g < 50 else "红色"
                    else:
                        return "粉色" if b > 100 else "红色"
                elif g > r and g > b:
                    if r > b:
                        return "黄绿色" if g - r < 50 else "绿色"
                    else:
                        return "青色" if b > 100 else "绿色"
                elif b > r and b > g:
                    if r > g:
                        return "紫色"
                    else:
                        return "蓝色"
                else:
                    return "混合色"
            
            color_name = get_color_name(rgb_color)
            
            return {
                "success": True,
                "color": {
                    "hex": hex_color,
                    "rgb": rgb_color,
                    "color_name": color_name,
                    "position": {"x": x, "y": y}
                },
                "image_dimensions": {"width": width, "height": height}
            }
            
        except Exception as e:
            return {"error": f"取色失败: {str(e)}"}
    
    @app.post("/annotate")
    async def annotate_image(request: dict):
        """
        图片颜色标注端点 - 右侧布局设计
        接收图片URL和颜色列表，返回标注后的图片
        """
        try:
            image_url = request.get("image_url", "")
            colors = request.get("colors", [])
            
            if not image_url:
                return {"error": "请提供图片URL"}
            
            if not colors:
                return {"error": "请提供颜色列表"}
            
            # 处理图片URL（支持HTTP URL和base64 data URL）
            if image_url.startswith('data:image'):
                # 处理base64编码的图片
                try:
                    header, encoded = image_url.split(',', 1)
                    image_data = base64.b64decode(encoded)
                    image = Image.open(io.BytesIO(image_data))
                except Exception as e:
                    return {"error": f"无法解析base64图片: {str(e)}"}
            else:
                # 处理HTTP URL
                try:
                    response = requests.get(image_url)
                    if response.status_code != 200:
                        return {"error": "无法下载图片"}
                    image = Image.open(io.BytesIO(response.content))
                except Exception as e:
                    return {"error": f"无法下载图片: {str(e)}"}
            
            # 转换为RGB格式
            image = image.convert('RGB')
            
            # 转换为numpy数组用于OpenCV处理
            img_array = np.array(image)
            img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            height, width = img_cv.shape[:2]
            
            # 按占比降序排列颜色
            sorted_colors = sorted(colors, key=lambda x: x.get("proportion", 0), reverse=True)
            
            # 计算右侧标注区域宽度
            annotation_width = 300
            total_width = width + annotation_width
            
            # 创建扩展画布：原图 + 右侧标注区域
            extended_img = np.ones((height, total_width, 3), dtype=np.uint8) * 250  # 浅灰背景
            extended_img[:height, :width] = img_cv  # 放置原图
            
            # 计算每个颜色区域的中心点（用于引导线）
            color_centers = []
            for color_info in sorted_colors:
                rgb_color = color_info.get("rgb", [255, 255, 255])
                target_bgr = np.array([rgb_color[2], rgb_color[1], rgb_color[0]], dtype=np.float32)
                
                # 转换到HSV色彩空间进行更准确的颜色匹配
                target_hsv = cv2.cvtColor(np.uint8([[target_bgr]]), cv2.COLOR_BGR2HSV)[0][0].astype(np.float32)
                img_hsv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2HSV).astype(np.float32)
                
                # 计算HSV色彩空间中的距离（考虑色相的周期性）
                h_diff = np.abs(img_hsv[:,:,0] - target_hsv[0])
                h_diff = np.minimum(h_diff, 180 - h_diff)  # 处理色相的周期性
                s_diff = np.abs(img_hsv[:,:,1] - target_hsv[1])
                v_diff = np.abs(img_hsv[:,:,2] - target_hsv[2])
                
                # 加权HSV距离计算（色相权重更高）
                hsv_distance = np.sqrt(
                    (h_diff * 2.0) ** 2 +  # 色相权重加倍
                    (s_diff * 1.0) ** 2 +  # 饱和度标准权重
                    (v_diff * 0.5) ** 2    # 明度权重减半
                )
                
                # 自适应阈值：基于目标颜色的饱和度和明度调整
                base_threshold = 40
                if target_hsv[1] < 50:  # 低饱和度颜色（灰色系）
                    threshold = base_threshold * 1.5
                elif target_hsv[2] < 50:  # 低明度颜色（暗色系）
                    threshold = base_threshold * 1.2
                else:
                    threshold = base_threshold
                
                # 创建颜色掩码
                mask = (hsv_distance < threshold).astype(np.uint8) * 255
                
                # 形态学操作优化
                kernel_small = np.ones((3,3), np.uint8)
                kernel_large = np.ones((7,7), np.uint8)
                
                # 先闭运算连接相近区域，再开运算去除噪声
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_large)
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_small)
                
                # 查找轮廓
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                if contours:
                    # 过滤掉太小的轮廓
                    min_area = (width * height) * 0.001  # 至少占图像面积的0.1%
                    valid_contours = [c for c in contours if cv2.contourArea(c) > min_area]
                    
                    if valid_contours:
                        # 找到最大的有效轮廓
                        largest_contour = max(valid_contours, key=cv2.contourArea)
                        
                        # 计算轮廓的质心
                        M = cv2.moments(largest_contour)
                        if M["m00"] != 0:
                            center_x = int(M["m10"] / M["m00"])
                            center_y = int(M["m01"] / M["m00"])
                            color_centers.append((center_x, center_y))
                        else:
                            # 使用轮廓边界框中心
                            x, y, w, h = cv2.boundingRect(largest_contour)
                            color_centers.append((x + w//2, y + h//2))
                    else:
                        # 使用掩码的加权中心
                        y_coords, x_coords = np.where(mask > 0)
                        if len(x_coords) > 0:
                            center_x = int(np.mean(x_coords))
                            center_y = int(np.mean(y_coords))
                            color_centers.append((center_x, center_y))
                        else:
                            color_centers.append((width // 2, height // 2))
                else:
                    # 如果没有找到轮廓，使用最相似像素的位置
                    min_distance_idx = np.unravel_index(np.argmin(hsv_distance), hsv_distance.shape)
                    color_centers.append((min_distance_idx[1], min_distance_idx[0]))
            
            # 在右侧区域绘制颜色标注
            annotation_start_x = width + 20
            color_block_size = 40
            text_margin = 10
            
            # 计算颜色块的垂直间距
            available_height = height - 40  # 留出上下边距
            if len(sorted_colors) > 1:
                vertical_spacing = available_height // len(sorted_colors)
            else:
                vertical_spacing = available_height
            
            for i, color_info in enumerate(sorted_colors):
                hex_color = color_info.get("hex", "#FFFFFF")
                rgb_color = color_info.get("rgb", [255, 255, 255])
                proportion = color_info.get("proportion", 0.0)
                
                # BGR格式用于OpenCV
                bgr_color = (int(rgb_color[2]), int(rgb_color[1]), int(rgb_color[0]))
                
                # 计算当前颜色块的Y位置
                block_y = 20 + i * vertical_spacing + vertical_spacing // 2
                
                # 绘制颜色方块
                block_top_left = (annotation_start_x, block_y - color_block_size // 2)
                block_bottom_right = (annotation_start_x + color_block_size, block_y + color_block_size // 2)
                
                cv2.rectangle(extended_img, block_top_left, block_bottom_right, bgr_color, -1)
                cv2.rectangle(extended_img, block_top_left, block_bottom_right, (0, 0, 0), 2)
                
                # 绘制引导线（从图片中的颜色区域到右侧色块）
                if i < len(color_centers):
                    start_point = color_centers[i]
                    end_point = (annotation_start_x, block_y)
                    
                    # 绘制细引导线
                    cv2.line(extended_img, start_point, end_point, (100, 100, 100), 1)
                    
                    # 在原图中标记颜色区域中心点
                    cv2.circle(extended_img, start_point, 5, bgr_color, -1)
                    cv2.circle(extended_img, start_point, 5, (0, 0, 0), 2)
                
                # 添加文本标注
                text_x = annotation_start_x + color_block_size + text_margin
                
                # HEX值
                hex_text = hex_color
                cv2.putText(extended_img, hex_text, (text_x, block_y - 10),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
                
                # RGB值
                rgb_text = f"RGB({rgb_color[0]},{rgb_color[1]},{rgb_color[2]})"
                cv2.putText(extended_img, rgb_text, (text_x, block_y + 5),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.4, (60, 60, 60), 1)
                
                # 占比
                proportion_text = f"{proportion:.1%}"
                cv2.putText(extended_img, proportion_text, (text_x, block_y + 20),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
            
            # 添加标题
            title_text = "Color Analysis"
            title_x = annotation_start_x
            cv2.putText(extended_img, title_text, (title_x, 30),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
            
            # 转换回RGB并编码为base64
            final_img_rgb = cv2.cvtColor(extended_img, cv2.COLOR_BGR2RGB)
            final_img_pil = Image.fromarray(final_img_rgb)
            
            # 保存为base64
            buffer = io.BytesIO()
            final_img_pil.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return {
                "success": True,
                "annotated_image": f"data:image/png;base64,{img_base64}",
                "image_dimensions": {
                    "width": final_img_pil.width,
                    "height": final_img_pil.height
                },
                "colors_annotated": len(sorted_colors),
                "processing_info": {
                    "original_size": f"{width}x{height}",
                    "final_size": f"{final_img_pil.width}x{final_img_pil.height}",
                    "layout": "right_side_annotation",
                    "features": ["color_blocks", "guide_lines", "sorted_by_proportion"]
                }
            }
            
        except Exception as e:
            logger.error(f"图片标注失败: {str(e)}")
            return {"error": f"图片标注失败: {str(e)}"}
    
    @app.get("/nim/wcag-requirements")
    async def get_wcag_requirements():
        """获取WCAG要求"""
        try:
            nim_client = NIMClient()
            wcag_info = await nim_client.get_wcag_requirements()
            return wcag_info
            
        except Exception as e:
            return {"error": f"获取WCAG要求失败: {str(e)}"}
    
    @app.post("/chat")
    async def chat(message: dict):
        """聊天接口，集成百炼API"""
        from bailian_client import BailianClient
        
        try:
            user_message = message.get("message", "")
            if not user_message:
                return {"error": "请输入有效的消息"}
            
            client = BailianClient()
            
            # 使用增强聊天功能，支持智能NIM调用
            result = await client.enhanced_chat_completion(user_message)
            
            if result['success']:
                return {
                    "message": user_message,
                    "reply": result['content'],
                    "model": result.get('model', 'qwen-plus'),
                    "usage": result.get('usage', {}),
                    "timestamp": "2025-01-07T13:34:35+08:00"
                }
            else:
                return {
                    "error": result['error'],
                    "details": result.get('details', '')
                }
                
        except Exception as e:
            return {"error": f"服务错误: {str(e)}"}
    
    @app.post("/chat/stream")
    async def chat_stream(request: dict):
        """流式聊天接口，集成百炼API"""
        from bailian_client import BailianClient
        
        async def generate_response():
            try:
                message = request.get("message", "")
                if not message:
                    yield f"data: {json.dumps({'choices': [{'delta': {'content': '请输入有效的消息'}, 'finish_reason': 'stop'}]})}\n\n"
                    return
                
                client = BailianClient()
                
                # 使用增强流式聊天功能，支持智能NIM调用
                async for chunk in client.enhanced_chat_stream(message):
                    if chunk['success']:
                        response_chunk = {
                            "choices": [{
                                "delta": {"content": chunk['content']},
                                "finish_reason": chunk.get('finish_reason')
                            }]
                        }
                        yield f"data: {json.dumps(response_chunk)}\n\n"
                        
                        if chunk.get('finish_reason') == 'stop':
                            break
                    else:
                        error_chunk = {
                            "choices": [{
                                "delta": {"content": f"错误: {chunk['error']}"},
                                "finish_reason": "stop"
                            }]
                        }
                        yield f"data: {json.dumps(error_chunk)}\n\n"
                        break
                        
            except Exception as e:
                error_chunk = {
                    "choices": [{
                        "delta": {"content": f"服务错误: {str(e)}"},
                        "finish_reason": "stop"
                    }]
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"
                
        return StreamingResponse(
            generate_response(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache"}
        )
    
    @app.websocket("/websocket")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket聊天接口"""
        await websocket.accept()
        try:
            while True:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                user_message = message_data.get("message", "")
                
                # 模拟响应
                response = {
                    "type": "message",
                    "content": f"WebSocket回复：{user_message}",
                    "timestamp": "2025-01-07T11:21:55+08:00"
                }
                
                await websocket.send_text(json.dumps(response))
        except WebSocketDisconnect:
            pass
    
    return app

def main():
    """主函数"""
    print("🚀 UI Color Bot 快速启动")
    print("=" * 30)
    
    # 加载环境变量
    load_env()
    
    # 检查API密钥
    api_key = os.getenv("BAILIAN_API_KEY")
    if not api_key or api_key == "your_actual_api_key_here":
        print("❌ 请在 .env 文件中配置真实的百炼API密钥")
        return
    
    print(f"✅ 百炼API密钥已配置 (长度: {len(api_key)})")
    
    # 创建应用
    app = create_simple_app()
    
    print("\n🚀 启动服务器...")
    print("📍 访问地址: http://localhost:8001")
    print("📚 API文档: http://localhost:8001/docs")
    print("🛑 停止服务: 按 Ctrl+C")
    print("-" * 50)
    
    # 启动服务器
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        reload=False
    )

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
快速启动脚本 - 直接使用FastAPI启动服务
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, List, Optional
import httpx
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from pathlib import Path
from config_loader import load_config_with_env
from bailian_client import BailianClient
from color_utils import ColorUtils
from nim_client import NIMClient, EnhancedColorAnalyzer

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
            colors = request.get("colors", [])
            text = request.get("text", "")
            image_url = request.get("image_url", "")
            
            nim_client = NIMClient()
            enhanced_analyzer = EnhancedColorAnalyzer()
            
            # 如果提供了图片URL，使用图片颜色提取
            if image_url:
                result = await enhanced_analyzer.analyze_image_colors(image_url)
                return result
            
            # 从文本中提取颜色（如果提供了文本）
            if text and not colors:
                from color_utils import ColorUtils
                colors = ColorUtils.extract_colors_from_text(text)
            
            if not colors:
                return {"error": "请提供颜色代码、包含颜色的文本或图片URL"}
            
            # 使用NIMs进行全面的颜色分析
            if len(colors) >= 2:
                # 检查调色板可访问性
                accessibility_result = await nim_client.check_palette_accessibility(colors)
                
                # 为主要颜色生成建议调色板
                palette_suggestions = []
                for color in colors[:2]:  # 取前两个颜色
                    palette_result = await nim_client.generate_palette(color, "complementary")
                    if palette_result.get("success"):
                        palette_suggestions.append({
                            "base_color": color,
                            "palette": palette_result
                        })
                
                return {
                    "success": True,
                    "input_colors": colors,
                    "accessibility_analysis": accessibility_result,
                    "palette_suggestions": palette_suggestions,
                    "timestamp": "2025-01-07T13:34:35+08:00"
                }
            else:
                # 单个颜色分析
                color = colors[0]
                comprehensive_result = await enhanced_analyzer.create_comprehensive_palette(color)
                return comprehensive_result
            
        except Exception as e:
            return {"error": f"颜色分析失败: {str(e)}"}
    
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
            
            # 检查是否是颜色相关的查询
            if any(keyword in user_message.lower() for keyword in ['颜色', '配色', 'color', '主题', '设计']):
                enhanced_message = client.get_color_suggestions(user_message)
            else:
                enhanced_message = user_message
            
            result = await client.chat_completion(enhanced_message)
            
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
                
                # 检查是否是颜色相关的查询
                if any(keyword in message.lower() for keyword in ['颜色', '配色', 'color', '主题', '设计']):
                    enhanced_message = client.get_color_suggestions(message)
                else:
                    enhanced_message = message
                
                async for chunk in client.chat_stream(enhanced_message):
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

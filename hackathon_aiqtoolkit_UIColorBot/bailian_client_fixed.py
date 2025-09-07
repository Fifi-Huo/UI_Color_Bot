#!/usr/bin/env python3
"""
百炼API客户端
集成阿里云百炼大模型API
"""

import os
import json
import httpx
from typing import Dict, Any, AsyncGenerator
import asyncio
import base64
import re

class BailianClient:
    """百炼API客户端"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or os.getenv("BAILIAN_API_KEY")
        self.base_url = base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        
        if not self.api_key:
            raise ValueError("百炼API密钥未配置")
    
    async def chat_completion(self, message: str, model: str = "qwen-plus") -> Dict[str, Any]:
        """同步聊天完成"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的UI设计顾问，具备调用NVIDIA NIM颜色分析服务的能力。当用户需要颜色分析时，你可以调用以下工具：\n1. analyze_image_colors - 分析图片中的主要颜色\n2. generate_color_palette - 基于颜色生成配色方案\n3. check_color_accessibility - 检查颜色的可访问性\n\n请根据用户需求智能选择合适的工具，并用专业的中文回答整合分析结果。"
                },
                {
                    "role": "user", 
                    "content": message
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2048
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "content": result["choices"][0]["message"]["content"],
                        "model": result.get("model", model),
                        "usage": result.get("usage", {})
                    }
                else:
                    return {
                        "success": False,
                        "error": f"API请求失败: {response.status_code}",
                        "details": response.text
                    }
                    
            except Exception as e:
                return {
                    "success": False,
                    "error": f"请求异常: {str(e)}"
                }
    
    async def chat_stream(self, message: str, model: str = "qwen-plus") -> AsyncGenerator[Dict[str, Any], None]:
        """流式聊天完成"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的UI设计顾问，具备调用NVIDIA NIM颜色分析服务的能力。当用户需要颜色分析时，你可以调用以下工具：\n1. analyze_image_colors - 分析图片中的主要颜色\n2. generate_color_palette - 基于颜色生成配色方案\n3. check_color_accessibility - 检查颜色的可访问性\n\n请根据用户需求智能选择合适的工具，并用专业的中文回答整合分析结果。"
                },
                {
                    "role": "user",
                    "content": message
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2048,
            "stream": True
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status_code != 200:
                        yield {
                            "success": False,
                            "error": f"流式请求失败: {response.status_code}"
                        }
                        return
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                                
                            try:
                                chunk_data = json.loads(data_str)
                                if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                                    choice = chunk_data["choices"][0]
                                    if "delta" in choice and "content" in choice["delta"]:
                                        yield {
                                            "success": True,
                                            "content": choice["delta"]["content"],
                                            "finish_reason": choice.get("finish_reason")
                                        }
                            except json.JSONDecodeError:
                                continue
                                
            except Exception as e:
                yield {
                    "success": False,
                    "error": f"流式请求失败: {str(e)}"
                }

    async def analyze_user_intent(self, message: str) -> Dict[str, Any]:
        """分析用户意图，判断是否需要调用NIM服务"""
        # 检查是否包含图片分析请求
        image_keywords = ['分析图片', '图片颜色', '提取颜色', '图像分析', '颜色分析', '图片中的', '图像中的']
        palette_keywords = ['配色方案', '调色板', '颜色搭配', '配色建议', '色彩方案', '配色搭配', '搭配怎么样']
        accessibility_keywords = ['可访问性', '对比度', '色盲', 'WCAG', '无障碍']
        
        # 检查是否同时提到图片和配色
        has_image_and_palette = ('图片' in message or 'data:image' in message) and any(keyword in message for keyword in palette_keywords)
        
        intent = {
            'needs_image_analysis': any(keyword in message for keyword in image_keywords) or has_image_and_palette,
            'needs_palette_generation': any(keyword in message for keyword in palette_keywords),
            'needs_accessibility_check': any(keyword in message for keyword in accessibility_keywords),
            'has_image': 'data:image' in message or '图片' in message,
            'has_color': re.search(r'#[0-9a-fA-F]{6}|rgb\(|颜色.*#', message),
            'needs_combined_analysis': has_image_and_palette  # 需要组合分析
        }
        
        return intent
    
    async def call_nim_service(self, service_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """调用NIM服务"""
        base_url = "http://localhost:8001"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if service_type == "analyze_image":
                    response = await client.post(f"{base_url}/analyze-image-base64", json=data)
                elif service_type == "generate_palette":
                    response = await client.post(f"{base_url}/color/palette", json=data)
                elif service_type == "check_accessibility":
                    response = await client.post(f"{base_url}/color/accessibility", json=data)
                else:
                    return {"success": False, "error": f"未知的服务类型: {service_type}"}
                
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                else:
                    return {"success": False, "error": f"服务调用失败: {response.status_code}"}
                    
        except Exception as e:
            return {"success": False, "error": f"NIM服务调用异常: {str(e)}"}
    
    async def enhanced_chat_completion(self, message: str) -> Dict[str, Any]:
        """增强的聊天完成，支持智能NIM调用"""
        try:
            # 分析用户意图
            intent = await self.analyze_user_intent(message)
            
            # 提取图片数据（如果有）
            image_data = None
            if intent['has_image']:
                # 提取base64图片数据
                image_match = re.search(r'data:image/[^;]+;base64,([^\s]+)', message)
                if image_match:
                    image_data = image_match.group(1)
            
            # 提取颜色数据（如果有）
            color_data = None
            if intent['has_color']:
                color_match = re.search(r'#([0-9a-fA-F]{6})', message)
                if color_match:
                    color_data = f"#{color_match.group(1)}"
            
            # 调用相应的NIM服务
            nim_results = {}
            extracted_colors = []
            
            # 如果需要图片分析，先提取颜色
            if intent['needs_image_analysis'] and image_data:
                result = await self.call_nim_service("analyze_image", {"image_data": image_data})
                if result['success']:
                    nim_results['image_analysis'] = result['data']
                    # 提取主要颜色用于后续分析
                    if 'colors' in result['data']:
                        extracted_colors = [color.get('hex_code', '') for color in result['data']['colors'][:3]]
            
            # 如果需要配色生成，使用提取的颜色或用户提供的颜色
            if intent['needs_palette_generation']:
                base_color = None
                if extracted_colors:
                    base_color = extracted_colors[0]  # 使用主要颜色
                elif color_data:
                    base_color = color_data
                
                if base_color:
                    result = await self.call_nim_service("generate_palette", {"base_color": base_color})
                    if result['success']:
                        nim_results['palette_generation'] = result['data']
            
            # 如果需要可访问性检查
            if intent['needs_accessibility_check']:
                check_colors = extracted_colors if extracted_colors else ([color_data] if color_data else [])
                for i, color in enumerate(check_colors[:2]):  # 检查前2个主要颜色
                    if color:
                        result = await self.call_nim_service("check_accessibility", {"color": color})
                        if result['success']:
                            if 'accessibility_check' not in nim_results:
                                nim_results['accessibility_check'] = []
                            nim_results['accessibility_check'].append({
                                'color': color,
                                'analysis': result['data']
                            })
            
            # 构建增强的消息
            enhanced_message = message
            if nim_results:
                enhanced_message += "\n\n=== NIM分析结果 ===\n"
                for service, data in nim_results.items():
                    enhanced_message += f"\n{service}: {json.dumps(data, ensure_ascii=False, indent=2)}\n"
                enhanced_message += "\n请基于以上分析结果，提供专业的UI设计建议。"
            
            # 调用AI进行回答
            return await self.chat_completion(enhanced_message)
            
        except Exception as e:
            return {"success": False, "error": f"增强聊天处理失败: {str(e)}"}
    
    async def enhanced_chat_stream(self, message: str) -> AsyncGenerator[Dict[str, Any], None]:
        """增强的流式聊天，支持智能NIM调用"""
        try:
            # 分析用户意图
            intent = await self.analyze_user_intent(message)
            
            # 提取图片数据（如果有）
            image_data = None
            if intent['has_image']:
                image_match = re.search(r'data:image/[^;]+;base64,([^\s]+)', message)
                if image_match:
                    image_data = image_match.group(1)
            
            # 提取颜色数据（如果有）
            color_data = None
            if intent['has_color']:
                color_match = re.search(r'#([0-9a-fA-F]{6})', message)
                if color_match:
                    color_data = f"#{color_match.group(1)}"
            
            # 调用相应的NIM服务
            nim_results = {}
            extracted_colors = []
            
            # 如果需要图片分析，先提取颜色
            if intent['needs_image_analysis'] and image_data:
                result = await self.call_nim_service("analyze_image", {"image_data": image_data})
                if result['success']:
                    nim_results['image_analysis'] = result['data']
                    # 提取主要颜色用于后续分析
                    if 'colors' in result['data']:
                        extracted_colors = [color.get('hex_code', '') for color in result['data']['colors'][:3]]
            
            # 如果需要配色生成，使用提取的颜色或用户提供的颜色
            if intent['needs_palette_generation']:
                base_color = None
                if extracted_colors:
                    base_color = extracted_colors[0]  # 使用主要颜色
                elif color_data:
                    base_color = color_data
                
                if base_color:
                    result = await self.call_nim_service("generate_palette", {"base_color": base_color})
                    if result['success']:
                        nim_results['palette_generation'] = result['data']
            
            # 如果需要可访问性检查
            if intent['needs_accessibility_check']:
                check_colors = extracted_colors if extracted_colors else ([color_data] if color_data else [])
                for i, color in enumerate(check_colors[:2]):  # 检查前2个主要颜色
                    if color:
                        result = await self.call_nim_service("check_accessibility", {"color": color})
                        if result['success']:
                            if 'accessibility_check' not in nim_results:
                                nim_results['accessibility_check'] = []
                            nim_results['accessibility_check'].append({
                                'color': color,
                                'analysis': result['data']
                            })
            
            # 构建增强的消息
            enhanced_message = message
            if nim_results:
                enhanced_message += "\n\n=== NIM分析结果 ===\n"
                for service, data in nim_results.items():
                    enhanced_message += f"\n{service}: {json.dumps(data, ensure_ascii=False, indent=2)}\n"
                enhanced_message += "\n请基于以上分析结果，提供专业的UI设计建议。"
            
            # 调用AI进行流式回答
            async for chunk in self.chat_stream(enhanced_message):
                yield chunk
                
        except Exception as e:
            yield {"success": False, "error": f"增强流式聊天处理失败: {str(e)}"}

# 测试函数
async def test_bailian_client():
    """测试百炼客户端"""
    try:
        client = BailianClient()
        
        # 测试同步聊天
        result = await client.chat_completion("你好，请介绍一下你的功能")
        print("同步聊天测试:")
        print(f"成功: {result['success']}")
        if result['success']:
            print(f"回复: {result['content'][:100]}...")
        else:
            print(f"错误: {result['error']}")
        
        print("\n" + "="*50 + "\n")
        
        # 测试流式聊天
        print("流式聊天测试:")
        async for chunk in client.chat_stream("推荐一个现代化的蓝色主题UI配色方案"):
            if chunk['success']:
                print(chunk['content'], end='', flush=True)
            else:
                print(f"错误: {chunk['error']}")
                break
        print("\n")
        
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_bailian_client())

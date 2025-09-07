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
                    "content": "你是一个专业的UI设计助手，专门帮助用户解决界面设计和颜色搭配问题。请用中文回答。"
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
                response.raise_for_status()
                result = response.json()
                
                if "choices" in result and len(result["choices"]) > 0:
                    return {
                        "success": True,
                        "content": result["choices"][0]["message"]["content"],
                        "model": result.get("model", model),
                        "usage": result.get("usage", {})
                    }
                else:
                    return {
                        "success": False,
                        "error": "API响应格式异常"
                    }
                    
            except httpx.HTTPStatusError as e:
                return {
                    "success": False,
                    "error": f"HTTP错误: {e.response.status_code}",
                    "details": e.response.text
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"请求失败: {str(e)}"
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
                    "content": "你是一个专业的UI设计助手，专门帮助用户解决界面设计和颜色搭配问题。请用中文回答。"
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
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]  # 移除 "data: " 前缀
                            
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

    def get_color_suggestions(self, description: str) -> str:
        """获取颜色建议的专门提示词"""
        return f"""
        作为UI设计专家，请为以下场景推荐合适的颜色搭配：

        场景描述：{description}

        请提供：
        1. 主色调建议（包含具体的十六进制颜色代码）
        2. 辅助色彩搭配
        3. 文字颜色建议
        4. 背景色建议
        5. 简要说明选择这些颜色的设计理由

        请确保颜色搭配符合现代UI设计原则，具有良好的对比度和可访问性。
        """

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

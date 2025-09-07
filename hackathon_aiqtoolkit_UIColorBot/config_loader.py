#!/usr/bin/env python3
"""
配置加载器 - 安全地从环境变量加载API密钥
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any

def load_config_with_env(config_path: str) -> Dict[str, Any]:
    """
    加载配置文件并替换环境变量占位符
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        解析后的配置字典
    """
    # 加载 .env 文件（如果存在）
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    
    # 也尝试从python-dotenv加载
    try:
        from dotenv import load_dotenv as dotenv_load
        dotenv_load(env_path)
    except ImportError:
        pass
    
    # 读取配置文件
    with open(config_path, 'r', encoding='utf-8') as f:
        config_content = f.read()
    
    # 替换环境变量占位符
    config_content = os.path.expandvars(config_content)
    
    # 解析YAML
    config = yaml.safe_load(config_content)
    
    return config

def load_dotenv(env_path: Path):
    """
    简单的 .env 文件加载器
    """
    if not env_path.exists():
        return
        
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                # 移除引号（如果有）
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                os.environ[key] = value
                print(f"✅ 加载环境变量: {key} = {value[:10]}...")

def get_api_key(key_name: str) -> str:
    """
    安全地获取API密钥
    
    Args:
        key_name: 环境变量名称
        
    Returns:
        API密钥
        
    Raises:
        ValueError: 如果未找到API密钥
    """
    api_key = os.getenv(key_name)
    if not api_key:
        raise ValueError(f"未找到环境变量 {key_name}，请检查 .env 文件或系统环境变量")
    
    if api_key in ["your_actual_api_key_here", "Your API Key"]:
        raise ValueError(f"请在 .env 文件中设置真实的 {key_name}")
    
    return api_key

# 使用示例
if __name__ == "__main__":
    try:
        # 加载配置
        config = load_config_with_env("configs/hackathon_config.yml")
        
        # 验证API密钥
        bailian_key = get_api_key("BAILIAN_API_KEY")
        print(f"✅ 百炼API密钥已正确配置 (长度: {len(bailian_key)})")
        
        print("✅ 配置加载成功")
        
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")

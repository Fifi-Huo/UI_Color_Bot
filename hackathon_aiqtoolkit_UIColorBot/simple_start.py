#!/usr/bin/env python3
"""
简化的项目启动脚本
当API配置完成后，直接运行此脚本启动项目
"""

import os
import sys
import subprocess
from pathlib import Path
from config_loader import load_config_with_env, get_api_key

def check_api_keys():
    """检查API密钥配置"""
    # 先加载 .env 文件
    from pathlib import Path
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        from config_loader import load_dotenv
        load_dotenv(env_path)
    
    try:
        bailian_key = get_api_key("BAILIAN_API_KEY")
        print(f"✅ 百炼API密钥已配置 (长度: {len(bailian_key)})")
        return True
    except ValueError as e:
        print(f"❌ {e}")
        return False

def start_server():
    """启动服务器"""
    try:
        # 加载配置
        config = load_config_with_env("configs/hackathon_config.yml")
        print("✅ 配置文件加载成功")
        
        # 启动服务
        print("🚀 启动服务器...")
        print("📍 访问地址: http://localhost:8001")
        print("📚 API文档: http://localhost:8001/docs")
        print("🛑 停止服务: 按 Ctrl+C")
        print("-" * 50)
        
        # 使用subprocess启动aiq serve
        cmd = [
            sys.executable, "-m", "aiq.cli.serve",
            "--config_file", "configs/hackathon_config.yml",
            "--host", "0.0.0.0",
            "--port", "8001"
        ]
        
        subprocess.run(cmd)
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 UI Color Bot 启动器")
    print("=" * 30)
    
    # 检查API密钥
    if not check_api_keys():
        print("\n📝 请先在 .env 文件中配置你的百炼API密钥:")
        print("   BAILIAN_API_KEY=sk-your-actual-api-key")
        return
    
    # 启动服务器
    start_server()

if __name__ == "__main__":
    main()

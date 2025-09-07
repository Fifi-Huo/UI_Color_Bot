#!/bin/bash

echo "🚀 启动 UI Color Bot 项目"
echo "========================="

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv .venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source .venv/bin/activate

# 安装基础依赖
echo "📥 安装依赖包..."
pip install --upgrade pip
pip install -e .
pip install tavily-python python-dotenv pyyaml

# 验证配置
echo "✅ 验证API配置..."
python config_loader.py

if [ $? -eq 0 ]; then
    echo "🎉 配置验证成功！"
    echo ""
    echo "🚀 启动服务..."
    aiq serve --config_file configs/hackathon_config.yml --host 0.0.0.0 --port 8001
else
    echo "❌ 配置验证失败，请检查 .env 文件中的API密钥"
    echo ""
    echo "📝 需要在 .env 文件中设置："
    echo "   BAILIAN_API_KEY=你的百炼API密钥"
    echo "   TAVILY_API_KEY=你的Tavily API密钥（可选）"
fi

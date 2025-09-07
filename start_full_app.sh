#!/bin/bash

echo "🚀 启动完整的 UI Color Bot 应用"
echo "================================="

# 检查是否在正确的目录
if [ ! -d "hackathon_aiqtoolkit_UIColorBot" ] || [ ! -d "NeMo-Agent-Toolkit-UI" ]; then
    echo "❌ 请在包含 hackathon_aiqtoolkit_UIColorBot 和 NeMo-Agent-Toolkit-UI 的目录中运行此脚本"
    exit 1
fi

# 启动后端服务
echo "📡 启动后端服务..."
cd hackathon_aiqtoolkit_UIColorBot
source .venv/bin/activate
python quick_start.py &
BACKEND_PID=$!
echo "后端服务 PID: $BACKEND_PID"

# 等待后端启动
echo "⏳ 等待后端服务启动..."
sleep 5

# 启动前端服务
echo "🎨 启动前端服务..."
cd ../NeMo-Agent-Toolkit-UI
npm run dev &
FRONTEND_PID=$!
echo "前端服务 PID: $FRONTEND_PID"

# 返回根目录
cd ..

echo ""
echo "✅ 应用启动完成！"
echo ""
echo "🌐 访问地址:"
echo "   前端界面: http://localhost:3000"
echo "   后端API:  http://localhost:8001"
echo "   API文档:  http://localhost:8001/docs"
echo ""
echo "🛑 停止服务: 按 Ctrl+C 或运行以下命令:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo ""

# 保存进程ID到文件
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

# 等待用户中断
wait

# 🎨 UI Color Bot 用户指南

## 📖 项目概述

UI Color Bot 是一个基于百炼API的专业UI颜色设计助手，集成了NVIDIA NeMo Agent Toolkit UI前端界面，提供智能的颜色分析、配色建议和可访问性检查功能。

## 🚀 快速开始

### 启动应用
```bash
cd /Users/fifihuo/Documents/UI_Color_Bot
./start_full_app.sh
```

### 访问地址
- **前端界面**: http://localhost:3000
- **后端API**: http://localhost:8001
- **API文档**: http://localhost:8001/docs

## 🎯 主要功能

### 1. 智能聊天助手
- **功能**: 基于百炼API的专业UI设计对话
- **特色**: 自动识别颜色相关查询并提供专业建议
- **使用**: 在前端界面直接对话

**示例对话**:
- "帮我设计一个现代化的蓝色主题配色方案"
- "这个网站的颜色搭配怎么样？#3498db #e74c3c"
- "什么颜色适合做按钮的背景色？"

### 2. 颜色分析 API

#### 分析配色方案
```bash
POST /color/analyze
{
  "colors": ["#3498db", "#e74c3c", "#2ecc71"]
}
```

**返回信息**:
- 配色和谐类型（互补色、类似色等）
- 颜色对比度分析
- 可访问性评估
- 优化建议

#### 生成配色方案
```bash
POST /color/palette
{
  "base_color": "#3498db",
  "scheme": "complementary"
}
```

**支持的配色方案**:
- `complementary`: 互补色
- `triadic`: 三角配色
- `analogous`: 类似色
- `monochromatic`: 单色配色

#### 对比度检查
```bash
POST /color/contrast
{
  "background": "#ffffff",
  "text": "#333333"
}
```

**返回标准**:
- WCAG AA/AAA 合规性
- 对比度数值
- 可访问性建议

### 3. 流式聊天
```bash
POST /chat/stream
{
  "message": "推荐一个适合电商网站的配色方案"
}
```

## 🛠️ 技术特性

### 后端技术栈
- **框架**: FastAPI
- **AI模型**: 阿里云百炼 (qwen-plus)
- **颜色处理**: 自研颜色工具库
- **通信**: WebSocket + HTTP Stream

### 前端技术栈
- **框架**: Next.js 14
- **UI库**: NVIDIA NeMo Agent Toolkit UI
- **样式**: Tailwind CSS
- **通信**: WebSocket + Server-Sent Events

### 颜色工具功能
- 颜色格式转换 (HEX ↔ RGB ↔ HSL)
- WCAG 对比度计算
- 配色方案生成
- 可访问性评估
- 颜色提取和分析

## 📝 使用示例

### 1. 获取网站配色建议
**输入**: "我要做一个科技公司的官网，请推荐配色方案"

**AI回复**: 提供具体的颜色代码、搭配理由和使用建议

### 2. 检查现有配色
**输入**: "分析这个配色：#2c3e50 #3498db #e74c3c #f39c12"

**系统分析**: 
- 配色类型识别
- 对比度评估
- 可访问性检查
- 优化建议

### 3. 生成配色变体
**API调用**: 
```json
{
  "base_color": "#3498db",
  "scheme": "monochromatic"
}
```

**返回结果**: 5个基于基础色的单色配色方案

## 🔧 配置说明

### 环境变量 (.env)
```bash
# 百炼API配置
BAILIAN_API_KEY=sk-your-bailian-api-key
DASHSCOPE_API_KEY=sk-your-dashscope-api-key

# Tavily搜索API（可选）
TAVILY_API_KEY=tvly-your-tavily-api-key
```

### 前端配置 (NeMo-Agent-Toolkit-UI/.env)
```bash
NEXT_PUBLIC_WORKFLOW=UI Color Bot
NEXT_PUBLIC_HTTP_CHAT_COMPLETION_URL=http://127.0.0.1:8001/chat/stream
NEXT_PUBLIC_WEBSOCKET_CHAT_COMPLETION_URL=ws://127.0.0.1:8001/websocket
```

## 🚨 故障排除

### 常见问题

1. **API密钥错误**
   - 检查 `.env` 文件中的密钥格式
   - 确认百炼API密钥有效性

2. **前端连接失败**
   - 确认后端服务运行在 8001 端口
   - 检查CORS配置

3. **颜色格式错误**
   - 使用标准十六进制格式: `#RRGGBB` 或 `#RGB`
   - 确保颜色代码以 `#` 开头

### 重启服务
```bash
# 停止所有服务
pkill -f "python quick_start.py"
pkill -f "next dev"

# 重新启动
./start_full_app.sh
```

## 📊 API 端点总览

| 端点 | 方法 | 功能 | 参数 |
|------|------|------|------|
| `/` | GET | 健康检查 | 无 |
| `/health` | GET | 系统状态 | 无 |
| `/chat` | POST | 同步聊天 | `{message}` |
| `/chat/stream` | POST | 流式聊天 | `{message}` |
| `/color/analyze` | POST | 颜色分析 | `{colors, text}` |
| `/color/palette` | POST | 生成配色 | `{base_color, scheme}` |
| `/color/contrast` | POST | 对比度检查 | `{background, text}` |
| `/websocket` | WS | WebSocket聊天 | 实时消息 |

## 🎨 设计原则

### 可访问性优先
- 遵循WCAG 2.1标准
- 提供对比度检查
- 支持色盲友好配色

### 专业性
- 基于色彩理论的配色算法
- 现代UI设计趋势
- 品牌色彩心理学

### 易用性
- 直观的对话界面
- 丰富的API接口
- 详细的分析报告

## 🔮 未来规划

- [ ] 图片颜色提取
- [ ] 品牌色彩分析
- [ ] 色彩趋势预测
- [ ] 更多配色方案
- [ ] 移动端适配

---

**技术支持**: 如有问题，请检查日志文件或重启服务

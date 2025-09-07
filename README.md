# 🎨 UI Color Bot

<div align="center">

![UI Color Bot](https://img.shields.io/badge/UI%20Color%20Bot-v1.2-blue.svg)
![NVIDIA NIM](https://img.shields.io/badge/NVIDIA-NIM-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-red.svg)
![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)
![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)

**专业的AI驱动UI颜色设计助手**

HSV色彩空间优化 | NVIDIA NIM微服务 | GPU加速颜色分析 | 点击取色功能 | 智能配色生成 | 可访问性检查

[快速开始](#-快速开始) • [功能特性](#-功能特性) • [API文档](#-api-文档) • [部署指南](#-部署指南)

</div>

---

## 📖 项目概述

UI Color Bot 是一个基于NVIDIA NIM微服务和百炼API的专业UI颜色设计平台，提供：

- 🤖 **智能聊天助手**: 基于大语言模型的专业颜色设计对话
- 🎨 **GPU加速颜色分析**: 使用NVIDIA cuML K-Means算法进行高效颜色提取
- 🖱️ **点击取色功能**: 精确获取图片任意位置的颜色，自动可访问性分析
- 🌈 **AI配色生成**: 7种和谐配色方案智能生成
- ♿ **可访问性检查**: WCAG标准合规性检测和色盲友好性分析
- 📊 **颜色标注图**: 专业的颜色区域标注和可视化
- 🎯 **色板管理**: 完整的颜色信息展示和批量操作

## 🚀 快速开始

### 系统要求

- Python 3.8+
- Node.js 16+
- NVIDIA GPU (推荐，用于加速颜色分析)
- Docker (可选)

### 一键启动

```bash
# 克隆项目
git clone <repository-url>
cd UI_Color_Bot

# 启动完整应用
./start_full_app.sh
```

### 访问地址

| 服务 | 地址 | 描述 |
|------|------|------|
| 🖥️ **前端界面** | http://localhost:3001 | 主要用户界面 |
| 🔧 **后端API** | http://localhost:8001 | FastAPI后端服务 |
| 📚 **API文档** | http://localhost:8001/docs | Swagger API文档 |
| 🎨 **颜色分析页** | http://localhost:3001/color-analysis | 专业颜色分析工具 |

## ✨ 功能特性

### 🤖 智能聊天助手

- **多模态交互**: 支持文本对话和图片上传
- **专业建议**: 基于色彩理论的设计建议
- **实时分析**: 上传图片自动进行颜色分析
- **流式响应**: 实时对话体验

**示例对话**:
```
用户: "帮我设计一个现代化的科技公司配色方案"
AI: 为您推荐以下现代科技风格配色方案...
    主色: #2563eb (专业蓝)
    辅色: #64748b (中性灰)
    强调色: #06b6d4 (青色)
```

### 🎨 GPU加速颜色分析

- **NVIDIA cuML K-Means**: GPU加速聚类算法，支持HSV色彩空间优化
- **HSV色彩空间**: 基于人眼视觉感知的颜色分析，提供更准确的颜色识别
- **智能颜色提取**: 自动识别图片中的主要颜色，支持base64和URL图片
- **精确分析**: 提供HEX、RGB、HSL格式和颜色占比
- **处理优化**: 毫秒级响应时间，支持图片压缩和大文件处理

### 🖱️ 点击取色功能

- **精确取色**: 点击图片任意位置获取像素级精确颜色
- **实时可访问性分析**: 自动检测WCAG AA/AAA标准合规性
- **对比度计算**: 与白色背景的精确对比度比值
- **色盲友好性**: 8种色盲类型的友好性评估
- **详细信息展示**: HEX、RGB值、颜色名称和改进建议
- **批量取色**: 支持多点取色，统一管理和分析

### 🌈 AI配色生成

支持7种专业配色方案：

| 配色类型 | 描述 | 适用场景 |
|----------|------|----------|
| **Complementary** | 互补色 | 强对比设计 |
| **Triadic** | 三角配色 | 活力丰富 |
| **Analogous** | 类似色 | 和谐统一 |
| **Monochromatic** | 单色配色 | 简约优雅 |
| **Split Complementary** | 分裂互补 | 平衡对比 |
| **Tetradic** | 四角配色 | 丰富层次 |
| **Square** | 正方形配色 | 均衡多彩 |

### ♿ 可访问性检查

- **WCAG 2.1合规**: AA/AAA级别检测
- **对比度计算**: 精确的颜色对比度分析
- **色盲友好**: 8种色盲类型模拟
- **优化建议**: 具体的改进方案

### 📊 颜色标注图

- **专业标注**: 右侧布局 + 颜色块 + 引导线
- **详细信息**: HEX、RGB值和占比显示
- **可视化**: 清晰的颜色区域标识
- **导出功能**: PNG格式下载

### 🎯 色板管理

- **响应式网格**: 2-6列自适应布局
- **交互式色块**: 点击复制，悬停预览
- **批量操作**: 一键复制所有颜色值
- **数据导出**: JSON格式完整色板数据

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js 14)                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │ Chat Interface│ │Color Analysis│ │  Color Palette Panel  │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/WebSocket
┌─────────────────────┴───────────────────────────────────────┐
│                 Backend (FastAPI)                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │   Chat API  │ │ Color APIs  │ │    Annotation API       │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                NVIDIA NIM Microservices                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │Color Extract│ │Palette Gen  │ │  Accessibility Check    │ │
│  │  (cuML)     │ │    (AI)     │ │      (WCAG)             │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 技术栈

### 后端技术

- **FastAPI**: 高性能Python Web框架
- **NVIDIA cuML**: GPU加速机器学习库
- **OpenCV**: 图像处理和标注
- **Pillow**: 图像操作和格式转换
- **DashScope**: 阿里云百炼大语言模型API

### 前端技术

- **Next.js 14**: React全栈框架
- **TypeScript**: 类型安全的JavaScript
- **Tailwind CSS**: 实用优先的CSS框架
- **Tabler Icons**: 现代图标库
- **React Hot Toast**: 优雅的通知组件

### NVIDIA NIM微服务

- **color-extraction-nim**: GPU加速颜色提取服务
- **palette-generation-nim**: AI驱动配色生成服务
- **accessibility-check-nim**: 可访问性检查服务

## 📋 API 文档

### 核心端点

| 端点 | 方法 | 功能 | 参数 |
|------|------|------|------|
| `/health` | GET | 健康检查 | 无 |
| `/chat` | POST | 智能对话 | `{message, attachments?}` |
| `/chat/stream` | POST | 流式对话 | `{message}` |
| `/analyze-image-base64` | POST | HSV颜色分析 | `{image_data, num_colors?}` |
| `/pick-color` | POST | 点击取色 | `{image_url, x, y}` |
| `/color/analyze` | POST | 颜色分析 | `{image_url}` |
| `/color/palette` | POST | 配色生成 | `{base_color, harmony_type}` |
| `/color/accessibility` | POST | 可访问性检查 | `{colors}` |
| `/annotate` | POST | 颜色标注图 | `{image_url}` |

### 使用示例

#### HSV颜色分析 (推荐)
```bash
curl -X POST "http://localhost:8001/analyze-image-base64" \
  -H "Content-Type: application/json" \
  -d '{
    "image_data": "data:image/jpeg;base64,/9j4AAQSkZJRgABA...",
    "num_colors": 5
  }'
```

#### 传统颜色分析
```bash
curl -X POST "http://localhost:8001/color/analyze" \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/image.jpg"}'
```

#### 点击取色
```bash
curl -X POST "http://localhost:8001/pick-color" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "data:image/jpeg;base64,/9j4AAQSkZJRgABA...",
    "x": 150,
    "y": 200
  }'
```

#### 配色生成
```bash
curl -X POST "http://localhost:8001/color/palette" \
  -H "Content-Type: application/json" \
  -d '{"base_color": "#3498db", "harmony_type": "complementary"}'
```

#### 标注图生成
```bash
curl -X POST "http://localhost:8001/annotate" \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/image.jpg"}'
```

## ⚙️ 配置说明

### 环境变量

创建 `hackathon_aiqtoolkit_UIColorBot/.env` 文件：

```bash
# 百炼API配置
BAILIAN_API_KEY=sk-your-bailian-api-key
DASHSCOPE_API_KEY=sk-your-dashscope-api-key

# GPU设备配置
CUDA_VISIBLE_DEVICES=0

# 服务端口配置
BACKEND_PORT=8001
FRONTEND_PORT=3001
```

### 前端配置

创建 `NeMo-Agent-Toolkit-UI/.env.local` 文件：

```bash
NEXT_PUBLIC_WORKFLOW=UI Color Bot
NEXT_PUBLIC_HTTP_CHAT_COMPLETION_URL=http://127.0.0.1:8001/chat/stream
NEXT_PUBLIC_WEBSOCKET_CHAT_COMPLETION_URL=ws://127.0.0.1:8001/websocket
```

## 🐳 Docker部署

### 构建镜像

```bash
# 构建NIM微服务
docker-compose -f docker-compose-nims.yml up -d

# 构建主应用
docker build -t ui-color-bot .
```

### 运行容器

```bash
docker run -d \
  --name ui-color-bot \
  --gpus all \
  -p 8001:8001 \
  -p 3001:3001 \
  -e DASHSCOPE_API_KEY=your-api-key \
  ui-color-bot
```

## 🧪 测试

### 运行测试套件

```bash
# 测试NIM微服务
python test_all_nims.py

# 测试集成系统
python test_integrated_system.py
```

### 测试结果示例

```
✅ Color Extraction NIM: 100% success rate
✅ Palette Generation NIM: 100% success rate  
✅ Accessibility Check NIM: 100% success rate
✅ Integrated System: All workflows working
```

## 🚨 故障排除

### 常见问题

1. **GPU内存不足**
   ```bash
   # 检查GPU使用情况
   nvidia-smi
   
   # 重启CUDA服务
   sudo systemctl restart nvidia-persistenced
   ```

2. **API密钥错误**
   ```bash
   # 验证环境变量
   echo $DASHSCOPE_API_KEY
   
   # 重新加载环境变量
   source .env
   ```

3. **端口冲突**
   ```bash
   # 检查端口占用
   lsof -i :8001
   lsof -i :3001
   
   # 终止占用进程
   pkill -f "python quick_start.py"
   pkill -f "next dev"
   ```

### 重启服务

```bash
# 完全重启
./start_full_app.sh

# 单独重启后端
cd hackathon_aiqtoolkit_UIColorBot
python quick_start.py

# 单独重启前端
cd NeMo-Agent-Toolkit-UI
npm run dev
```

## 🎯 使用场景

### 设计师工作流

1. **图片颜色提取**: 上传设计稿，自动提取主要颜色
2. **配色方案生成**: 基于品牌色生成和谐配色
3. **可访问性检查**: 确保设计符合WCAG标准
4. **标注图导出**: 生成专业的颜色标注文档

### 开发者集成

1. **API调用**: 集成颜色分析功能到现有系统
2. **批量处理**: 大量图片的颜色数据提取
3. **自动化检查**: CI/CD流程中的可访问性验证

### 品牌管理

1. **品牌色分析**: 分析竞品和市场趋势
2. **色彩一致性**: 确保多平台色彩统一
3. **可访问性合规**: 满足无障碍设计要求

## 🆕 最新更新 (v1.2)

### 🖱️ 点击取色功能
- ✅ **精确像素取色**: 点击图片任意位置获取精确颜色值
- ✅ **自动可访问性分析**: 取色时自动进行WCAG标准检测
- ✅ **实时对比度计算**: 与白色背景的精确对比度比值
- ✅ **色盲友好性检测**: 8种色盲类型的可用性评估
- ✅ **详细信息展示**: HEX、RGB、颜色名称和改进建议
- ✅ **批量取色管理**: 支持多点取色，统一查看和分析

### 🔧 API端点优化
- ✅ **新增/pick-color端点**: 支持坐标点击取色功能
- ✅ **修复API路由错误**: 正确调用/analyze-image-base64端点
- ✅ **解决URL长度限制**: 支持大型base64图片数据处理
- ✅ **TypeScript类型安全**: 完善的接口类型定义和错误处理

### HSV色彩空间优化 (v1.1)
- ✅ **颜色识别精度提升**: 采用HSV色彩空间进行K-Means聚类，更符合人眼视觉感知
- ✅ **算法优化**: 同时支持GPU (cuML) 和CPU (sklearn) 的HSV色彩空间处理
- ✅ **Base64图片支持**: 直接处理前端上传的base64编码图片，无需外部URL
- ✅ **图片压缩优化**: 自动调整图片尺寸，提升处理性能和稳定性
- ✅ **错误处理增强**: 完善的异常处理和用户友好的错误信息

### 前端体验改进
- ✅ **React渲染优化**: 修复对象渲染错误，确保色板正确显示
- ✅ **API限制提升**: 支持最大10MB的图片上传
- ✅ **交互式色板**: 点击复制、批量操作、JSON导出功能
- ✅ **响应式设计**: 2-6列自适应色板布局

## 🔮 未来规划

- [ ] **云端部署**: NVIDIA LaunchPad集成
- [ ] **移动端适配**: 响应式设计优化
- [ ] **更多AI模型**: 集成更多NVIDIA NIM服务
- [ ] **批量处理**: 支持多图片同时分析
- [ ] **API扩展**: 更丰富的颜色操作接口
- [ ] **插件系统**: Figma/Sketch插件开发

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 技术支持

- 📧 Email: support@ui-color-bot.com
- 🐛 Issues: [GitHub Issues](https://github.com/your-repo/issues)
- 📖 文档: [用户指南](USER_GUIDE.md)

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给我们一个星标！**

Made with ❤️ by the UI Color Bot Team

</div>

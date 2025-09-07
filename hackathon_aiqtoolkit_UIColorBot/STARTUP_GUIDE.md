# 🚀 项目启动指南

API配置完成后，按照以下步骤启动项目：

## 📋 启动前检查清单

### 1. 安装 uv 包管理器
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
```

### 2. 创建虚拟环境并安装依赖
```bash
# 创建Python虚拟环境
uv venv --seed .venv --python 3.12

# 激活虚拟环境
source .venv/bin/activate

# 安装项目依赖
uv pip install -e .
uv pip install tavily-python
uv pip install python-dotenv
```

### 3. 验证API配置
```bash
python config_loader.py
```

### 4. 启动项目
```bash
# 使用配置文件启动
aiq serve --config_file configs/hackathon_config.yml --host 0.0.0.0 --port 8001
```

## 🔧 常见问题解决

### Python环境问题
- 确保Python版本 >= 3.11, < 3.13
- 使用虚拟环境避免包冲突

### API Key问题
- 检查 `.env` 文件中的API密钥格式
- 确认环境变量正确加载

### 依赖安装问题
- 使用 `uv` 包管理器提高安装速度
- 检查网络连接和代理设置

## 📱 访问地址

启动成功后：
- **API文档**: http://localhost:8001/docs
- **健康检查**: http://localhost:8001/health

## 🧪 测试建议

1. **时间查询**: "现在几点了？"
2. **网络搜索**: "北京今天的天气怎么样？"
3. **对话测试**: "你好，介绍一下你的功能"

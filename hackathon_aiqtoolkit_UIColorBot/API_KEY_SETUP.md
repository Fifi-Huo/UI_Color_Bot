# 百炼API Key 配置指南

## 🔐 安全存放API Key的方法

### 方法1：使用 .env 文件（推荐）

1. **编辑 `.env` 文件**
   ```bash
   # 在项目根目录的 .env 文件中添加你的真实API key
   BAILIAN_API_KEY=sk-your-actual-bailian-api-key-here
   DASHSCOPE_API_KEY=sk-your-actual-dashscope-api-key-here
   ```

2. **获取百炼API Key**
   - 访问 [阿里云百炼平台](https://bailian.console.aliyun.com/)
   - 登录后进入控制台
   - 在API管理页面创建或查看你的API Key

3. **验证配置**
   ```bash
   python config_loader.py
   ```

### 方法2：系统环境变量

在你的 shell 配置文件中添加：

```bash
# ~/.zshrc 或 ~/.bash_profile
export BAILIAN_API_KEY="sk-your-actual-bailian-api-key-here"
export DASHSCOPE_API_KEY="sk-your-actual-dashscope-api-key-here"
```

然后重新加载配置：
```bash
source ~/.zshrc
```

### 方法3：临时环境变量

在运行程序前设置：
```bash
export BAILIAN_API_KEY="sk-your-actual-bailian-api-key-here"
python your_script.py
```

## ⚠️ 安全注意事项

1. **永远不要**将API key直接写在代码中
2. **永远不要**将包含API key的文件提交到Git
3. **使用 .gitignore**确保 `.env` 文件不被跟踪
4. **定期轮换**你的API key
5. **限制API key权限**，只给予必要的访问权限

## 🔍 故障排除

### 常见错误

1. **"未找到环境变量"**
   - 检查 `.env` 文件是否存在
   - 确认环境变量名称拼写正确
   - 验证 `.env` 文件格式（无空格，使用=分隔）

2. **"API key无效"**
   - 确认API key是否正确复制
   - 检查API key是否已激活
   - 验证API key权限设置

3. **"配置加载失败"**
   - 检查YAML文件语法
   - 确认文件路径正确
   - 验证文件编码为UTF-8

### 测试API连接

```python
import os
from config_loader import get_api_key

try:
    api_key = get_api_key("BAILIAN_API_KEY")
    print(f"✅ API Key 配置成功，长度: {len(api_key)}")
except Exception as e:
    print(f"❌ 配置错误: {e}")
```

## 📝 配置文件说明

项目使用以下配置结构：
- `configs/hackathon_config.yml` - 主配置文件
- `.env` - 环境变量文件（本地）
- `config_loader.py` - 配置加载工具

配置文件中的 `${BAILIAN_API_KEY}` 会自动替换为环境变量中的实际值。

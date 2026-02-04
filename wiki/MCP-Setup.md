# MCP Server 配置

MCP (Model Context Protocol) 是 Anthropic 提出的协议，允许 AI 工具返回原生内容（如图片）直接显示在聊天窗口中。

## 为什么使用 MCP？

| 方式 | 图片显示 | 配置复杂度 |
|------|----------|------------|
| HTTP API | 需要 Read 工具读取文件路径 | 简单 |
| **MCP Server** | **原生显示在聊天窗口** | 中等 |

## 配置步骤

### 1. 安装依赖

```bash
# 使用 ComfyUI 的 Python 环境
pip install mcp
```

### 2. 配置 Cursor

在项目根目录创建 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "anima-tool": {
      "command": "<PATH_TO_PYTHON>",
      "args": ["<PATH_TO>/ComfyUI-AnimaTool/servers/mcp_server.py"],
      "env": {
        "COMFYUI_URL": "http://127.0.0.1:8188",
        "COMFYUI_MODELS_DIR": "<PATH_TO>/ComfyUI/models"
      }
    }
  }
}
```

> 说明：`COMFYUI_MODELS_DIR` 指向 **ComfyUI 的 models 根目录**（包含 loras/、checkpoints/ 等子目录）。
> 该变量用于 `list_anima_models(model_type="loras")` 在本地磁盘上查找同名 `.json` sidecar 元数据文件。

### 路径示例

**Windows**：

```json
{
  "mcpServers": {
    "anima-tool": {
      "command": "C:\\ComfyUI\\.venv\\Scripts\\python.exe",
      "args": ["C:\\ComfyUI\\custom_nodes\\ComfyUI-AnimaTool\\servers\\mcp_server.py"],
      "env": {
        "COMFYUI_URL": "http://127.0.0.1:8188",
        "COMFYUI_MODELS_DIR": "C:\\ComfyUI\\models"
      }
    }
  }
}
```

**macOS/Linux**：

```json
{
  "mcpServers": {
    "anima-tool": {
      "command": "/path/to/ComfyUI/.venv/bin/python",
      "args": ["/path/to/ComfyUI/custom_nodes/ComfyUI-AnimaTool/servers/mcp_server.py"]
    }
  }
}
```

### 3. 重启 Cursor

重启 Cursor 以加载 MCP Server 配置。

## 验证配置

### 检查状态

Cursor Settings → MCP → 查看 `anima-tool` 状态

状态说明：
- ✅ Running：正常运行
- ❌ Failed：启动失败，点击查看日志
- ⏳ Starting：正在启动

### 测试生成

在 Cursor 聊天中输入：

> 画一个穿白裙的少女，竖屏 9:16，safe

如果配置正确，图片会直接显示在聊天窗口中。

## 故障排除

### "Connection closed" 错误

1. 确认 `mcp` 库已安装到正确的 Python 环境
2. 检查路径转义（Windows 使用 `\\` 或 `/`）
3. 使用绝对路径

### MCP Server 没加载

1. 检查 Cursor Settings → MCP → anima-tool 状态
2. 点击 "Show Output" 查看日志
3. 确认 Python 路径正确

### 生成失败

1. 确认 ComfyUI 正在运行（`http://127.0.0.1:8188`）
2. 确认 Anima 模型文件存在
3. 检查 ComfyUI 控制台错误

### LoRA 报错："Value not in list: lora_name ..."

这是 ComfyUI 的枚举校验：`LoraLoaderModelOnly.lora_name` 必须与 `GET /models/loras` 返回的字符串 **逐字一致**。

- Windows 下通常是反斜杠路径（例如 `_Anima\cosmic_xxx.safetensors`）
- 如果你在 JSON 里写，需要写成 `_Anima\\cosmic_xxx.safetensors`

PowerShell 一行命令获取 LoRA 列表：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8188/models/loras"
```

### 手动测试

```bash
python /path/to/ComfyUI-AnimaTool/servers/mcp_server.py
```

正常情况下不会有输出（MCP 使用 stdio 通信）。如果有错误会打印到 stderr。

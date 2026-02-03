# Anima Tool MCP Server 配置指南

让 Cursor/Claude 原生显示生成的图片（不需要 Read 工具）。

## 快速配置

### 1. 安装 MCP 依赖

```bash
# 使用 ComfyUI 的 Python 环境
pip install mcp
```

### 2. 配置 Cursor

在你的项目根目录创建 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "anima-tool": {
      "command": "<PATH_TO_PYTHON>",
      "args": ["<PATH_TO>/ComfyUI-AnimaTool/servers/mcp_server.py"]
    }
  }
}
```

**路径说明**：
- `<PATH_TO_PYTHON>`：ComfyUI 使用的 Python 解释器路径
- `<PATH_TO>`：ComfyUI custom_nodes 目录路径

### Windows 示例

```json
{
  "mcpServers": {
    "anima-tool": {
      "command": "C:\\ComfyUI\\.venv\\Scripts\\python.exe",
      "args": ["C:\\ComfyUI\\custom_nodes\\ComfyUI-AnimaTool\\servers\\mcp_server.py"]
    }
  }
}
```

### macOS/Linux 示例

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

## 使用

1. **确保 ComfyUI 运行**（默认 `http://127.0.0.1:8188`）
2. 直接让 AI 生成图片：

> 用 @fkey, @jima 画师风格，画一个穿白裙的少女，竖屏 9:16，safe

图片会**原生显示**在聊天窗口中。

## 验证 MCP Server

### 检查状态

Cursor Settings → MCP → 查看 `anima-tool` 状态

### 手动测试

```bash
# Windows
python "<PATH_TO>/ComfyUI-AnimaTool/servers/mcp_server.py"

# macOS/Linux
python /path/to/ComfyUI/custom_nodes/ComfyUI-AnimaTool/servers/mcp_server.py
```

如果正常启动，不会有任何输出（MCP 使用 stdio 通信）。

## 故障排除

### MCP Server 没加载？

1. 检查 Cursor Settings → MCP → anima-tool 状态
2. 查看输出日志（点击 "Show Output"）
3. 确认 Python 路径正确（使用绝对路径）
4. 确认已安装 `mcp` 库

### "Connection closed" 错误？

1. 确认 `mcp` 库已安装到正确的 Python 环境
2. 检查路径是否使用正确的转义（Windows 使用 `\\\\` 或 `/`）

### 生成失败？

1. 确认 ComfyUI 正在运行
2. 确认 Anima 模型文件存在
3. 检查 ComfyUI 控制台的错误信息

## 高级配置

### 自定义 ComfyUI URL

如果 ComfyUI 运行在非默认端口，修改 `executor/config.py`：

```python
comfyui_url: str = "http://127.0.0.1:YOUR_PORT"
```

### 禁用图片保存

默认会把生成的图片保存到 `outputs/` 目录。如需禁用：

```python
download_images: bool = False
```

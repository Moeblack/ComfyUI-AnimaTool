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

### 环境变量配置（推荐）

无需修改代码，通过环境变量配置：

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `COMFYUI_URL` | `http://127.0.0.1:8188` | ComfyUI 服务地址 |
| `ANIMATOOL_TIMEOUT` | `600` | 生成超时（秒） |
| `ANIMATOOL_DOWNLOAD_IMAGES` | `true` | 是否保存图片到本地 |

### 在 MCP 配置中设置环境变量

```json
{
  "mcpServers": {
    "anima-tool": {
      "command": "C:\\ComfyUI\\.venv\\Scripts\\python.exe",
      "args": ["C:\\ComfyUI\\custom_nodes\\ComfyUI-AnimaTool\\servers\\mcp_server.py"],
      "env": {
        "COMFYUI_URL": "http://192.168.1.100:8188",
        "ANIMATOOL_TIMEOUT": "300"
      }
    }
  }
}
```

### 远程 ComfyUI 配置

如果 ComfyUI 运行在其他机器/Docker：

**局域网**：
```json
"env": { "COMFYUI_URL": "http://192.168.1.100:8188" }
```

**Docker 访问宿主机**：
```json
"env": { "COMFYUI_URL": "http://host.docker.internal:8188" }
```

### 禁用图片保存

```json
"env": { "ANIMATOOL_DOWNLOAD_IMAGES": "false" }
```

---

## 其他客户端支持

### Cherry Studio

Cherry Studio v0.9.0+ 支持 MCP 协议。

#### 方式一：使用 uvx (推荐)

无需在 ComfyUI 环境安装依赖，直接运行：

在 Cherry Studio 设置 -> MCP Servers -> 点击添加：

- **Type**: `stdio`
- **Command**: `uvx`
- **Args** (注意：请分三行填写):
    ```text
    --from
    comfyui-animatool
    animatool-mcp
    ```
- **Environment Variables**:
    - `COMFYUI_URL`: `http://127.0.0.1:8188`

#### 方式二：本地运行 (使用 ComfyUI Python)

- **Type**: `stdio`
- **Command**: `<PATH_TO_PYTHON>` (ComfyUI 的 Python 解释器路径)
- **Args**: `<PATH_TO>/ComfyUI-AnimaTool/servers/mcp_server.py` (填入绝对路径)
- **Environment Variables**:
    - `COMFYUI_URL`: `http://127.0.0.1:8188`

### SillyTavern (酒馆)

需安装 [SillyTavern MCP Client](https://github.com/Moeblack/sillytavern-mcp-client) 扩展。

1. 打开 Extensions -> MCP Client -> Manage Servers
2. 点击 **Add Server (JSON)**
3. 填入以下配置（使用 uvx 示例）：

```json
{
  "id": "animatool",
  "name": "Anima Tool",
  "transport": {
    "type": "stdio",
    "command": "uvx",
    "args": [
      "--from",
      "comfyui-animatool",
      "animatool-mcp"
    ],
    "env": {
      "COMFYUI_URL": "http://127.0.0.1:8188"
    }
  },
  "enabled": true,
  "autoConnect": true
}
```

> 注意：如需使用本地 Python 环境，请将 `command` 改为 python 路径，`args` 改为 `["/path/to/ComfyUI-AnimaTool/servers/mcp_server.py"]`。

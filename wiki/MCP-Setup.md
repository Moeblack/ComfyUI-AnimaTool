# MCP Server 配置

MCP (Model Context Protocol) 是 Anthropic 提出的协议，允许 AI 工具返回原生内容（如图片）直接显示在聊天窗口中。

## 为什么使用 MCP？

| 方式 | 图片显示 | 配置复杂度 |
|------|----------|------------|
| HTTP API | 需要 Read 工具读取文件路径 | 简单 |
| **MCP Server** | **原生显示在聊天窗口** | 中等 |

## 配置步骤

### 方式一：使用 uvx (推荐，无需安装依赖)

直接在 Cursor 配置中使用 `uvx` 拉起最新版客户端（需安装 [uv](https://github.com/astral-sh/uv)）。此方式无需污染 ComfyUI 环境，且自动保持更新。

在项目根目录创建/编辑 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "animatool": {
      "command": "uvx",
      "args": [
        "--from",
        "comfyui-animatool",
        "animatool-mcp"
      ],
      "env": {
        "COMFYUI_URL": "http://127.0.0.1:8188",
        "ANIMATOOL_CHECK_MODELS": "false"
      }
    }
  }
}
```

> 说明：`ANIMATOOL_CHECK_MODELS` 设为 `false` 可跳过本地模型检查（适合远程连接 ComfyUI 的场景）。

### 方式二：直接运行插件内置 Server (开发调试用)

如果你需要修改 server 代码，或者不想安装 uv，可以直接运行插件目录下的脚本。

1. **安装依赖**：
   ```bash
   # 在 ComfyUI 的 python 环境中
   pip install mcp
   ```

2. **配置 Cursor**：

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

#### 路径示例 (方式二)

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

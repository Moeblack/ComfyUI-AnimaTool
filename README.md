# ComfyUI-AnimaTool

<p align="center">
  <img src="assets/hero.webp" alt="ComfyUI-AnimaTool Demo" width="100%">
</p>

<p align="center">
  <b>让 AI Agent 直接生成二次元图片，原生显示在聊天窗口</b>
</p>

<p align="center">
  Cursor / Claude / Gemini / OpenAI → MCP / HTTP API → ComfyUI → Anima 模型
</p>

---

![Screenshot](assets/screenshot.webp)

## Documentation

- [📖 Wiki & Prompt Guide](https://github.com/Moeblack/ComfyUI-AnimaTool/wiki) - 详细的提示词指南、安装教程和 API 文档。
- [🤖 Cursor Skill](CURSOR_SKILL.md) - **Cursor / Windsurf 用户必读**！将此文件内容作为 Agent Skill，让 AI 学会如何写高质量提示词。

## Features

- **MCP Server**：图片原生显示在 Cursor/Claude 聊天窗口
- **HTTP API**：随 ComfyUI 启动，无需额外服务
- **结构化提示词**：按 Anima 规范自动拼接
- **多长宽比支持**：21:9 到 9:21（共 14 种预设）

---

## Installation

### Method 1: ComfyUI Manager (Recommended)

1. 打开 ComfyUI Manager
2. 搜索 "Anima Tool"
3. 点击 Install
4. 重启 ComfyUI

### Method 2: Manual Install

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/Moeblack/ComfyUI-AnimaTool.git
pip install -r ComfyUI-AnimaTool/requirements.txt
```

### Prerequisites

确保以下模型文件已放置到 ComfyUI 对应目录：

| 文件 | 路径 | 说明 |
|------|------|------|
| `anima-preview.safetensors` | `models/diffusion_models/` | Anima UNET |
| `qwen_3_06b_base.safetensors` | `models/text_encoders/` | Qwen3 CLIP |
| `qwen_image_vae.safetensors` | `models/vae/` | VAE |

模型下载：[circlestone-labs/Anima on Hugging Face](https://huggingface.co/circlestone-labs/Anima)

---

## Usage

### 方式 1：MCP Server（推荐，原生图片显示）

#### 配置 Cursor

在项目根目录创建 `.cursor/mcp.json`：

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

**示例（Windows）**：

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

#### 安装 MCP 依赖

```bash
pip install mcp
```

#### 使用

1. 确保 ComfyUI 运行在 `http://127.0.0.1:8188`
2. 重启 Cursor 加载 MCP Server
3. 直接让 AI 生成图片：

> 画一个穿白裙的少女在花园里，竖屏 9:16，safe

图片会**原生显示**在聊天窗口中。

---

### 方式 2：ComfyUI 内置 HTTP API

启动 ComfyUI 后，以下路由自动注册：

| 路由 | 方法 | 说明 |
|------|------|------|
| `/anima/health` | GET | 健康检查 |
| `/anima/schema` | GET | Tool Schema |
| `/anima/knowledge` | GET | 专家知识 |
| `/anima/generate` | POST | 执行生成 |

#### 调用示例

**PowerShell**：

```powershell
$body = @{
    aspect_ratio = "3:4"
    quality_meta_year_safe = "masterpiece, best quality, newest, year 2024, safe"
    count = "1girl"
    artist = "@fkey, @jima"
    tags = "upper body, smile, white dress"
    neg = "worst quality, low quality, blurry, bad hands, nsfw"
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://127.0.0.1:8188/anima/generate" -Method Post -Body $body -ContentType "application/json"
```

**curl**：

```bash
curl -X POST http://127.0.0.1:8188/anima/generate \
  -H "Content-Type: application/json" \
  -d '{"aspect_ratio":"3:4","quality_meta_year_safe":"masterpiece, best quality, newest, year 2024, safe","count":"1girl","artist":"@fkey, @jima","tags":"upper body, smile, white dress","neg":"worst quality, low quality, blurry, bad hands, nsfw"}'
```

---

### 方式 3：独立 FastAPI Server

```bash
cd ComfyUI-AnimaTool
pip install fastapi uvicorn
python -m servers.http_server
```

访问 `http://127.0.0.1:8000/docs` 查看 Swagger UI。

---

## Parameters

### Required

| 参数 | 类型 | 说明 |
|------|------|------|
| `quality_meta_year_safe` | string | 质量/年份/安全标签（必须包含 safe/sensitive/nsfw/explicit） |
| `count` | string | 人数（`1girl`, `2girls`, `1boy`） |
| `artist` | string | 画师，**必须带 `@`**（如 `@fkey, @jima`） |
| `tags` | string | Danbooru 标签 |
| `neg` | string | 负面提示词 |

### Optional

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `aspect_ratio` | string | - | 长宽比（自动计算分辨率） |
| `width` / `height` | int | - | 直接指定分辨率 |
| `character` | string | `""` | 角色名 |
| `series` | string | `""` | 作品名 |
| `appearance` | string | `""` | 外观描述 |
| `style` | string | `""` | 画风 |
| `environment` | string | `""` | 环境/光影 |
| `steps` | int | 25 | 步数 |
| `cfg` | float | 4.5 | CFG |
| `seed` | int | 随机 | 种子 |
| `sampler_name` | string | `er_sde` | 采样器 |

### Supported Aspect Ratios

```
横屏: 21:9, 2:1, 16:9, 16:10, 5:3, 3:2, 4:3
方形: 1:1
竖屏: 3:4, 2:3, 3:5, 10:16, 9:16, 1:2, 9:21
```

---

## Important Rules

1. **画师必须带 `@`**：如 `@fkey, @jima`，否则几乎无效
2. **必须明确安全标签**：`safe` / `sensitive` / `nsfw` / `explicit`
3. **推荐画师组合**：`@fkey, @jima`（效果稳定）
4. **分辨率约 1MP**：Anima preview 版本更稳定
5. **提示词不分行**：单行逗号连接

---

## Directory Structure

```
ComfyUI-AnimaTool/
├── __init__.py           # ComfyUI extension（注册 /anima/* 路由）
├── executor/             # 核心执行器
│   ├── anima_executor.py
│   ├── config.py
│   └── workflow_template.json
├── knowledge/            # 专家知识库
│   ├── anima_expert.md
│   ├── artist_list.md
│   └── prompt_examples.md
├── schemas/              # Tool Schema
│   └── tool_schema_universal.json
├── servers/
│   ├── mcp_server.py     # MCP Server（原生图片返回）
│   ├── http_server.py    # 独立 FastAPI
│   └── cli.py            # 命令行工具
├── assets/               # 截图等资源
├── outputs/              # 生成的图片（gitignore）
├── README.md
├── LICENSE
├── CHANGELOG.md
├── pyproject.toml
└── requirements.txt
```

---

## Configuration

### 环境变量（推荐）

所有配置都可以通过环境变量覆盖，无需修改代码：

#### 基础配置

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `COMFYUI_URL` | `http://127.0.0.1:8188` | ComfyUI 服务地址 |
| `ANIMATOOL_TIMEOUT` | `600` | 生成超时（秒） |
| `ANIMATOOL_DOWNLOAD_IMAGES` | `true` | 是否保存图片到本地 |
| `ANIMATOOL_OUTPUT_DIR` | `./outputs` | 图片输出目录 |
| `ANIMATOOL_TARGET_MP` | `1.0` | 目标像素数（MP） |
| `ANIMATOOL_ROUND_TO` | `16` | 分辨率对齐倍数 |

#### 模型配置

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `COMFYUI_MODELS_DIR` | *(未设置)* | ComfyUI models 目录路径，用于模型预检查 |
| `ANIMATOOL_UNET_NAME` | `anima-preview.safetensors` | UNET 模型文件名 |
| `ANIMATOOL_CLIP_NAME` | `qwen_3_06b_base.safetensors` | CLIP 模型文件名 |
| `ANIMATOOL_VAE_NAME` | `qwen_image_vae.safetensors` | VAE 模型文件名 |
| `ANIMATOOL_CHECK_MODELS` | `true` | 是否启用模型预检查 |

### 在 Cursor MCP 配置中设置环境变量

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

### 模型预检查

设置 `COMFYUI_MODELS_DIR` 后，生成前会自动检查模型文件是否存在：

```json
"env": {
  "COMFYUI_MODELS_DIR": "C:\\ComfyUI\\models"
}
```

如果缺少模型文件，会给出友好提示：

```
缺少以下模型文件：
  - unet: diffusion_models/anima-preview.safetensors
  - clip: text_encoders/qwen_3_06b_base.safetensors

请从 HuggingFace 下载：https://huggingface.co/circlestone-labs/Anima
并放置到 ComfyUI/models/ 对应子目录
```

**远程 ComfyUI 场景**：如果不设置 `COMFYUI_MODELS_DIR`，则跳过预检查（因为无法访问远程文件系统）。

### 远程/Docker ComfyUI 配置

如果 ComfyUI 不在本机运行：

**局域网其他电脑**：
```bash
export COMFYUI_URL=http://192.168.1.100:8188
```

**Docker 容器访问宿主机**：
```bash
export COMFYUI_URL=http://host.docker.internal:8188
```

**WSL 访问 Windows**：
```bash
export COMFYUI_URL=http://$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):8188
```

---

## Troubleshooting

### 错误：无法连接到 ComfyUI

**症状**：`Connection refused` 或 `无法连接到 ComfyUI`

**排查步骤**：
1. 确认 ComfyUI 已启动：浏览器访问 `http://127.0.0.1:8188`
2. 确认端口正确：默认 8188，如果改过需要设置 `COMFYUI_URL`
3. 确认防火墙未阻止（Windows Defender / 企业防火墙）
4. 如果 ComfyUI 在远程/Docker，设置正确的 `COMFYUI_URL`

### 错误：H,W should be divisible by spatial_patch_size

**症状**：`H,W (xxx, xxx) should be divisible by spatial_patch_size 2`

**原因**：分辨率不是 16 的倍数

**解决**：
- 使用预设的 `aspect_ratio`（如 `16:9`、`9:16`、`1:1`）
- 如果手动指定 `width`/`height`，确保是 16 的倍数（如 512、768、1024）

### 错误：模型文件不存在

**症状**：ComfyUI 控制台报 `FileNotFoundError` 或 `Model not found`

**解决**：确认以下文件存在：

| 文件 | 位置 |
|------|------|
| `anima-preview.safetensors` | `ComfyUI/models/diffusion_models/` |
| `qwen_3_06b_base.safetensors` | `ComfyUI/models/text_encoders/` |
| `qwen_image_vae.safetensors` | `ComfyUI/models/vae/` |

下载地址：[circlestone-labs/Anima](https://huggingface.co/circlestone-labs/Anima)

### MCP Server 没加载？

1. **检查状态**：Cursor Settings → MCP → anima-tool 应显示绿色
2. **查看日志**：点击 "Show Output" 查看错误
3. **确认路径**：Python 和脚本路径必须是**绝对路径**
4. **确认依赖**：`pip install mcp`（使用 ComfyUI 的 Python 环境）
5. **重启 Cursor**：修改配置后必须重启

### 生成超时？

**症状**：等待很久后报 `TimeoutError`

**可能原因**：
- ComfyUI 正在加载模型（首次生成较慢）
- GPU 显存不足导致处理缓慢
- 步数 `steps` 设置过高

**解决**：
- 增加超时时间：`export ANIMATOOL_TIMEOUT=1200`
- 降低步数：`steps: 25`（默认值）
- 检查 ComfyUI 控制台是否有错误

### API 调用卡住？

确保使用的是最新版本，旧版本可能存在事件循环阻塞问题。

---

## System Requirements

- **Python**: 3.10+
- **ComfyUI**: 最新版本
- **GPU**: 推荐 8GB+ 显存（Anima 模型较大）
- **依赖**：`mcp`（MCP Server）、`requests`（可选，HTTP 请求）

---

## Credits

- **Anima Model**: [circlestone-labs/Anima](https://huggingface.co/circlestone-labs/Anima)
- **ComfyUI**: [comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)
- **MCP Protocol**: [Anthropic Model Context Protocol](https://github.com/anthropics/anthropic-cookbook/tree/main/misc/model_context_protocol)

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Contributing

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

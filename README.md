# ComfyUI-AnimaTool

> [!NOTE]
> **今日更新**
> - 🎰 **十连抽功能** — 支持 `repeat` / `batch_size`，一次出多张不是梦
> - 🔄 **更换卡池功能** — 可以切换 UNET / CLIP / VAE 模型了，试试新卡池
> - 📋 **寻访记录功能** — 查看历史生成记录，支持 reroll 重新抽卡
>
> ✅ **云端/远程连接更简单** — 新增 `uvx` 免安装模式，一行配置连接远程 ComfyUI，无需本地环境
> ✅ **酒馆 MCP 客户端已发布** — [SillyTavern MCP Client](https://github.com/Moeblack/sillytavern-mcp-client)，支持 stdio + Streamable HTTP 传输
> 
> ✅ **工具调用体验修复** — [Tool Use Fix](https://github.com/Moeblack/sillytavern-tooluse-fix)，合并碎片消息、图片直接显示、Swipe 代理

> [!TIP]
> **Cherry Studio 现已支持 MCP 图片显示！**  
> 我们提交的 PR 已修复 Cherry Studio 对 MCP `ImageContent` 的处理。在官方合并之前，你可以使用预览版体验完整的 MCP 图片功能：  
> **下载预览版** → [Cherry Studio v1.7.17-preview](https://github.com/Moeblack/cherry-studio/releases/tag/v1.7.17-preview)  
> 包含以下修复：
> - 支持按助手单独配置是否将 MCP 工具图片发送给模型
> - 修复 OpenAI 兼容提供商的 base64 图片数据处理
> - 修复 Gemini 的 MCP 多模态工具结果转换
> - **性能修复 v2**：解决多轮出图后严重卡顿问题 — IPC 排除大 slice + base64 就地 strip（修复了 v1.7.16-preview2 中 Zod safeParse 克隆导致 strip 无效的问题）— [上游 PR #12766](https://github.com/CherryHQ/cherry-studio/pull/12766)

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

> **⚠️ 关于 QwenEdit 引擎的特别提醒**
> 本工具现已接入 QwenEdit 模型，支持自然语言对话修图、换装及精准文字生成。请注意：
> 1. **兼容性**：QwenEdit 引擎目前**仅在 Windows 环境下进行过测试**，其他操作系统可能存在未知的路径或环境问题。
> 2. **路径严格要求**：由于 MCP 架构通信限制，使用 QwenEdit 修图时，传入给大模型的原图/参考图路径**必须是完整的本地绝对路径**（例如 `C:\Images\test.png`），不支持相对路径！
> 3. **独立 MCP 包不支持**：目前的独立 PyPI 包版 MCP Server（即 `uvx comfyui-animatool`）暂不支持 QwenEdit 引擎。要使用 QwenEdit，请务必以 `custom_nodes` 方式安装本插件，并使用**本地源码版** `mcp_server.py`。
> 详见 [QwenEdit 指南](https://github.com/Moeblack/ComfyUI-AnimaTool/wiki/QwenEdit-Guide)。

## Features

- **MCP Server**：图片原生显示在 Cursor/Claude 聊天窗口
- **HTTP API**：随 ComfyUI 启动，无需额外服务
- **结构化提示词**：按 Anima 规范自动拼接
- **多长宽比支持**：21:9 到 9:21（共 14 种预设）
- **Reroll / 历史记录**：支持基于历史记录重新生成，可覆盖部分参数（换画师、加 LoRA 等）
- **批量生成**：`repeat` 参数提交多次独立任务（queue 模式），`batch_size` 在单任务内生成多张
- **双引擎支持**：内置传统 Anima 模型（Danbooru 标签）与全新的 QwenEdit 引擎（自然语言、精准文字生成、局部修图）

---

## Related Projects

### SillyTavern 全家桶

在 SillyTavern（酒馆）中使用 AnimaTool 生成图片？推荐安装以下配套插件：

| 项目 | 说明 |
|------|------|
| [SillyTavern MCP Client](https://github.com/Moeblack/sillytavern-mcp-client) | 酒馆 MCP 客户端，连接 AnimaTool 等 MCP Server，支持 stdio + Streamable HTTP |
| [SillyTavern Tool Use Fix](https://github.com/Moeblack/sillytavern-tooluse-fix) | 工具调用体验修复，合并碎片消息、图片直接显示在对话中 |

```
ComfyUI-AnimaTool (本项目，MCP Server)
        ↕ MCP 协议 (stdio / streamable-http)
SillyTavern MCP Client (连接 + 工具注册)
        ↕ SillyTavern Tool Calling
Tool Use Fix (合并显示 + 体验优化)
```

### AnimaLoraToolkit - LoRA 训练工具

如果你想训练自己的 LoRA/LoKr 来搭配 Anima 使用，推荐使用 **[AnimaLoraToolkit](https://github.com/Moeblack/AnimaLoraToolkit)**：

- **YAML 配置文件** - 通过 `--config` 加载，命令行参数可覆盖
- **LoRA / LoKr 双模式** - 标准 LoRA 和 LyCORIS LoKr
- **ComfyUI 兼容** - 输出的 safetensors 可直接在本工具中使用
- **JSON Caption 支持** - 结构化标签，分类 shuffle
- **实时训练监控** - Web 界面显示 loss 曲线和采样图
- **Checkpoint 恢复** - 保存完整训练状态，支持断点续训

训练完成后，将 LoRA 放入 `ComfyUI/models/loras/` 目录，即可通过本工具的 `loras` 参数加载使用。

#### 示例：Cosmic Princess Kaguya LoKr

使用 AnimaLoraToolkit 训练的画风+角色 LoKr，还原 Netflix 动画电影《超时空辉耀姬！》的 4K 剧场版画风：

- **下载**：[Civitai](https://civitai.com/models/2366705)
- **触发词**：`@spacetime kaguya`（画风）、`cosmic princess kaguya`（作品）
- **推荐权重**：0.8 - 1.0

---

## Installation

### Cherry Studio 用户

如果你使用 Cherry Studio 作为 MCP 客户端，需要安装我们的预览版才能正确显示 MCP 返回的图片：

1. 下载 [Cherry Studio v1.7.17-preview](https://github.com/Moeblack/cherry-studio/releases/tag/v1.7.17-preview)（安装版或便携版均可）
2. 安装后按下方「方式 1：MCP Server」配置即可
3. 生成的图片会直接显示在聊天窗口中

> 官方版 Cherry Studio 尚未合并此修复，使用官方版会导致图片显示为 base64 乱码，且多轮出图后会严重卡顿。  
> v1.7.17-preview 基于上游 v1.7.17，修复了出图后内存膨胀和 UI 冻结的问题（[详情](https://github.com/CherryHQ/cherry-studio/pull/12766)）。

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

本插件支持双引擎，请**根据你想要使用的功能**下载对应的模型文件，并放置到 ComfyUI 相应目录：

**1. 使用传统 Anima 引擎 (`generate_anima_image`)**

| 文件 | 路径 | 说明 | 大小 |
|------|------|------|------|
| `anima-preview.safetensors` | `models/diffusion_models/` | Anima UNET | ~3.5GB |
| `qwen_3_06b_base.safetensors` | `models/text_encoders/` | Qwen3 CLIP | ~1.2GB |
| `qwen_image_vae.safetensors` | `models/vae/` | VAE | ~330MB |

**2. 使用 QwenEdit 引擎 (`generate_qwen_image`)**

| 文件 | 路径 | 说明 | 大小 |
|------|------|------|------|
| `Qwen-Rapid-AIO-NSFW-v23.safetensors` | `models/checkpoints/_Qwen/` | Qwen AIO | ~4GB |
| `qwen_3_06b_base.safetensors` | `models/text_encoders/` | Qwen3 CLIP | ~1.2GB |
| `qwen_image_vae.safetensors` | `models/vae/` | VAE | ~330MB |

模型下载：[circlestone-labs/Anima](https://huggingface.co/circlestone-labs/Anima) (Anima) 或对应 Qwen 仓库。

---

## Usage

### 方式 0：独立 MCP（推荐：云端/远程 ComfyUI，或不想装到 custom_nodes）

如果你只想连接一台正在运行的 ComfyUI（本机或云端），并且不想把本仓库放进 `ComfyUI/custom_nodes/`，可以使用独立 PyPI 包 **[`comfyui-animatool`](https://github.com/Moeblack/animatool-mcp)**（安装后使用命令 `animatool-mcp`）（仅通过 ComfyUI 标准 API：`/prompt`、`/history/<id>`、`/view?...` 工作）。

#### 安装

**方式一：使用 uvx (推荐，无需安装)**

无需手动安装 Python 包，直接在 Cursor 配置中使用 `uvx` 运行（需安装 [uv](https://github.com/astral-sh/uv)）：

*(配置见下方 JSON)*

**方式二：使用 pip**

```bash
pip install comfyui-animatool
```

**方式三：源码安装 (开发用)**

```bash
pip install -e ./animatool-mcp
```

#### 配置 Cursor

在项目根目录创建 `.cursor/mcp.json`（以 `uvx` 为例）：

```json
{
  "mcpServers": {
    "anima-tool": {
      "command": "uvx",
      "args": ["--from", "comfyui-animatool", "animatool-mcp"],
      "env": {
        "COMFYUI_URL": "http://127.0.0.1:8188",
        "ANIMATOOL_CHECK_MODELS": "false"
      }
    }
  }
}
```

#### 云端鉴权（可选）

如果云端 ComfyUI 需要鉴权（反代/VPN/网关等），可额外设置：

- `ANIMATOOL_BEARER_TOKEN`
- 或 `ANIMATOOL_HEADERS_JSON`（自定义 Header JSON 字符串）

> 该方式**不依赖**安装本 custom node；只要 `COMFYUI_URL` 可访问即可。
>
> ⚠️ **关于 QwenEdit 引擎**：此 PyPI 独立包版本目前**暂未集成 QwenEdit 工具**。如果你需要使用自然语言修图和换装功能，请使用下方介绍的**方式 1：MCP Server（本地 custom_nodes 源码运行）**。

---

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
| `/anima/generate` | POST | 执行生成（支持 `repeat` 批量） |
| `/anima/history` | GET | 查看最近生成历史 |
| `/anima/reroll` | POST | 基于历史记录重新生成 |

#### 调用示例

**PowerShell**：

```powershell
$body = @{
    aspect_ratio = "3:4"
    quality_meta_year_safe = "masterpiece, best quality, newest, year 2025, safe"
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
  -d '{"aspect_ratio":"3:4","quality_meta_year_safe":"masterpiece, best quality, newest, year 2025, safe","count":"1girl","artist":"@fkey, @jima","tags":"upper body, smile, white dress","neg":"worst quality, low quality, blurry, bad hands, nsfw"}'
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
| `repeat` | int | 1 | 提交几次独立生成任务（queue 模式，每次独立随机 seed）。总张数 = repeat × batch_size |
| `batch_size` | int | 1 | 单次任务内生成几张（latent batch 模式，更吃显存） |
| `loras` | array | `[]` | 可选：追加 LoRA（仅 UNET）。`name` 为 `ComfyUI/models/loras/` 下的相对路径（可含子目录），示例：`[{"name":"_Anima/cosmic_kaguya_lokr_epoch4_comfyui.safetensors","weight":0.8}]` |

### Supported Aspect Ratios

```
横屏: 21:9, 2:1, 16:9, 16:10, 5:3, 3:2, 4:3
方形: 1:1
竖屏: 3:4, 2:3, 3:5, 10:16, 9:16, 1:2, 9:21
```

---

### LoRA（可选）

> 当前版本会在 **UNETLoader → KSampler(model)** 之间链式注入 `LoraLoaderModelOnly`，因此**只对 UNET 生效**（不会改 CLIP）。

#### 1）把 LoRA 放到 ComfyUI 的 loras 目录

你的 LoRA 路径（示例）：

- `G:\\AIGC\\ComfyUICommon\\models\\loras\\_Anima\\cosmic_kaguya_lokr_epoch4_comfyui.safetensors`

对应请求里 `loras[i].name` 应写为（相对 `models/loras/`）：

- 推荐写法：`_Anima/cosmic_kaguya_lokr_epoch4_comfyui.safetensors`

> 说明：ComfyUI 侧实际会校验 `lora_name` 是否在 `GET /models/loras` 的返回列表里。
> - Windows 环境下该列表通常是反斜杠路径（例如 `_Anima\\cosmic_kaguya_lokr_epoch4_comfyui.safetensors`）
> - **本项目会根据 `/models/loras` 返回值自动规范化分隔符**（你用 `/` 或 `\\` 都可以），但如果你直接在 ComfyUI 里手工填 `lora_name`，请务必复制接口返回值。

#### 2）生成时传入 loras 参数

可直接参考本仓库示例：[`examples/requests/generate_with_cosmic_kaguya_lora.json`](examples/requests/generate_with_cosmic_kaguya_lora.json)

```json
{
  "aspect_ratio": "3:4",
  "quality_meta_year_safe": "newest, year 2025, safe",
  "count": "1girl",
  "character": "kaguya",
  "series": "cosmic princess kaguya",
  "artist": "@spacetime kaguya",
  "appearance": "long hair, black hair, purple eyes",
  "tags": "school uniform, smile, standing, looking at viewer",
  "environment": "classroom, window, sunlight",
  "nltags": "A cheerful girl stands by the window.",
  "neg": "worst quality, low quality, blurry, bad hands, nsfw",
  "loras": [
    {
      "name": "_Anima/cosmic_kaguya_lokr_epoch4_comfyui.safetensors",
      "weight": 0.9
    }
  ]
}
```

#### 3）（可选）为 LoRA 写 sidecar 元数据，让 MCP 的 list 工具可见

为了避免把整个 `loras` 目录无差别暴露给 MCP 客户端，本项目在 `list_anima_models(model_type="loras")` 时**强制只返回存在同名 `.json` sidecar 元数据文件的 LoRA**。

- LoRA 文件：`ComfyUI/models/loras/_Anima/cosmic_kaguya_lokr_epoch4_comfyui.safetensors`
- sidecar：`ComfyUI/models/loras/_Anima/cosmic_kaguya_lokr_epoch4_comfyui.safetensors.json`

示例 sidecar 文件可参考：

- [`examples/loras/_Anima/cosmic_kaguya_lokr_epoch4_comfyui.safetensors.json`](examples/loras/_Anima/cosmic_kaguya_lokr_epoch4_comfyui.safetensors.json)

> sidecar JSON 的字段结构完全自定义，本项目只要求其为合法 JSON。

> 注意：要让 MCP 服务端读取该 sidecar，你还需要设置 `COMFYUI_MODELS_DIR` 指向本机的 **models 根目录**（例如 `C:\\ComfyUI\\models`；你的示例则是 `G:\\AIGC\\ComfyUICommon\\models`）。远程 ComfyUI 场景通常无法读取远程文件系统，因此只支持“直接使用 loras 参数”，不支持 list。

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
│   ├── history.py        # 生成历史管理器（内存 + JSONL 持久化）
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
| `COMFYUI_MODELS_DIR` | *(未设置)* | ComfyUI models 目录路径，用于模型预检查；同时也用于 **LoRA sidecar 元数据读取**（`list_anima_models(model_type="loras")`） |
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

AGPL-3.0 License - see [LICENSE](LICENSE) for details.

---

## Contributing

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

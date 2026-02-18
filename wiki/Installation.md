# 安装指南

## 前置要求

- ComfyUI 已安装并可正常运行
- Python 3.10+
- 足够的显存（推荐 8GB+）

## 安装方法

### 方法 1：ComfyUI Manager（推荐）

1. 打开 ComfyUI Manager
2. 搜索 "Anima Tool"
3. 点击 Install
4. 重启 ComfyUI

### 方法 2：手动安装

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/Moeblack/ComfyUI-AnimaTool.git
pip install -r ComfyUI-AnimaTool/requirements.txt
```

## 模型文件

本插件支持双引擎，请**根据你想要使用的工具功能**下载对应的模型文件，并放置到 ComfyUI 的相应目录中：

### 1. 使用传统 Anima 引擎 (`generate_anima_image`)

主要用于二次元 Danbooru 标签生图。需要以下文件：

| 文件 | 路径 | 说明 | 大小 |
|------|------|------|------|
| `anima-preview.safetensors` | `models/diffusion_models/` | Anima UNET | ~3.5GB |
| `qwen_3_06b_base.safetensors` | `models/text_encoders/` | Qwen3 CLIP | ~1.2GB |
| `qwen_image_vae.safetensors` | `models/vae/` | VAE | ~330MB |

### 2. 使用 QwenEdit 引擎 (`generate_qwen_image`)

主要用于自然语言生图、精准文字生成、局部修图与换装。需要以下文件：

| 文件 | 路径 | 说明 | 大小 |
|------|------|------|------|
| `Qwen-Rapid-AIO-NSFW-v23.safetensors` | `models/checkpoints/_Qwen/` | Qwen AIO | ~4GB |
| `qwen_3_06b_base.safetensors` | `models/text_encoders/` | Qwen3 CLIP | ~1.2GB |
| `qwen_image_vae.safetensors` | `models/vae/` | VAE | ~330MB |

*(注：两个引擎共用同一个 CLIP 和 VAE 模型)*

### 下载方式

**方式 1：Hugging Face**

访问 [circlestone-labs/Anima](https://huggingface.co/circlestone-labs/Anima) 下载 Anima 模型，或访问 Qwen 的模型仓库下载 AIO 模型。

**方式 2：命令行**

```bash
# 需要安装 huggingface_hub
pip install huggingface_hub

# 下载模型
huggingface-cli download circlestone-labs/Anima anima-preview.safetensors --local-dir ./
```

## 验证安装

1. 启动 ComfyUI
2. 查看控制台，应该看到：

```
[ComfyUI-AnimaTool] Routes registered: /anima/health, /anima/schema, /anima/knowledge, /anima/generate
```

3. 访问 `http://127.0.0.1:8188/anima/health`，应该返回：

```json
{"status": "ok", "comfyui_url": "http://127.0.0.1:8188", ...}
```

## MCP Server 额外依赖

如果要使用 MCP Server（Cursor 原生图片显示），需要额外安装：

```bash
pip install mcp
```

详细配置见 [MCP Server 配置](MCP-Setup)。

## 故障排除

### 模型加载失败？

1. 确认文件路径正确
2. 确认文件完整（检查文件大小）
3. 确认 ComfyUI 版本支持 Anima 模型

### 路由未注册？

1. 确认 `ComfyUI-AnimaTool` 目录在 `custom_nodes/` 下
2. 检查 Python 导入错误（查看 ComfyUI 启动日志）
3. 确认依赖已安装

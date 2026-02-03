# API 参考

ComfyUI-AnimaTool 提供三种 API 接入方式：

1. **MCP Server** - Cursor/Claude 原生图片显示
2. **ComfyUI HTTP API** - 随 ComfyUI 启动
3. **独立 FastAPI Server** - 可独立部署

## MCP Tool

### generate_anima_image

生成二次元/插画图片。

#### 参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `prompt_hint` | string | 否 | - | 人类可读的需求摘要 |
| `aspect_ratio` | string | 否 | - | 长宽比（会覆盖 width/height） |
| `width` | integer | 否 | - | 宽度 |
| `height` | integer | 否 | - | 高度 |
| `quality_meta_year_safe` | string | **是** | - | 质量/年份/安全标签 |
| `count` | string | **是** | - | 人数 |
| `character` | string | 否 | `""` | 角色名 |
| `series` | string | 否 | `""` | 作品名 |
| `appearance` | string | 否 | `""` | 外观描述 |
| `artist` | string | **是** | - | 画师（必须带 @） |
| `style` | string | 否 | `""` | 画风 |
| `tags` | string | **是** | - | Danbooru 标签 |
| `nltags` | string | 否 | `""` | 自然语言补充 |
| `environment` | string | 否 | `""` | 环境/光影 |
| `neg` | string | **是** | - | 负面提示词 |
| `steps` | integer | 否 | 25 | 步数 |
| `cfg` | number | 否 | 4.5 | CFG |
| `sampler_name` | string | 否 | `er_sde` | 采样器 |
| `seed` | integer | 否 | 随机 | 种子 |

#### 返回

MCP Server 返回：
- `TextContent`: 生成信息（分辨率、提示词等）
- `ImageContent`: 图片（base64 编码）

---

## ComfyUI HTTP API

随 ComfyUI 启动自动注册以下路由。

### GET /anima/health

健康检查。

**响应**：

```json
{
  "status": "ok",
  "comfyui_url": "http://127.0.0.1:8188",
  "tool_root": "/path/to/ComfyUI-AnimaTool"
}
```

### GET /anima/schema

获取 Tool Schema（JSON Schema 格式）。

**响应**：

```json
{
  "name": "generate_anima_image",
  "description": "...",
  "parameters": { ... }
}
```

### GET /anima/knowledge

获取专家知识库。

**响应**：

```json
{
  "anima_expert": "...",
  "artist_list": "...",
  "prompt_examples": "..."
}
```

### POST /anima/generate

执行图片生成。

**请求体**：

```json
{
  "aspect_ratio": "3:4",
  "quality_meta_year_safe": "masterpiece, best quality, newest, year 2024, safe",
  "count": "1girl",
  "artist": "@fkey, @jima",
  "tags": "upper body, smile, white dress",
  "neg": "worst quality, low quality, blurry, bad hands, nsfw"
}
```

**响应**：

```json
{
  "success": true,
  "prompt_id": "uuid-xxx",
  "positive": "masterpiece, best quality, ...",
  "negative": "worst quality, ...",
  "width": 872,
  "height": 1160,
  "images": [
    {
      "filename": "AnimaTool__00001_.png",
      "subfolder": "",
      "type": "output",
      "view_url": "http://127.0.0.1:8188/view?filename=...",
      "saved_path": "/path/to/outputs/AnimaTool__00001_.png",
      "base64": "...",
      "mime_type": "image/png",
      "data_url": "data:image/png;base64,...",
      "markdown": "![AnimaTool__00001_.png](data:image/png;base64,...)"
    }
  ]
}
```

---

## 独立 FastAPI Server

### 启动

```bash
cd ComfyUI-AnimaTool
pip install fastapi uvicorn
python -m servers.http_server
```

默认运行在 `http://127.0.0.1:8000`。

### 路由

| 路由 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 欢迎信息 |
| `/health` | GET | 健康检查 |
| `/schema` | GET | Tool Schema |
| `/knowledge` | GET | 专家知识 |
| `/generate` | POST | 执行生成 |
| `/docs` | GET | Swagger UI |

### Swagger UI

访问 `http://127.0.0.1:8000/docs` 查看交互式 API 文档。

---

## CLI 工具

```bash
cd ComfyUI-AnimaTool
python -m servers.cli --help
```

### 示例

```bash
python -m servers.cli \
  --aspect-ratio "3:4" \
  --quality "masterpiece, best quality, newest, year 2024, safe" \
  --count "1girl" \
  --artist "@fkey, @jima" \
  --tags "upper body, smile, white dress" \
  --neg "worst quality, low quality, blurry"
```

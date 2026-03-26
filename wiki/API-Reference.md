# API 参考

ComfyUI-AnimaTool 提供三种 API 接入方式：

1. **MCP Server** - Cursor/Claude 原生图片显示
2. **ComfyUI HTTP API** - 随 ComfyUI 启动
3. **独立 FastAPI Server** - 可独立部署

## MCP Tools

### generate_anima_image

生成二次元/插画图片。

#### 参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `prompt_hint` | string | 否 | - | 人类可读的需求摘要 |
| `aspect_ratio` | string | 否 | - | 长宽比（如 `16:9`、`9:16`） |
| `width` | integer | 否 | - | 宽度（像素，16 的倍数，会覆盖 aspect_ratio） |
| `height` | integer | 否 | - | 高度（像素，16 的倍数，会覆盖 aspect_ratio） |
| `quality_meta_year_safe` | string | **是** | - | 质量/年份/安全标签（必须含 safe/sensitive/nsfw/explicit） |
| `count` | string | **是** | - | 人数（`1girl`、`2girls`、`1boy`） |
| `character` | string | 否 | `""` | 角色名 |
| `series` | string | 否 | `""` | 作品名 |
| `appearance` | string | 否 | `""` | 外观描述（发色、眼睛等） |
| `artist` | string | **是** | - | 画师（必须带 `@`，如 `@fkey`） |
| `style` | string | 否 | `""` | 画风 |
| `tags` | string | **是** | - | Danbooru 标签（逗号分隔） |
| `nltags` | string | 否 | `""` | 自然语言补充 |
| `environment` | string | 否 | `""` | 环境/光影 |
| `neg` | string | **是** | - | 负面提示词 |
| `steps` | integer | 否 | 25 | 步数 |
| `cfg` | number | 否 | 4.5 | CFG |
| `sampler_name` | string | 否 | `er_sde` | 采样器 |
| `seed` | integer | 否 | 随机 | 种子 |
| `repeat` | integer | 否 | 1 | 提交几次独立生成任务（queue 模式，每次独立随机 seed）。范围 1-16 |
| `batch_size` | integer | 否 | 1 | 单次任务内生成几张（latent batch，更吃显存）。范围 1-4 |
| `loras` | array | 否 | `[]` | 追加 LoRA（仅 UNET）。每项 `{"name": "...", "weight": 1.0}`，name 必须与 `/models/loras` 返回值一致 |

> 总生成张数 = `repeat` × `batch_size`。推荐使用 `repeat`（默认方式，显存友好）。

#### 返回

MCP Server 返回：
- `ImageContent`: 图片（base64 编码，原生显示）
- `TextContent`: 历史记录提示（如 `已保存为历史记录 #12。可用 reroll_anima_image(source="last") 重新生成。`）

---

### list_anima_models

查询 ComfyUI 当前可用的模型文件列表。

#### 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `model_type` | string | **是** | `loras` / `diffusion_models` / `vae` / `text_encoders` |

> 当 `model_type=loras` 时，强制只返回存在同名 `.json` sidecar 元数据文件的 LoRA。

#### 返回

`TextContent`：JSON 格式的模型列表。

---

### list_anima_history

查看最近的图片生成历史记录。

#### 参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `limit` | integer | 否 | 5 | 返回最近几条（1-50） |

#### 返回

`TextContent`：每行一条记录摘要，格式：

```
#12 [2026-02-06 17:30] @fkey | 1girl, white hair, blue eyes | seed:42 | 872x1160
#11 [2026-02-06 17:28] @ciloranko | 2girls, school uniform | seed:78923 | 1024x1024
```

---

### reroll_anima_image

基于历史记录重新生成图片。引用一条历史记录作为基础参数，可选覆盖部分参数。

#### 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `source` | string | **是** | `"last"`（最近一条）或历史 ID（如 `"12"` 或 `"#12"`） |
| *其他* | - | 否 | 所有 `generate_anima_image` 的参数均可作为覆盖项 |

> - `seed` 默认自动随机（出不同画面）。手动指定 seed 可复现相同画面。
> - `repeat` 同样可用，如 `reroll_anima_image(source="last", repeat=3)` 一次出 3 张。

#### 典型用法

| 场景 | 调用 |
|------|------|
| 再 roll 一次 | `reroll_anima_image(source="last")` |
| 再来 3 张 | `reroll_anima_image(source="last", repeat=3)` |
| 换个画师再来 | `reroll_anima_image(source="last", artist="@ciloranko")` |
| 回溯第 3 条记录 | `reroll_anima_image(source="3")` |
| 保持 seed 不变加 LoRA | `reroll_anima_image(source="last", seed=原seed, loras=[...])` |

#### 返回

与 `generate_anima_image` 一致（图片 + 历史记录提示）。

---

### generate_qwen_image

使用 QwenEdit 引擎生成/编辑图片，支持自然语言、0参考文生图、局部修图换装。

#### 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `character_and_action` | string | 【生图必填】角色与主要动作的描述。局部修改时若不改动作请留空。 |
| `appearance_details` | string | 【生图必填】角色的外貌与服装细节。修图时如需强制锚定特征填入此处，否则留空。 |
| `environment_and_lighting`| string | 【生图必填】背景环境、光影描述。修图时若不改背景必须留空。 |
| `style_and_quality` | string | 【全局选填】画质词或整体画风（如 '8k，电影级光影'）。 |
| `edit_actions` | array | 【修图必填】局部修改指令数组。纯生图**必须留空**。 |
| `preserve_constraints`| string | 【修图核心锁】强制防崩坏指令，如 '保持人物脸部特征和背景不变'。 |
| `render_text` | string | 【选填】需要 Qwen 在画面中精准生成的文字。 |
| `base_image` | string | 【选填】底图/原图的**本地绝对路径**（⚠️受MCP限制必须是绝对路径。独立 PyPI 包暂不支持 QwenEdit）。传入后切换为图生图模式（Picture 1）。 |
| `reference_images` | array | 【选填】参考图**本地绝对路径**数组（最多2张）。依次映射为 Picture 2, Picture 3。 |
| `aspect_ratio` | string | 【选填】生图/扩图长宽比（如 '16:9'）。有底图时默认跟随原图比例。 |
| `seed` | integer | 【选填】随机种子。 |
| `repeat` | integer | 【选填】独立任务重复次数，每次随机 seed。 |

#### 返回

MCP Server 返回：
- `ImageContent`: 图片（原生显示）
- `TextContent`: 保存路径与 Qwen 最终发送的指令。

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

执行图片生成。支持 `repeat` 参数一次提交多个独立任务。

**请求体**：

```json
{
  "aspect_ratio": "3:4",
  "quality_meta_year_safe": "masterpiece, best quality, newest, year 2025, safe",
  "count": "1girl",
  "artist": "@fkey, @jima",
  "tags": "upper body, smile, white dress",
  "neg": "worst quality, low quality, blurry, bad hands, nsfw",
  "repeat": 1
}
```

**响应**：

```json
{
  "success": true,
  "prompt_id": "uuid-xxx",
  "positive": "masterpiece, best quality, ...",
  "negative": "worst quality, ...",
  "seed": 1234567890,
  "width": 872,
  "height": 1160,
  "history_id": 12,
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

> `repeat > 1` 时，响应为 `{"success": true, "results": [...]}`，每项结构同上。

### GET /anima/history

查看最近生成历史。

**参数**：`?limit=5`（默认 5，范围 1-50）

**响应**：

```json
{
  "count": 2,
  "records": [
    {
      "id": 12,
      "timestamp": "2026-02-06T17:30:00",
      "params": { "artist": "@fkey", "tags": "...", "..." : "..." },
      "positive_text": "masterpiece, ...",
      "seed": 1234567890,
      "width": 872,
      "height": 1160
    }
  ]
}
```

### POST /anima/reroll

基于历史记录重新生成。

**请求体**：

```json
{
  "source": "last",
  "overrides": {
    "artist": "@ciloranko",
    "repeat": 3
  }
}
```

> `source`：`"last"` 或历史 ID（如 `"12"`）。`overrides` 中的参数会覆盖原始记录。
> seed 不指定则自动随机。

**响应**：与 `/anima/generate` 一致。

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
| `/generate` | POST | 执行生成（支持 repeat） |
| `/history` | GET | 查看生成历史 |
| `/reroll` | POST | 基于历史重新生成 |
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
  --quality "masterpiece, best quality, newest, year 2025, safe" \
  --count "1girl" \
  --artist "@fkey, @jima" \
  --tags "upper body, smile, white dress" \
  --neg "worst quality, low quality, blurry"
```

# Anima 二次元图像生成

使用 Anima 模型（circlestone-labs/Anima）在本地 ComfyUI 生成高质量二次元/插画图片。

## 触发条件

- 用户要求生成二次元/动漫/插画风格图片
- 用户提到 Anima 模型
- 用户要求使用特定画师风格（如 @fkey, @jima）

## 使用方法

**直接调用 MCP 工具** `generate_anima_image`，传入结构化参数。

## 硬性规则

1. **画师必须带 `@` 前缀**（如 `@fkey, @jima`），否则几乎无效
2. **必须明确安全标签**：`safe` / `sensitive` / `nsfw` / `explicit`
3. **推荐画师组合**：`@fkey, @jima`（效果稳定）
4. **标签顺序**：质量 → 人数 → 角色 → 作品 → 画师 → 风格 → 外观 → 标签 → 环境

## 必填参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `quality_meta_year_safe` | 质量/年份/安全 | `"masterpiece, best quality, newest, year 2024, safe"` |
| `count` | 人数 | `"1girl"`, `"2girls"`, `"1boy"` |
| `artist` | 画师（带@） | `"@fkey, @jima"` |
| `tags` | 核心标签 | `"upper body, smile, white dress"` |
| `neg` | 负面提示词 | `"worst quality, low quality, blurry, bad hands, nsfw"` |

## 常用可选参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `aspect_ratio` | 长宽比 | `"16:9"`, `"9:16"`, `"3:4"`, `"1:1"` |
| `character` | 角色名 | `"hatsune miku"` |
| `series` | 作品名 | `"vocaloid"` |
| `appearance` | 外观 | `"long hair, blue eyes"` |
| `environment` | 环境/光影 | `"sunset, backlight"` |
| `steps` | 步数 | `25`（默认） |
| `seed` | 种子 | 不填则随机 |

## 长宽比选项

```
横屏: 21:9, 2:1, 16:9, 16:10, 5:3, 3:2, 4:3
方形: 1:1
竖屏: 3:4, 2:3, 3:5, 10:16, 9:16, 1:2, 9:21
```

## 调用示例

用户："画一个穿白裙的少女在花园里，竖屏"

```json
{
  "aspect_ratio": "3:4",
  "quality_meta_year_safe": "masterpiece, best quality, newest, year 2024, safe",
  "count": "1girl",
  "artist": "@fkey, @jima",
  "tags": "upper body, smile, white dress, garden, flowers, sunlight",
  "environment": "outdoor, natural lighting, bokeh",
  "neg": "worst quality, low quality, blurry, bad hands, bad anatomy, extra fingers, missing fingers, text, watermark, nsfw, explicit"
}
```

## 提示词技巧

- **自然语言最多一句**：用 `nltags` 字段，太长会注意力跑掉
- **构图优先**：1MP 分辨率下确保主体占画面比例足够大
- **手脚易崩**：负面词加 `bad hands, extra fingers, missing fingers, bad feet`
- **兽耳娘防变异**：负面加 `anthro`
- **反咒量大管饱**：负面词要细分，不要只写 `bad anatomy`

## 前置条件

- ComfyUI 运行在 `http://127.0.0.1:8188`
- Anima 模型文件已放置

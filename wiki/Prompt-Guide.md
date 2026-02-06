# 提示词指南

本指南介绍如何为 Anima 模型编写高质量的提示词。

## 硬性规则

1. **画师必须带 `@` 前缀**：如 `@fkey, @jima`，否则几乎无效
2. **必须明确安全标签**：`safe` / `sensitive` / `nsfw` / `explicit`
3. **提示词不分行**：单行逗号连接，分行会影响效果

## 提示词结构

推荐的标签顺序：

```
质量 → 人数 → 角色 → 作品 → 画师 → 风格 → 外观 → 标签 → 环境
```

### 字段说明

| 字段 | 说明 | 示例 |
|------|------|------|
| `quality_meta_year_safe` | 质量、年份、安全标签 | `masterpiece, best quality, newest, year 2024, safe` |
| `count` | 人数 | `1girl`, `2girls`, `1boy`, `no humans` |
| `character` | 角色名 | `hatsune miku`, `serena (pokemon)` |
| `series` | 作品名 | `vocaloid`, `pokemon` |
| `artist` | 画师（必须带 @） | `@fkey, @jima` |
| `style` | 画风 | `anime illustration`, `watercolor` |
| `appearance` | 外观 | `long hair, blue eyes, twintails` |
| `tags` | 核心标签 | `upper body, smile, white dress` |
| `environment` | 环境/光影 | `sunset, backlight, outdoor` |
| `neg` | 负面提示词 | `worst quality, low quality, blurry` |

## 质量标签

### 正面（推荐组合）

```
masterpiece, best quality, highres, newest, year 2024
```

### 负面（基础模板）

```
worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, bad anatomy, bad hands, bad feet, missing fingers, extra fingers, text, watermark, logo
```

## 安全标签

| 标签 | 说明 |
|------|------|
| `safe` | 全年龄向 |
| `sensitive` | 擦边/性感但不露骨 |
| `nsfw` | 成人内容 |
| `explicit` | 明确的成人内容 |

**重要**：必须在 `quality_meta_year_safe` 中明确指定其中一个。

## 画师推荐

### 稳定组合

- `@fkey, @jima` - 效果稳定，色彩明亮

### 热门画师

- `@wlop` - 精致写实风
- `@ciloranko` - 明亮可爱风
- `@ask_(askzy)` - 细腻唯美风
- `@nardack` - 柔和梦幻风

### 画师名格式规则

- 必须以 `@` 开头：`@fkey`，而非 `fkey`
- 名字中间**无下划线**：`@kawakami rokkaku`，而非 `@kawakami_rokkaku`
- 多画师用逗号分隔：`@fkey, @jima`（但稳定性下降，建议最多 1-2 位）
- 如果画师名本身含括号（如 `yd (orange maru)`），需要转义：`@yd \(orange maru\)`
- 不常见的画师可能效果不稳定

## 长宽比

| 类型 | 比例 | 适用场景 |
|------|------|----------|
| 横屏 | 21:9, 2:1, 16:9, 16:10, 5:3, 3:2, 4:3 | 风景、场景 |
| 方形 | 1:1 | 头像、图标 |
| 竖屏 | 3:4, 2:3, 3:5, 10:16, 9:16, 1:2, 9:21 | 人物立绘、手机壁纸 |

## 示例

### 基础示例

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

### 角色示例

```json
{
  "aspect_ratio": "9:16",
  "quality_meta_year_safe": "masterpiece, best quality, highres, newest, year 2024, safe",
  "count": "1girl",
  "character": "hatsune miku",
  "series": "vocaloid",
  "appearance": "long twintails, aqua hair, aqua eyes",
  "artist": "@fkey, @jima",
  "style": "anime illustration, cinematic lighting",
  "tags": "full body, stage, concert, singing, microphone, spotlight",
  "environment": "night, neon, crowd silhouette, bokeh",
  "neg": "worst quality, low quality, blurry, bad anatomy, bad hands, extra fingers, text, watermark, nsfw"
}
```

### 场景示例

```json
{
  "aspect_ratio": "16:9",
  "quality_meta_year_safe": "masterpiece, best quality, newest, year 2024, safe",
  "count": "no humans",
  "artist": "@fkey",
  "style": "anime background, scenic",
  "tags": "landscape, mountain, lake, reflection, clouds",
  "environment": "sunset, golden hour, dramatic lighting",
  "neg": "worst quality, low quality, blurry, text, watermark"
}
```

## LoRA（可选）

如果需要加载 LoRA，使用 `loras` 数组：

- `name`：LoRA 名称（可包含子目录）
- `weight`：LoRA 权重（默认 1.0，UNET-only）

### 技术细节

- LoRA 仅作用于 UNET（不影响 CLIP），在 UNETLoader → KSampler 之间链式注入 `LoraLoaderModelOnly`
- **`name` 必须与 `list_anima_models(model_type=loras)` 或 ComfyUI `GET /models/loras` 返回值逐字一致**，否则触发 ComfyUI 校验错误
- `list_anima_models(model_type=loras)` 仅返回存在同名 `.json` sidecar 元数据文件的 LoRA（强制要求）
- Windows 下 `/models/loras` 通常返回反斜杠路径（如 `_Anima\xxx.safetensors`），在 JSON 中写作 `_Anima\\xxx.safetensors`
- 本工具会自动规范化路径分隔符（`/` 或 `\` 都可以）
- 远程 ComfyUI 场景下 list 功能不可用（无法读取远程文件系统），但可直接传 `loras` 参数

一行命令获取 LoRA 列表（PowerShell）：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8188/models/loras"
```

示例：

```json
{
  "aspect_ratio": "3:4",
  "quality_meta_year_safe": "masterpiece, best quality, newest, year 2024, safe",
  "count": "1girl",
  "artist": "@fkey",
  "tags": "full body, fantasy outfit, glowing",
  "loras": [
    {
      "name": "_Anima\\cosmic_kaguya_lokr_epoch4_comfyui.safetensors",
      "weight": 0.9
    }
  ],
  "neg": "worst quality, low quality, blurry, bad anatomy, bad hands, extra fingers, missing fingers, text, watermark, logo, nsfw"
}
```

## 常见问题

### 手脚崩坏？

负面词加：
```
bad hands, extra fingers, missing fingers, bad feet, extra limbs
```

### 兽耳娘变异？

负面词加：
```
anthro, furry
```

### 构图不对？

- 使用 `upper body`、`full body`、`portrait` 等明确构图
- 1MP 分辨率下确保主体占画面比例足够大

### 画风不稳定？

- 使用推荐的画师组合
- 避免使用过于小众的画师
- 可以添加 `style` 字段辅助

---

## Reroll 与批量生成

### 重新生成（Reroll）

每次生成后会自动记录参数。可以基于历史重新生成：

- `reroll_anima_image(source="last")` — 相同参数，新随机 seed
- `reroll_anima_image(source="last", artist="@ciloranko")` — 换画师
- `reroll_anima_image(source="12")` — 回溯第 12 条记录
- `list_anima_history()` — 查看最近的生成记录

### 批量生成

- **`repeat`**（推荐）：提交 N 次独立任务，每次随机 seed，显存与单张相同
- **`batch_size`**：单次任务内 latent batch，速度快但更吃显存
- 总张数 = `repeat` × `batch_size`

```json
{
  "repeat": 3,
  "aspect_ratio": "3:4",
  "quality_meta_year_safe": "masterpiece, best quality, newest, year 2024, safe",
  "count": "1girl",
  "artist": "@fkey",
  "tags": "upper body, smile",
  "neg": "worst quality, low quality, blurry"
}
```

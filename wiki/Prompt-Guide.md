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

### 使用技巧

- 可以组合多个画师：`@fkey, @jima`
- 画师名必须带 `@` 前缀
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

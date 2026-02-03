# Prompt JSON 示例

> 这些示例可直接用于工具调用（HTTP/CLI/Function Calling）。

## 1) 竖构图 9:16（约 1MP），人物半身

```json
{
  "aspect_ratio": "9:16",
  "quality_meta_year_safe": "masterpiece, best quality, highres, newest, year 2024, safe",
  "count": "1girl",
  "character": "hatsune miku",
  "series": "vocaloid",
  "appearance": "long twintails, aqua hair, aqua eyes, petite",
  "artist": "@fkey, @jima",
  "style": "anime illustration, cinematic lighting, high contrast",
  "tags": "upper body, looking at viewer, smile, stage, holding guitar, spotlight, bokeh",
  "environment": "night, neon, rim light, depth of field",
  "neg": "worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, bad anatomy, bad hands, bad feet, missing fingers, extra fingers, text, watermark, logo, nsfw, explicit"
}
```

## 2) 横构图 16:10（约 1MP），全身动态

```json
{
  "aspect_ratio": "16:10",
  "quality_meta_year_safe": "best quality, highres, newest, year 2024, safe",
  "count": "1girl",
  "character": "",
  "series": "",
  "appearance": "short hair, brown hair, red eyes, small breasts",
  "artist": "@toridamono",
  "style": "clean lineart, vibrant colors",
  "tags": "full body, dynamic pose, running, wind, motion blur, dramatic angle",
  "environment": "sunset, backlight, dust particles",
  "neg": "worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, bad anatomy, bad hands, bad feet, extra fingers, missing fingers, text, watermark, logo, nsfw, explicit"
}
```

## 3) 超宽 21:9（约 1MP），风景+小人

```json
{
  "aspect_ratio": "21:9",
  "quality_meta_year_safe": "good quality, highres, newest, year 2024, safe",
  "count": "1girl",
  "character": "",
  "series": "",
  "appearance": "long hair, white dress",
  "artist": "@guweiz",
  "style": "painterly, atmospheric perspective",
  "tags": "wide shot, small figure, landscape, mountains, river, clouds",
  "environment": "golden hour, volumetric light, haze",
  "neg": "worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, bad anatomy, bad hands, bad feet, extra fingers, missing fingers, text, watermark, logo, nsfw, explicit"
}
```

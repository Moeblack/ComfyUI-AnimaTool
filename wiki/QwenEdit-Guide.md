# QwenEdit 工具使用指南

Qwenedit（基于 qwen-image-edit 衍生模型）为 ComfyUI-AnimaTool 带来了强大的自然语言和视觉理解能力，支持**“0参考文生图”**以及**“极致约束的多重图片编辑”**（换装、换背景、添加文字等）。

> **⚠️ 重要提醒**：
> 1. **兼容性**：QwenEdit 引擎目前**仅在 Windows 环境下进行过测试**，其他操作系统可能存在未知的路径或环境问题。
> 2. **路径严格要求**：由于 MCP 架构与 ComfyUI 跨进程/跨环境通信的限制，修图时传入的所有图片路径（`base_image` 和 `reference_images`）**必须是完整的本地绝对路径**（例如 `C:\Images\test.png`），绝对不支持相对路径！
> 3. **独立 MCP 包不支持**：目前的独立 PyPI 包版 MCP Server（`uvx comfyui-animatool` 或全局安装版）暂不支持 QwenEdit 引擎。请务必使用 `custom_nodes` 源码方式安装并运行本地 `mcp_server.py`。

## 1. 核心定位与原则

QwenEdit 模型使用**简单直接的自然语言指令**作为提示词格式，不需要复杂的模板结构或词缀堆砌（与传统 Stable Diffusion / Danbooru 标签体系完全不同）。

- **直白指令**：如 `"Change her shirt to pink"`, `"Convert into professional technical sketch"`。
- **简短明确**：避免过度详细的描述，指令越短越好。
- **语言支持**：支持中英文指令（中文也可直接识别，如 `"把背景换成雪山"`）。

---

## 2. 模式切换与智能填表哲学

当你通过 MCP 调用 `generate_qwen_image` 或对应的 HTTP API 时，系统会根据填入的参数自动切换模式：

### 模式 A：纯文生图 (0参考原创)
- **适用场景**：从零开始生成全新图片。
- **填表要求**：
  - `character_and_action`: 【必填】角色与主要动作的描述。
  - `appearance_details`: 【必填】角色的外貌与服装细节。
  - `environment_and_lighting`: 【必填】背景环境、光影描述。
  - `edit_actions`: **【必须留空！】**
  - `base_image`: **【必须留空！】**

### 模式 B：局部修图 / 多重图片编辑 (有原图或参考图)
- **适用场景**：对之前生成的本地图片进行修改、换装、换背景、添加文字等。
- **填表要求**：
  - `base_image`: 【必填】填入本地原图的**绝对路径**（如前一轮 AI 生成后保存的路径，必须是绝对路径！）。**传入后，原图将被底层引擎标记为 `Picture 1`。**
  - `edit_actions`: 【必填】局部修改指令数组。**必须使用 'Picture 1' 来代指原图！**（例：`["Change the shirt in Picture 1 to pink", "Remove the passerby in the background of Picture 1"]`）。
  - `preserve_constraints`: 【强烈建议填写】强制防崩坏指令！（例：`"Keep the face and background in Picture 1 completely unchanged"`）。
  - `reference_images`: 【选填】如果你想把 `Picture 1` 的某处替换成另一张图的样子，填入参考图**绝对路径**。**传入后，它们会依次变为 `Picture 2`、`Picture 3`。**（例指令：`["Change the face in Picture 1 to match the face in Picture 2"]`）。
  - `character_and_action`, `environment_and_lighting`: 如果不需要修改动作和背景，**必须留空**！
  - `appearance_details`: 仅在修图时如果你不希望特定身材（如贫乳）被归一化，请填入此处强制锚定原有特征。否则留空。

---

## 3. 提示词最佳实践与速查手册

### 3.1 最佳实践技巧
- **不要堆砌词缀**：与其写 `girl, smile, blue dress`，不如写 `Make the girl smile and wear a blue dress`。
- **保持其他元素不变**：在 `preserve_constraints` 添加 `"Keep everything else unchanged"` 可以防止意外修改。
- **锁定身份特征**：使用 `"Preserve face/clothing features"` 保持人物特征。
- **使用负面提示词**（如有配置）：负面词依然有效，如 `"no distortion, no warped text, no duplicate faces"`。
- **分步编辑**：对于复杂的修改（例如同时要换背景、换衣服、加帽子），模型容易顾此失彼。建议**链式进行 2-3 个较小的编辑**，分多轮对话完成，每次拿着上一轮的 `base_image` 继续修图。

### 3.2 常用功能指令速查

| 功能场景 | 关键动词 (Action Verbs) | 提示词模板示例 (需放入 `edit_actions` 数组中) |
| :--- | :--- | :--- |
| **物体替换** | **Change / Swap / Replace** | `Change the dog in Picture 1 into a cat` (把图1的狗换成猫) |
| **物体添加** | **Add / Insert** | `Add a pair of glasses on the man's face in Picture 1` (在图1男人脸上加副眼镜) |
| **物体移除** | **Remove / Delete** | `Remove the passerby in the background of Picture 1` (移除图1背景中的路人) |
| **属性修改** | **Make / Turn** | `Make the sky in Picture 1 blue and sunny` (让图1天空变蓝放晴) |
| **细节修复** | **Fix / Refine** | `Fix the fingers in Picture 1 to make them look natural` (修复图1手指使其自然) |

---

## 4. 特殊场景：精准文字生成 (Text Rendering)

Qwen 系列的一大强项是中文/英文文字生成。如果需要在画面中写字：
- 直接使用工具参数 `render_text`: （例：`"阿里巴巴"`）。**后台会自动加引号并注入提示词**。
- 在提示词/编辑指令配合指明位置：`["Place a wooden sign board on the grass in Picture 1 with the text"]`，Qwen 会自动将参数中的文字渲染在牌子上。

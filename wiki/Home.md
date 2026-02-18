# ComfyUI-AnimaTool Wiki

欢迎来到 ComfyUI-AnimaTool 的 Wiki！

## 简介

ComfyUI-AnimaTool 是一个让 AI Agent（Cursor / Claude / Gemini / OpenAI）通过 MCP / HTTP API 直接调用 ComfyUI 生成二次元图片的工具。

### 主要特点

- **MCP Server**：图片原生显示在 Cursor/Claude 聊天窗口
- **HTTP API**：随 ComfyUI 启动，无需额外服务
- **结构化提示词**：按 Anima 规范自动拼接
- **多长宽比支持**：21:9 到 9:21（共 14 种预设）
- **Reroll / 历史记录**：基于历史记录重新生成，支持覆盖部分参数
- **批量生成**：`repeat`（多次独立 queue）和 `batch_size`（单任务多张）
- **双引擎支持**：支持传统 Anima 模型（Danbooru 标签）与全新的 QwenEdit 引擎（自然语言、精准文字生成、局部修图）。
- **AI 技能库 (Skills)**：内置 `.md` 技能库，支持支持 Skill 的 AI 客户端直接加载。

## 快速开始

1. [安装指南](Installation)
2. [MCP Server 配置](MCP-Setup)
3. [提示词指南](Prompt-Guide)
4. [QwenEdit 指南](QwenEdit-Guide)
5. [API 参考](API-Reference)
6. [常见问题](FAQ)

## 使用的模型

本工具基于 [circlestone-labs/Anima](https://huggingface.co/circlestone-labs/Anima) 模型：

- 2B 参数，专注于二次元/插画生成
- 使用 Qwen3 作为文本编码器
- 支持 `@artist` 画师风格标签
- 支持 Danbooru 标签系统

**新增支持模型：[QwenEdit](https://huggingface.co/Qwen)**

- 极简自然语言指令，无需复杂词缀。
- 支持 **0参考文生图** 以及 **多参考局部修图/换装**。
- 强大的 **精准中英文文字生成** 能力。

## AI 技能库 (Skills)

本仓库在 `skills/` 目录下内置了专为 AI Agent 编写的技能说明文档。如果你使用的 AI 聊天客户端（如 Cursor、Cline 等）支持导入 Skill / 规则库，可以直接导入这些文件，这将极大提升 AI 使用本工具的准确率：

- `skills/how-to-use-animatool.md` - 指导 AI 如何根据 Danbooru 标签规范使用 `generate_anima_image`。
- `skills/how-to-use-qwenedit.md` - 指导 AI 如何使用自然语言指令和视觉映射调用 `generate_qwen_image` 修图。

## 链接

- [GitHub 仓库](https://github.com/Moeblack/ComfyUI-AnimaTool)
- [Anima 模型](https://huggingface.co/circlestone-labs/Anima)
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI)

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

## 快速开始

1. [安装指南](Installation)
2. [MCP Server 配置](MCP-Setup)
3. [提示词指南](Prompt-Guide)
4. [API 参考](API-Reference)
5. [常见问题](FAQ)

## 使用的模型

本工具基于 [circlestone-labs/Anima](https://huggingface.co/circlestone-labs/Anima) 模型：

- 2B 参数，专注于二次元/插画生成
- 使用 Qwen3 作为文本编码器
- 支持 `@artist` 画师风格标签
- 支持 Danbooru 标签系统

## 链接

- [GitHub 仓库](https://github.com/Moeblack/ComfyUI-AnimaTool)
- [Anima 模型](https://huggingface.co/circlestone-labs/Anima)
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI)

# 常见问题 (FAQ)

## 安装问题

### Q: ComfyUI 启动后没有看到路由注册日志？

**A**: 检查以下几点：

1. 确认 `ComfyUI-AnimaTool` 目录在 `custom_nodes/` 下
2. 查看 ComfyUI 启动日志是否有导入错误
3. 确认依赖已安装：`pip install -r requirements.txt`

### Q: 模型文件放在哪里？

**A**: 

| 文件 | 路径 |
|------|------|
| `anima-preview.safetensors` | `ComfyUI/models/diffusion_models/` |
| `qwen_3_06b_base.safetensors` | `ComfyUI/models/text_encoders/` |
| `qwen_image_vae.safetensors` | `ComfyUI/models/vae/` |

### Q: 显存不够怎么办？

**A**: Anima 模型需要约 6-8GB 显存。可以尝试：

1. 使用更小的分辨率
2. 关闭其他占用显存的程序
3. 使用 `--lowvram` 参数启动 ComfyUI

---

## MCP Server 问题

### Q: Cursor 显示 "Connection closed"？

**A**: 

1. 确认 `mcp` 库已安装到正确的 Python 环境
2. 检查 `.cursor/mcp.json` 中的路径是否正确
3. Windows 路径使用 `\\` 或 `/`

### Q: MCP Server 状态一直是 "Starting"？

**A**: 

1. 检查 Python 路径是否正确
2. 点击 "Show Output" 查看错误日志
3. 手动运行 `python mcp_server.py` 测试

### Q: 图片没有显示在聊天窗口？

**A**: 

1. 确认 MCP Server 状态为 "Running"
2. 确认 ComfyUI 正在运行
3. 检查 ComfyUI 控制台是否有错误

---

## 生成问题

### Q: 生成失败，提示 "timeout"？

**A**: 

1. 确认 ComfyUI 正在运行（`http://127.0.0.1:8188`）
2. 检查 ComfyUI 控制台的错误信息
3. 可能是显存不足导致的

### Q: 画师风格没有效果？

**A**: 

画师名**必须**带 `@` 前缀：

- ✅ `@fkey, @jima`
- ❌ `fkey, jima`

### Q: 生成的图片质量不好？

**A**: 

1. 使用推荐的质量标签：`masterpiece, best quality, highres, newest, year 2024`
2. 负面词要详细：`worst quality, low quality, blurry, bad anatomy, bad hands...`
3. 使用推荐的画师组合：`@fkey, @jima`

### Q: 手脚经常崩坏？

**A**: 

负面词加入：

```
bad hands, extra fingers, missing fingers, bad feet, extra limbs, bad anatomy
```

### Q: 如何固定种子复现结果？

**A**: 

在参数中指定 `seed`：

```json
{
  "seed": 12345,
  ...
}
```

---

## API 问题

### Q: HTTP API 调用卡住不返回？

**A**: 

确保使用最新版本。旧版本可能存在事件循环阻塞问题。

### Q: 如何修改 ComfyUI 地址？

**A**: 

修改 `executor/config.py`：

```python
comfyui_url: str = "http://YOUR_HOST:YOUR_PORT"
```

### Q: 如何禁用图片本地保存？

**A**: 

修改 `executor/config.py`：

```python
download_images: bool = False
```

---

## 其他问题

### Q: 支持哪些采样器？

**A**: 

ComfyUI 支持的所有采样器都可以使用。推荐：

- `er_sde`（默认，效果稳定）
- `euler_ancestral`
- `dpmpp_2m_sde`

### Q: 支持批量生成吗？

**A**: 

支持两种方式：

1. **`repeat` 参数**（推荐）：提交多次独立生成任务（queue 模式），每次独立随机 seed，显存占用与单张相同。例如 `repeat: 3` 会提交 3 次独立生成。
2. **`batch_size` 参数**：单次任务内生成多张（latent batch 模式），共享参数，速度更快但更吃显存。

总张数 = `repeat` × `batch_size`。

### Q: 如何重新生成上一张图？

**A**: 

使用 `reroll_anima_image` 工具：

- **再 roll 一次**：`reroll_anima_image(source="last")`
- **再来 3 张**：`reroll_anima_image(source="last", repeat=3)`
- **换个画师**：`reroll_anima_image(source="last", artist="@ciloranko")`
- **回溯历史**：先用 `list_anima_history` 查看记录，再用 `reroll_anima_image(source="12")` 指定 ID

每次生成后会自动返回历史记录 ID，方便后续引用。

### Q: 可以自定义工作流吗？

**A**: 

可以修改 `executor/workflow_template.json`，但需要保持输入输出接口兼容。

---

## 还有问题？

请在 [GitHub Issues](https://github.com/Moeblack/ComfyUI-AnimaTool/issues) 提交问题。

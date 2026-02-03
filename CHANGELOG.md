# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-03

### Added

- Initial release
- **MCP Server**: Native image display in Cursor/Claude chat window
- **ComfyUI HTTP API**: Routes `/anima/health`, `/anima/schema`, `/anima/knowledge`, `/anima/generate`
- **Standalone HTTP Server**: FastAPI-based server for external integrations
- **CLI Tool**: Command-line interface for batch generation
- **Structured Prompt System**: Quality/Artist/Character/Tags/Environment fields
- **Aspect Ratio Support**: 14 presets from 21:9 to 9:21, auto-calculates ~1MP resolution
- **Expert Knowledge Base**: Anima prompting guidelines, artist list, examples

### Technical Details

- Uses `circlestone-labs/Anima` model (2B params, anime/illustration focused)
- Requires Qwen3 tokenizer (`qwen_3_06b_base.safetensors`) and VAE (`qwen_image_vae.safetensors`)
- Artist tags must use `@` prefix (e.g., `@fkey, @jima`)
- Safety labels required: `safe`, `sensitive`, `nsfw`, `explicit`

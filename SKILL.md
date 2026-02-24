---
name: nova-ai-automation
description: |
  Nova AI 播客自动化工具包 - 将 YouTube 翻译文档自动转为播客音频。
  
  功能：
  1. YouTube 翻译转播客 - 自动将 YouTube 翻译文档转为播客音频
  2. RSS Feed 生成 - 管理播客 RSS Feed
  
  触发关键词：播客自动化、YouTube转播客、podcast、RSS
---

# Nova AI 播客自动化工具包

## 功能概览

| 脚本 | 功能 | 说明 |
|------|------|------|
| `youtube_to_podcast.py` | YouTube 翻译转播客 | 翻译文档 → AI脚本 → TTS音频 → GitHub |
| `podcast_github_rss.py` | RSS Feed 生成 | 管理播客 RSS Feed，发布到 GitHub Pages |

## 快速使用

### YouTube 翻译转播客
```bash
cd /workspace/skills/nova-ai-automation
python scripts/youtube_to_podcast.py
```

流程：
1. 从 `youtube-translations` 仓库读取翻译文档
2. AI 生成播客脚本（纯文本，适合 TTS）
3. Edge TTS 生成音频（微软云希男声）
4. 上传到 GitHub `NovaAI-Podcast` 仓库
5. 更新 RSS Feed

### 手动指定脚本生成音频
```bash
python scripts/youtube_to_podcast.py \
  --script-file /path/to/script.txt \
  --title "播客标题" \
  --description "播客描述"
```

### RSS Feed 管理
```bash
# 发布新单集
python scripts/podcast_github_rss.py publish "标题" "简介" ./audio.mp3

# 仅推送更新
python scripts/podcast_github_rss.py push
```

## 配置说明

### 播客配置
- GitHub 仓库：`NovaAI-Podcast`
- RSS Feed：`https://ychenjk-sudo.github.io/NovaAI-Podcast/feed.xml`
- TTS 模型：Edge TTS `zh-CN-YunxiNeural`（微软云希男声，免费）

### 翻译源
- YouTube 翻译仓库：`ychenjk-sudo/youtube-translations`

## 依赖安装
```bash
pip install edge-tts requests
```

## 文件结构
```
nova-ai-automation/
├── SKILL.md
└── scripts/
    ├── youtube_to_podcast.py    # YouTube 翻译转播客主流程
    └── podcast_github_rss.py    # RSS Feed 生成器
```

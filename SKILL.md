---
name: nova-ai-automation
description: |
  Nova AI 自动化工具包 - 包含 AI 新闻聚合推送和播客自动生成功能。
  
  功能：
  1. BestBlogs AI 新闻精选 - 每日抓取高分 AI 文章推送到飞书
  2. AK 博客精选 - Karpathy 推荐的 92 个 HN 热门博客，推送+写入飞书文档
  3. YouTube 翻译转播客 - 自动将 YouTube 翻译文档转为播客音频
  
  触发关键词：AI新闻、播客自动化、BestBlogs、AK博客、YouTube转播客
---

# Nova AI 自动化工具包

## 功能概览

| 功能 | 说明 | 触发命令 |
|------|------|----------|
| BestBlogs 推送 | AI领域85分+文章推送飞书 | `python scripts/bestblogs_feishu.py` |
| AK 博客推送 | Karpathy 推荐博客推送飞书 | `python scripts/ak_blogs_feishu.py` |
| AK 博客文档 | 写入飞书文档（含翻译摘要） | `python scripts/ak_blogs_to_feishu_doc.py` |
| YouTube 转播客 | 翻译文档转音频上传 GitHub | `python scripts/youtube_to_podcast.py` |

## 快速使用

### 1. BestBlogs AI 新闻推送
```bash
cd /workspace/skills/nova-ai-automation
python scripts/bestblogs_feishu.py
```
- 抓取 BestBlogs 85 分以上的 AI 文章
- 格式化后推送到飞书

### 2. AK 博客精选
```bash
python scripts/ak_blogs_feishu.py      # 推送到飞书
python scripts/ak_blogs_to_feishu_doc.py  # 写入飞书文档
```
- 抓取 Karpathy 推荐的 92 个 HN 热门博客
- 生成核心观点摘要 + 中文翻译
- 写入固定飞书文档顶部

### 3. YouTube 翻译转播客
```bash
python scripts/youtube_to_podcast.py
```
- 从 `youtube-translations` 仓库读取翻译文档
- AI 生成播客脚本
- Edge TTS 生成音频
- 上传到 GitHub `NovaAI-Podcast` 仓库
- 更新 RSS Feed

## 配置说明

### 飞书推送目标
修改脚本中的 `ou_xxx` 为目标用户的 open_id

### 播客配置
- GitHub 仓库：`NovaAI-Podcast`
- RSS Feed：`https://ychenjk-sudo.github.io/NovaAI-Podcast/feed.xml`
- TTS 模型：Edge TTS `zh-CN-YunxiNeural`

### 定时任务（已配置）
- BestBlogs 推送：每天 9:00
- AK 博客文档：每天 18:00

## 依赖安装
```bash
pip install feedparser edge-tts requests
```

## 文件结构
```
nova-ai-automation/
├── SKILL.md
├── scripts/
│   ├── bestblogs_feishu.py      # BestBlogs 推送
│   ├── ak_blogs_feishu.py       # AK 博客推送
│   ├── ak_blogs_to_feishu_doc.py # AK 博客文档
│   ├── youtube_to_podcast.py    # YouTube 转播客
│   └── podcast_github_rss.py    # RSS 生成器
└── references/
    └── rss_sources.md           # RSS 源列表
```

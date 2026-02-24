#!/usr/bin/env python3
"""
YouTube 翻译 → 播客 自动化流水线

流程：
1. 从 youtube-translations 仓库读取翻译文档
2. AI 生成播客脚本（对话体）
3. TTS 生成音频
4. 上传到 lixiang-podcast 仓库
5. 更新 RSS Feed
"""

import os
import re
import json
import subprocess
from datetime import datetime
from pathlib import Path

# ============ 配置 ============

# 仓库路径
TRANSLATIONS_REPO = "/tmp/yt-trans"
PODCAST_REPO = "/workspace/NovaAI-Podcast"

# 播客配置
PODCAST_CONFIG = {
    "title": "AI前沿解读",
    "description": "每期精选一个 YouTube 深度访谈，用中文为你解读 AI 领域最前沿的思想和实践。",
    "author": "理想",
    "email": "podcast@example.com",
    "language": "zh-cn",
    "category": "Technology",
}

# 已处理的文档记录
PROCESSED_FILE = f"{PODCAST_REPO}/processed.json"

# ============ 核心函数 ============

def load_processed():
    """加载已处理的文档列表"""
    try:
        with open(PROCESSED_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"processed": []}

def save_processed(data):
    """保存已处理列表"""
    with open(PROCESSED_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_translation_files():
    """获取所有翻译文档"""
    files = []
    for f in Path(TRANSLATIONS_REPO).glob("*.md"):
        if f.name != "README.md":
            files.append(f)
    return sorted(files, reverse=True)  # 最新的在前

def parse_translation(file_path):
    """解析翻译文档"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取标题
    title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
    title = title_match.group(1) if title_match else file_path.stem
    
    # 提取视频链接
    link_match = re.search(r'\*\*视频链接\*\*: (.+)$', content, re.MULTILINE)
    video_link = link_match.group(1) if link_match else ""
    
    # 提取核心观点
    core_points = []
    points_section = re.search(r'## 核心观点\n(.+?)(?=\n## |\n---|\Z)', content, re.DOTALL)
    if points_section:
        points_text = points_section.group(1)
        # 提取每个要点的标题
        for match in re.finditer(r'### \d+\. (.+)\n(.+?)(?=\n### |\Z)', points_text, re.DOTALL):
            core_points.append({
                "title": match.group(1),
                "content": match.group(2).strip()[:500]
            })
    
    # 提取频道和日期
    channel_match = re.search(r'\*\*频道\*\*: (.+)$', content, re.MULTILINE)
    channel = channel_match.group(1) if channel_match else "Unknown"
    
    date_match = re.search(r'\*\*发布时间\*\*: (.+)$', content, re.MULTILINE)
    pub_date = date_match.group(1) if date_match else ""
    
    return {
        "filename": file_path.name,
        "title": title,
        "video_link": video_link,
        "channel": channel,
        "pub_date": pub_date,
        "core_points": core_points,
        "content": content
    }

def generate_podcast_script(doc):
    """生成播客脚本（可以用 AI 优化）"""
    
    script = f"""
大家好，欢迎收听「AI前沿解读」，我是你们的主播。

今天这期节目，我们来聊一个很有意思的视频：{doc['title']}

这个视频来自 {doc['channel']} 频道，原视频链接我会放在节目简介里。

好，我们直接进入正题。这个视频主要讲了以下几个核心观点：

"""
    
    for i, point in enumerate(doc['core_points'][:5], 1):
        script += f"""
第{i}点，{point['title']}。

{point['content'][:300]}

"""
    
    script += """
好了，以上就是今天这期节目的主要内容。

如果你觉得有收获，欢迎订阅我们的播客，我们下期再见！
"""
    
    return script.strip()

def text_to_speech_edge(text, output_path):
    """使用 Edge TTS 生成音频（免费）"""
    import asyncio
    import edge_tts
    
    async def generate():
        communicate = edge_tts.Communicate(text, "zh-CN-YunxiNeural")
        await communicate.save(output_path)
    
    asyncio.run(generate())
    print(f"✅ 音频已生成: {output_path}")

def update_podcast_rss():
    """更新播客 RSS"""
    # 调用之前写的脚本
    os.system(f"cd {PODCAST_REPO} && python /workspace/scripts/podcast_github_rss.py generate 2>/dev/null")

def git_push_podcast(message):
    """推送播客更新"""
    os.chdir(PODCAST_REPO)
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", message], check=True)
    subprocess.run(["git", "push"], check=True)
    print(f"✅ 已推送到 GitHub")

def process_one_translation(file_path):
    """处理单个翻译文档"""
    print(f"\n📄 处理: {file_path.name}")
    
    # 解析文档
    doc = parse_translation(file_path)
    print(f"   标题: {doc['title']}")
    print(f"   要点数: {len(doc['core_points'])}")
    
    # 生成播客脚本
    script = generate_podcast_script(doc)
    print(f"   脚本长度: {len(script)} 字")
    
    # 生成音频
    episode_id = f"ep{datetime.now().strftime('%Y%m%d%H%M')}"
    audio_filename = f"{episode_id}_{file_path.stem}.mp3"
    audio_path = f"{PODCAST_REPO}/episodes/{audio_filename}"
    
    os.makedirs(f"{PODCAST_REPO}/episodes", exist_ok=True)
    
    print(f"   正在生成音频...")
    text_to_speech_edge(script, audio_path)
    
    # 更新 episodes.json
    episodes_file = f"{PODCAST_REPO}/episodes.json"
    try:
        with open(episodes_file, 'r') as f:
            data = json.load(f)
    except:
        data = {"episodes": []}
    
    episode = {
        "id": episode_id,
        "title": f"解读：{doc['title'][:50]}",
        "description": f"本期解读 {doc['channel']} 的视频。原视频：{doc['video_link']}",
        "filename": audio_filename,
        "audio_url": f"https://ychenjk-sudo.github.io/NovaAI-Podcast/episodes/{audio_filename}",
        "duration": 0,
        "file_size": os.path.getsize(audio_path),
        "pub_date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0800"),
        "guid": episode_id,
        "source_file": file_path.name,
        "video_link": doc['video_link']
    }
    
    data["episodes"].insert(0, episode)
    
    with open(episodes_file, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return episode

def main():
    """主流程"""
    print("🎙️ YouTube 翻译 → 播客 自动化")
    print("=" * 50)
    
    # 更新翻译仓库
    print("\n📥 更新翻译仓库...")
    os.chdir(TRANSLATIONS_REPO)
    subprocess.run(["git", "pull"], capture_output=True)
    
    # 加载已处理列表
    processed = load_processed()
    processed_files = set(processed.get("processed", []))
    
    # 获取所有翻译文件
    files = get_translation_files()
    print(f"   找到 {len(files)} 个翻译文档")
    
    # 找出未处理的
    new_files = [f for f in files if f.name not in processed_files]
    print(f"   其中 {len(new_files)} 个未处理")
    
    if not new_files:
        print("\n✅ 没有新的翻译需要处理")
        return
    
    # 处理第一个新文档
    file_to_process = new_files[0]
    episode = process_one_translation(file_to_process)
    
    # 标记为已处理
    processed["processed"].append(file_to_process.name)
    save_processed(processed)
    
    # 更新 RSS
    print("\n📻 更新 RSS Feed...")
    update_podcast_rss()
    
    # 推送
    print("\n🚀 推送到 GitHub...")
    git_push_podcast(f"Add podcast: {episode['title']}")
    
    print(f"\n🎉 完成！")
    print(f"📻 RSS: https://ychenjk-sudo.github.io/lixiang-podcast/feed.xml")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        # 列出所有翻译
        files = get_translation_files()
        for f in files:
            print(f.name)
    else:
        main()

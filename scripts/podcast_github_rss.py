#!/usr/bin/env python3
"""
播客 RSS 生成器 - GitHub Pages 版
- 音频托管在 GitHub 仓库
- RSS Feed 通过 GitHub Pages 托管
- 完全免费
"""

import os
import json
import hashlib
import subprocess
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

# ============ 配置区域 ============

# GitHub 仓库配置
GITHUB_USERNAME = "ychenjk-sudo"
GITHUB_REPO = "lixiang-podcast"
GITHUB_BRANCH = "main"

# 生成的 URL 基础路径
# GitHub Pages URL: https://{username}.github.io/{repo}/
BASE_URL = f"https://{GITHUB_USERNAME}.github.io/{GITHUB_REPO}"

# 播客基础信息
PODCAST_CONFIG = {
    "title": "AI前沿解读",
    "description": "每期精选一个 YouTube 深度访谈，用中文为你解读 AI 领域最前沿的思想和实践。基于 YouTube 视频翻译，AI 自动生成。",
    "author": "理想",
    "email": "podcast@lixiang.com",
    "website": BASE_URL,
    "language": "zh-cn",
    "category": "Technology",
    "subcategory": "Tech News",
    "image": "",  # 封面图 URL
    "explicit": "false"
}

# 本地路径（仓库克隆到本地的位置）
REPO_PATH = "/workspace/lixiang-podcast"
EPISODES_DIR = f"{REPO_PATH}/episodes"
EPISODES_JSON = f"{REPO_PATH}/episodes.json"
RSS_FILE = f"{REPO_PATH}/feed.xml"

# ============ 核心函数 ============

def init_repo():
    """初始化仓库目录"""
    os.makedirs(EPISODES_DIR, exist_ok=True)
    
    # 初始化 episodes.json
    if not os.path.exists(EPISODES_JSON):
        with open(EPISODES_JSON, 'w') as f:
            json.dump({"episodes": []}, f)
    
    # 创建 index.html（GitHub Pages 需要）
    index_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{PODCAST_CONFIG['title']}</title>
    <meta http-equiv="refresh" content="0; url=feed.xml">
</head>
<body>
    <h1>{PODCAST_CONFIG['title']}</h1>
    <p>{PODCAST_CONFIG['description']}</p>
    <p><a href="feed.xml">RSS Feed</a></p>
</body>
</html>"""
    
    with open(f"{REPO_PATH}/index.html", 'w') as f:
        f.write(index_html)
    
    print(f"✅ 仓库目录已初始化: {REPO_PATH}")

def load_episodes():
    """加载单集列表"""
    try:
        with open(EPISODES_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"episodes": []}

def save_episodes(data):
    """保存单集列表"""
    data["last_updated"] = datetime.now().isoformat()
    with open(EPISODES_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_file_size(file_path):
    """获取文件大小"""
    return os.path.getsize(file_path)

def get_audio_duration(file_path):
    """获取音频时长"""
    try:
        import mutagen
        audio = mutagen.File(file_path)
        if audio and audio.info:
            return int(audio.info.length)
    except:
        pass
    return 0

def add_episode(title, description, audio_file_path):
    """
    添加新单集
    1. 复制音频到仓库
    2. 更新 episodes.json
    3. 生成 RSS
    """
    data = load_episodes()
    
    # 生成 episode ID
    episode_num = len(data["episodes"]) + 1
    episode_id = f"ep{episode_num:03d}"
    
    # 复制音频文件到仓库
    filename = os.path.basename(audio_file_path)
    new_filename = f"{episode_id}_{filename}"
    dest_path = f"{EPISODES_DIR}/{new_filename}"
    
    import shutil
    shutil.copy2(audio_file_path, dest_path)
    print(f"✅ 音频已复制: {dest_path}")
    
    # 音频 URL
    audio_url = f"{BASE_URL}/episodes/{new_filename}"
    
    # 获取音频信息
    duration = get_audio_duration(dest_path)
    file_size = get_file_size(dest_path)
    
    # 发布时间
    pub_date = datetime.now()
    
    # 创建单集记录
    episode = {
        "id": episode_id,
        "title": title,
        "description": description,
        "filename": new_filename,
        "audio_url": audio_url,
        "duration": duration,
        "file_size": file_size,
        "pub_date": pub_date.strftime("%a, %d %b %Y %H:%M:%S +0800"),
        "guid": hashlib.md5(f"{title}{pub_date.isoformat()}".encode()).hexdigest(),
        "created_at": pub_date.isoformat()
    }
    
    # 添加到列表
    data["episodes"].insert(0, episode)
    save_episodes(data)
    
    # 生成 RSS
    generate_rss()
    
    print(f"✅ 单集已添加: [{episode_id}] {title}")
    return episode

def generate_rss():
    """生成 RSS Feed"""
    data = load_episodes()
    config = PODCAST_CONFIG
    
    rss = Element('rss')
    rss.set('version', '2.0')
    rss.set('xmlns:itunes', 'http://www.itunes.com/dtds/podcast-1.0.dtd')
    rss.set('xmlns:atom', 'http://www.w3.org/2005/Atom')
    
    channel = SubElement(rss, 'channel')
    
    SubElement(channel, 'title').text = config['title']
    SubElement(channel, 'description').text = config['description']
    SubElement(channel, 'language').text = config['language']
    SubElement(channel, 'link').text = config['website']
    SubElement(channel, 'lastBuildDate').text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0800")
    
    # Atom self link
    atom_link = SubElement(channel, 'atom:link')
    atom_link.set('href', f"{BASE_URL}/feed.xml")
    atom_link.set('rel', 'self')
    atom_link.set('type', 'application/rss+xml')
    
    SubElement(channel, 'itunes:author').text = config['author']
    SubElement(channel, 'itunes:summary').text = config['description']
    SubElement(channel, 'itunes:explicit').text = config['explicit']
    
    if config.get('image'):
        image = SubElement(channel, 'itunes:image')
        image.set('href', config['image'])
    
    owner = SubElement(channel, 'itunes:owner')
    SubElement(owner, 'itunes:name').text = config['author']
    SubElement(owner, 'itunes:email').text = config['email']
    
    category = SubElement(channel, 'itunes:category')
    category.set('text', config['category'])
    
    # 添加单集
    for ep in data['episodes']:
        item = SubElement(channel, 'item')
        SubElement(item, 'title').text = ep['title']
        SubElement(item, 'description').text = ep['description']
        SubElement(item, 'pubDate').text = ep['pub_date']
        SubElement(item, 'guid').text = ep['guid']
        
        enclosure = SubElement(item, 'enclosure')
        enclosure.set('url', ep['audio_url'])
        enclosure.set('length', str(ep['file_size']))
        enclosure.set('type', 'audio/mpeg')
        
        SubElement(item, 'itunes:duration').text = str(ep['duration'])
        SubElement(item, 'itunes:summary').text = ep['description']
    
    xml_str = minidom.parseString(tostring(rss, encoding='unicode')).toprettyxml(indent="  ")
    
    with open(RSS_FILE, 'w', encoding='utf-8') as f:
        f.write(xml_str)
    
    print(f"✅ RSS 已生成: {RSS_FILE}")

def git_push(message="Update podcast"):
    """提交并推送到 GitHub"""
    os.chdir(REPO_PATH)
    
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", message], check=True)
    subprocess.run(["git", "push"], check=True)
    
    print(f"✅ 已推送到 GitHub")
    print(f"📻 RSS Feed: {BASE_URL}/feed.xml")

def publish(title, description, audio_file_path):
    """一键发布"""
    add_episode(title, description, audio_file_path)
    git_push(f"Add episode: {title}")
    
    print(f"\n🎉 发布完成！")
    print(f"📻 RSS: {BASE_URL}/feed.xml")
    print(f"💡 小宇宙/Spotify 订阅这个 RSS 即可自动同步")

# ============ 命令行 ============

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("""
播客发布工具 (GitHub Pages 版)

用法:
  python podcast_github_rss.py init                           # 初始化仓库
  python podcast_github_rss.py add <标题> <简介> <音频文件>    # 添加单集
  python podcast_github_rss.py push [提交信息]                # 推送到 GitHub
  python podcast_github_rss.py publish <标题> <简介> <音频>   # 一键发布

示例:
  python podcast_github_rss.py publish "EP01 首期节目" "欢迎收听" ./ep01.mp3
        """)
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "init":
        init_repo()
    elif cmd == "add" and len(sys.argv) >= 5:
        add_episode(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "push":
        msg = sys.argv[2] if len(sys.argv) > 2 else "Update podcast"
        git_push(msg)
    elif cmd == "publish" and len(sys.argv) >= 5:
        publish(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print("参数错误")

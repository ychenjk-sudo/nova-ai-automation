#!/usr/bin/env python3
"""
AK 博客精选 → 飞书文档
1. 抓取文章
2. 获取全文
3. AI摘要+翻译
4. 写入飞书文档
5. 返回文档链接
"""

import feedparser
import json
import re
import os
import sys
from datetime import datetime, timedelta
from html import unescape
import concurrent.futures
import socket

# 配置
STATE_FILE = "/workspace/scripts/.ak_blogs_doc_state.json"
MAX_ITEMS = 5
MAX_AGE_DAYS = 3

# RSS 源列表（精选）
RSS_FEEDS = [
    ("Simon Willison", "https://simonwillison.net/atom/everything/"),
    ("Jeff Geerling", "https://www.jeffgeerling.com/blog.xml"),
    ("antirez", "http://antirez.com/rss"),
    ("Pluralistic", "https://pluralistic.net/feed/"),
    ("Mitchell Hashimoto", "https://mitchellh.com/feed.xml"),
    ("Xe Iaso", "https://xeiaso.net/blog.rss"),
    ("Gary Marcus", "https://garymarcus.substack.com/feed"),
    ("Dan Abramov", "https://overreacted.io/rss.xml"),
    ("matklad", "https://matklad.github.io/feed.xml"),
    ("Paul Graham", "http://www.aaronsw.com/2002/feeds/pgessays.rss"),
    ("Julia Evans", "https://jvns.ca/atom.xml"),
    ("Stratechery", "https://stratechery.com/feed/"),
    ("fasterthanli.me", "https://fasterthanli.me/index.xml"),
    ("Drew DeVault", "https://drewdevault.com/blog/index.xml"),
    ("Coding Horror", "https://blog.codinghorror.com/rss/"),
    ("Hacker News Top", "https://hnrss.org/frontpage"),
]

def load_state():
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"sent_ids": [], "last_run": None}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def clean_html(html_text):
    if not html_text:
        return ""
    text = re.sub(r'<[^>]+>', '', str(html_text))
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def fetch_single_feed(feed_info):
    """抓取单个 RSS 源"""
    name, url = feed_info
    socket.setdefaulttimeout(8)
    try:
        feed = feedparser.parse(url)
        articles = []
        cutoff = datetime.now() - timedelta(days=MAX_AGE_DAYS)
        
        for entry in feed.entries[:3]:
            pub_date = None
            for date_field in ['published', 'updated', 'created']:
                if hasattr(entry, date_field + '_parsed') and getattr(entry, date_field + '_parsed'):
                    try:
                        pub_date = datetime(*getattr(entry, date_field + '_parsed')[:6])
                        break
                    except:
                        pass
            
            if pub_date and pub_date.replace(tzinfo=None) < cutoff:
                continue
            
            title = entry.get('title', '')
            link = entry.get('link', '')
            # 获取完整内容
            content = entry.get('content', [{}])[0].get('value', '') if entry.get('content') else ''
            if not content:
                content = entry.get('summary', entry.get('description', ''))
            
            content_text = clean_html(content)
            
            if title and link:
                articles.append({
                    "id": link,
                    "title": title,
                    "link": link,
                    "source": name,
                    "content": content_text[:5000],  # 限制长度
                    "pub_date": pub_date.isoformat() if pub_date else None
                })
        
        return articles
    except Exception as e:
        return []

def fetch_all_feeds():
    """并发抓取"""
    all_articles = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        results = executor.map(fetch_single_feed, RSS_FEEDS)
        for articles in results:
            all_articles.extend(articles)
    
    all_articles.sort(key=lambda x: x.get('pub_date') or '', reverse=True)
    return all_articles

def format_for_doc(articles):
    """格式化为飞书文档 Markdown"""
    today = datetime.now().strftime("%Y年%m月%d日")
    
    lines = [
        f"# 📚 AK 博客精选 ({today})",
        "",
        f"> 来源: Karpathy 推荐的 HN 热门博客 | 共 {len(articles)} 篇",
        "",
        "---",
        "",
    ]
    
    for i, art in enumerate(articles, 1):
        lines.append(f"## {i}. {art['title']}")
        lines.append("")
        lines.append(f"**来源**: {art['source']} | **链接**: {art['link']}")
        lines.append("")
        
        if art.get('summary_zh'):
            lines.append("### 📌 核心观点")
            lines.append("")
            lines.append(art['summary_zh'])
            lines.append("")
        
        if art.get('translation'):
            lines.append("### 📖 内容翻译")
            lines.append("")
            lines.append(art['translation'])
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    return "\n".join(lines)

def main():
    """主函数 - 返回文章数据供外部处理"""
    state = load_state()
    sent_ids = set(state.get("sent_ids", []))
    
    print("正在抓取 AK 推荐博客...", file=sys.stderr)
    articles = fetch_all_feeds()
    print(f"共抓取到 {len(articles)} 篇", file=sys.stderr)
    
    new_articles = [a for a in articles if a["id"] not in sent_ids]
    print(f"其中新文章 {len(new_articles)} 篇", file=sys.stderr)
    
    if not new_articles:
        print("没有新文章", file=sys.stderr)
        return None
    
    to_process = new_articles[:MAX_ITEMS]
    
    # 更新状态
    for art in to_process:
        sent_ids.add(art["id"])
    state["sent_ids"] = list(sent_ids)[-200:]
    state["last_run"] = datetime.now().isoformat()
    save_state(state)
    
    # 输出 JSON 供外部处理
    print(json.dumps(to_process, ensure_ascii=False, indent=2))
    return to_process

if __name__ == "__main__":
    main()

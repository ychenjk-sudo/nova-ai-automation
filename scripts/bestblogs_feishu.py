#!/usr/bin/env python3
"""
BestBlogs AI新闻 → 飞书推送
每天抓取BestBlogs高分AI文章，推送到飞书
"""

import feedparser
import json
import re
from datetime import datetime, timedelta
from html import unescape
import hashlib

# 配置
RSS_URL = "https://www.bestblogs.dev/zh/feeds/rss?category=ai&minScore=85"
STATE_FILE = "/workspace/scripts/.bestblogs_state.json"
MAX_ITEMS = 5  # 每次最多推送几条

def load_state():
    """加载已推送的文章ID"""
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"sent_ids": [], "last_run": None}

def save_state(state):
    """保存状态"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def clean_html(html_text):
    """清理HTML标签，提取纯文本"""
    # 移除HTML标签
    text = re.sub(r'<[^>]+>', '', html_text)
    # 解码HTML实体
    text = unescape(text)
    # 清理多余空白
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_summary(description):
    """从description中提取摘要"""
    # 尝试提取 One-Sentence Summary
    match = re.search(r'One-Sentence Summary[^<]*</h3>\s*<p[^>]*>([^<]+)', description)
    if match:
        return clean_html(match.group(1))
    
    # 尝试提取 Summary
    match = re.search(r'Summary[^<]*</h3>\s*<p[^>]*>([^<]+)', description)
    if match:
        return clean_html(match.group(1))[:200] + "..."
    
    return clean_html(description)[:200] + "..."

def extract_score(description):
    """提取AI评分"""
    match = re.search(r'AI Score[^<]*</span><span[^>]*>(\d+)', description)
    if match:
        return int(match.group(1))
    return None

def extract_source(description):
    """提取来源"""
    match = re.search(r'Source[^<]*</span><span[^>]*>([^<]+)', description)
    if match:
        return clean_html(match.group(1))
    return None

def fetch_articles():
    """抓取RSS文章"""
    feed = feedparser.parse(RSS_URL)
    articles = []
    
    for entry in feed.entries[:20]:  # 最多处理20条
        article = {
            "id": entry.get("guid", entry.get("link", "")),
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "published": entry.get("published", ""),
            "description": entry.get("description", ""),
        }
        
        # 提取结构化信息
        article["summary"] = extract_summary(article["description"])
        article["score"] = extract_score(article["description"])
        article["source"] = extract_source(article["description"])
        
        articles.append(article)
    
    return articles

def format_feishu_message(articles):
    """格式化飞书消息"""
    if not articles:
        return None
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    lines = [f"📰 **AI新闻精选** ({today})", ""]
    
    for i, art in enumerate(articles, 1):
        score_emoji = "🔥" if art["score"] and art["score"] >= 90 else "⭐"
        score_str = f" [{art['score']}分]" if art["score"] else ""
        
        lines.append(f"**{i}. {art['title']}**{score_str}")
        lines.append(f"   {art['summary']}")
        if art["source"]:
            lines.append(f"   来源: {art['source']}")
        lines.append(f"   🔗 {art['link']}")
        lines.append("")
    
    lines.append("---")
    lines.append("_数据来源: BestBlogs.dev_")
    
    return "\n".join(lines)

def main():
    """主函数"""
    state = load_state()
    sent_ids = set(state.get("sent_ids", []))
    
    # 抓取文章
    articles = fetch_articles()
    
    # 过滤已发送的
    new_articles = [a for a in articles if a["id"] not in sent_ids]
    
    if not new_articles:
        print("没有新文章")
        return None
    
    # 取前N条
    to_send = new_articles[:MAX_ITEMS]
    
    # 格式化消息
    message = format_feishu_message(to_send)
    
    # 更新状态
    for art in to_send:
        sent_ids.add(art["id"])
    
    # 保持最近100条记录
    state["sent_ids"] = list(sent_ids)[-100:]
    state["last_run"] = datetime.now().isoformat()
    save_state(state)
    
    return message

if __name__ == "__main__":
    msg = main()
    if msg:
        print(msg)
    else:
        print("No new articles to send")

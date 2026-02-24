#!/usr/bin/env python3
"""
AK (Karpathy) 推荐的 92 个 HN 热门博客 → 飞书推送
"""

import feedparser
import json
import re
from datetime import datetime, timedelta
from html import unescape
import hashlib
import concurrent.futures
import time

# AK 推荐的 OPML 地址
OPML_URL = "https://gist.githubusercontent.com/emschwartz/e6d2bf860ccc367fe37ff953ba6de66b/raw/426957f043dc0054f95aae6c19de1d0b4ecc2bb2/hn-popular-blogs-2025.opml"
STATE_FILE = "/workspace/scripts/.ak_blogs_state.json"
MAX_ITEMS = 5  # 每次最多推送几条
MAX_AGE_DAYS = 3  # 只看最近几天的文章

# 预定义的 RSS 源列表（从 OPML 提取）
RSS_FEEDS = [
    ("Simon Willison", "https://simonwillison.net/atom/everything/"),
    ("Jeff Geerling", "https://www.jeffgeerling.com/blog.xml"),
    ("Krebs on Security", "https://krebsonsecurity.com/feed/"),
    ("Daring Fireball", "https://daringfireball.net/feeds/main"),
    ("antirez", "http://antirez.com/rss"),
    ("Pluralistic", "https://pluralistic.net/feed/"),
    ("Mitchell Hashimoto", "https://mitchellh.com/feed.xml"),
    ("Dynomight", "https://dynomight.net/feed.xml"),
    ("Xe Iaso", "https://xeiaso.net/blog.rss"),
    ("Old New Thing", "https://devblogs.microsoft.com/oldnewthing/feed"),
    ("Ken Shirriff", "https://www.righto.com/feeds/posts/default"),
    ("Armin Ronacher", "https://lucumr.pocoo.org/feed.atom"),
    ("Gary Marcus", "https://garymarcus.substack.com/feed"),
    ("Rachel by the Bay", "https://rachelbythebay.com/w/atom.xml"),
    ("Dan Abramov", "https://overreacted.io/rss.xml"),
    ("John D Cook", "https://www.johndcook.com/blog/feed/"),
    ("matklad", "https://matklad.github.io/feed.xml"),
    ("Evan Hahn", "https://evanhahn.com/feed.xml"),
    ("Terrible Software", "https://terriblesoftware.org/feed/"),
    ("Paul Graham", "http://www.aaronsw.com/2002/feeds/pgessays.rss"),
    ("Julia Evans", "https://jvns.ca/atom.xml"),
    ("Stratechery", "https://stratechery.com/feed/"),
    ("Hillel Wayne", "https://www.hillelwayne.com/index.xml"),
    ("fasterthanli.me", "https://fasterthanli.me/index.xml"),
    ("Drew DeVault", "https://drewdevault.com/blog/index.xml"),
    ("Molly White", "https://www.citationneeded.news/rss/"),
    ("Lenny's Newsletter", "https://www.lennysnewsletter.com/feed"),
    ("lcamtuf", "https://lcamtuf.substack.com/feed"),
    ("Ben Thompson", "https://stratechery.com/feed/"),
    ("Coding Horror", "https://blog.codinghorror.com/rss/"),
    ("Hacker News", "https://hnrss.org/frontpage"),
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

def parse_date(date_str):
    """尝试解析日期"""
    if not date_str:
        return None
    try:
        # feedparser 通常会解析成 time tuple
        import email.utils
        parsed = email.utils.parsedate_to_datetime(date_str)
        return parsed
    except:
        pass
    return None

def fetch_single_feed(feed_info):
    """抓取单个 RSS 源"""
    name, url = feed_info
    try:
        import socket
        socket.setdefaulttimeout(5)  # 5秒超时
        feed = feedparser.parse(url)
        articles = []
        cutoff = datetime.now() - timedelta(days=MAX_AGE_DAYS)
        
        for entry in feed.entries[:5]:  # 每个源最多取5条
            # 解析发布时间
            pub_date = None
            for date_field in ['published', 'updated', 'created']:
                if hasattr(entry, date_field + '_parsed') and getattr(entry, date_field + '_parsed'):
                    try:
                        pub_date = datetime(*getattr(entry, date_field + '_parsed')[:6])
                        break
                    except:
                        pass
            
            # 过滤太老的文章
            if pub_date and pub_date.replace(tzinfo=None) < cutoff:
                continue
            
            title = entry.get('title', '')
            link = entry.get('link', '')
            summary = clean_html(entry.get('summary', entry.get('description', '')))[:200]
            
            if title and link:
                articles.append({
                    "id": link,
                    "title": title,
                    "link": link,
                    "source": name,
                    "summary": summary + "..." if len(summary) >= 200 else summary,
                    "pub_date": pub_date.isoformat() if pub_date else None
                })
        
        return articles
    except Exception as e:
        return []

def fetch_all_feeds():
    """并发抓取所有源"""
    all_articles = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(fetch_single_feed, RSS_FEEDS)
        for articles in results:
            all_articles.extend(articles)
    
    # 按时间排序（最新的在前）
    all_articles.sort(key=lambda x: x.get('pub_date') or '', reverse=True)
    
    return all_articles

def format_feishu_message(articles):
    if not articles:
        return None
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    lines = [f"📚 **AK推荐博客精选** ({today})", ""]
    
    for i, art in enumerate(articles, 1):
        lines.append(f"**{i}. {art['title']}**")
        lines.append(f"   ✍️ {art['source']}")
        if art['summary']:
            lines.append(f"   {art['summary'][:100]}...")
        lines.append(f"   🔗 {art['link']}")
        lines.append("")
    
    lines.append("---")
    lines.append("_来源: Karpathy 推荐的 92 个 HN 热门博客_")
    
    return "\n".join(lines)

def main():
    state = load_state()
    sent_ids = set(state.get("sent_ids", []))
    
    print("正在抓取 AK 推荐的博客...")
    articles = fetch_all_feeds()
    print(f"共抓取到 {len(articles)} 篇文章")
    
    # 过滤已发送的
    new_articles = [a for a in articles if a["id"] not in sent_ids]
    print(f"其中新文章 {len(new_articles)} 篇")
    
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
    
    state["sent_ids"] = list(sent_ids)[-200:]
    state["last_run"] = datetime.now().isoformat()
    save_state(state)
    
    return message

if __name__ == "__main__":
    msg = main()
    if msg:
        print(msg)
    else:
        print("No new articles to send")

from atproto import Client, models
from dotenv import load_dotenv
import os
import openai
import schedule
import time
import random
import re
import grapheme
import json
from datetime import datetime

# ========== 🎐 Sleep Time Checker ==========
def is_sleep_time():
    now = datetime.now()
    current_minutes = now.hour * 60 + now.minute
    sleep_start = 22 * 60 + 30  # 10:30 PM
    sleep_end = 6 * 60 + 15     # 6:15 AM
    return sleep_start <= current_minutes or current_minutes <= sleep_end

# ========== 🌱 Load .env ==========
load_dotenv()
client = Client()
client.login(os.getenv("BSKY_HANDLE"), os.getenv("BSKY_PASSWORD"))
my_did = client.me.did
openai.api_key = os.getenv("OPENAI_API_KEY")

# ========== 🌐 RSS Feed Sources ==========
RSS_FEEDS = [
    "https://feeds.npr.org/1014/rss.xml",
    "http://rss.cnn.com/rss/edition.rss",
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.yahoo.com/news/rss",
]

# ========== 📆 Load previously posted headlines ==========
POSTED_LOG = "posted_headlines.json"
if os.path.exists(POSTED_LOG):
    with open(POSTED_LOG, "r") as f:
        posted_headlines = json.load(f)
else:
    posted_headlines = []

# ========== 🧐 Sassify Function ==========
def generate_sassy_headline(original_text):
    prompt = f"""
Rewrite this political headline with drag queen sass. Keep it sharp, short, and spicy. Add emojis if needed. Never punch down. Your sass targets political figures, corruption, and hypocrisy—not everyday people or victims.
You're a drag queen—fierce, fabulous, and always punching up at power with style.
Headline: "{original_text}"
Sassified:
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a sassy, drag-queen-style AI who roasts political headlines with savage wit and fierce commentary."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.9,
        max_tokens=60
    )
    return response.choices[0].message.content.strip()

# ========== 📌 Facet Builder ==========
def build_facets_from_text(post_text):
    return []  # Skipping facet building for now

# ========== 💬 Safe Post Helper ==========
def safe_post(post_text, facets, reply_to=None):
    global my_did
    if grapheme.length(post_text) > 300:
        print(f"⚠️ Truncating post from {grapheme.length(post_text)} to 300 graphemes.")
        post_text = grapheme.slice(post_text, 0, 300).rstrip()

    record_kwargs = {
        "text": post_text,
        "facets": facets,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    if reply_to:
        uri, cid = reply_to
        record_kwargs["reply"] = models.app.bsky.feed.post.ReplyRef(
            root={"uri": uri, "cid": cid},
            parent={"uri": uri, "cid": cid}
        )

    record = models.app.bsky.feed.post.Record(**record_kwargs).model_dump(by_alias=True)

    for attempt in range(4):
        try:
            client.app.bsky.feed.post.create(repo=my_did, record=record)
            print(f"📣 Ivana posted: {post_text}")
            return True
        except Exception as e:
            if hasattr(e, 'error') and e.error == 'InvalidToken':
                print(f"🔄 Token expired (attempt {attempt + 1}). Re-logging in...")
                client.login(os.getenv("BSKY_HANDLE"), os.getenv("BSKY_PASSWORD"))
                my_did = client.me.did
                delay = random.randint(60 * (attempt + 1), 120 * (attempt + 2))
                time.sleep(delay)
            else:
                print(f"⚠️ Error posting: {e}")
                return False
    print("❌ All retries failed.")
    return False

# ========== 🧠 Ask If We Should Reply ==========
def ask_reply(text: str) -> str:
    resp = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are Ivana, a political drag queen who roasts nonsense with flair. Reply only when it’s juicy and worth your sass."},
            {"role": "user", "content": (
                f"Here is a post:\n\"{text}\"\n"
                "Would you want to reply? Answer YES or NO. If YES, generate the reply. Add emojis if needed. Keep it under 280 graphemes."
            )}
        ],
        temperature=0.85,
        max_tokens=150
    )
    content = resp.choices[0].message.content.strip()
    if content.upper().startswith("YES"):
        parts = content.split("\n", 1)
        return parts[1].strip() if len(parts) > 1 else ""
    return ""

# ========== 📰 Fetch headlines from RSS ==========
def fetch_headlines():
    import feedparser
    headlines = []
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        valid_entries = [
            {
                "source": feed.feed.title if 'title' in feed.feed else "Unknown",
                "text": entry.title.strip(),
                "link": entry.link
            }
            for entry in feed.entries[:5]
            if entry.title.strip() not in posted_headlines
        ]
        if valid_entries:
            headlines.append(random.choice(valid_entries))
    return headlines

# ========== 💬 Post to Bluesky ==========
def post_sassy_skoot():
    try:
        headlines = fetch_headlines()
        if not headlines:
            print("😴 No fresh headlines to roast.")
            return

        headline = random.choice(headlines)
        sassified = generate_sassy_headline(headline["text"]).strip()

        if sassified.startswith('"') and sassified.endswith('"'):
            sassified = sassified[1:-1].strip()

        link = headline["link"].strip()
        emoji_line = "💅🔥"
        post_text = f"{sassified}\n{emoji_line}\n{link}"
        facets = build_facets_from_text(post_text)

        safe_post(post_text, facets)

        posted_headlines.append(headline["text"])
        posted_headlines[:] = posted_headlines[-100:]
        with open(POSTED_LOG, "w") as f:
            json.dump(posted_headlines, f)

    except Exception as e:
        print(f"Error posting sassified headline: {e}")

# ========== 💬 Scan for Replies ==========
def scan_and_reply():
    if is_sleep_time():
        return
    try:
        notes = client.app.bsky.notification.list_notifications({"limit": 10}).notifications
        for n in notes:
            if n.author.did == my_did:
                continue
            if n.reason == "reply" and not n.is_read:
                reply_text = ask_reply(n.record.text)
                if reply_text:
                    uri = n.record.reply.root.uri
                    cid = n.record.reply.root.cid
                    safe_post(reply_text, build_facets_from_text(reply_text), reply_to=(uri, cid))
                    client.app.bsky.notification.update_seen({"seenAt": datetime.utcnow().isoformat() + "Z"})
                    return
    except Exception as e:
        print("Error scanning notifications for Ivana:", e)
    try:
        timeline = client.app.bsky.feed.get_timeline({"limit": 10}).feed
        for post in timeline:
            if post.post.author.did == my_did:
                continue
            uri = post.post.uri
            cid = post.post.cid
            text = post.post.record.text or ""
            if not text:
                continue
            reply_text = ask_reply(text)
            if reply_text:
                safe_post(reply_text, build_facets_from_text(reply_text), reply_to=(uri, cid))
                return
    except Exception as e:
        print("Error scanning feed for Ivana:", e)

# ========== ⏱ Scheduler ==========
schedule.every(random.randint(30, 60)).minutes.do(post_sassy_skoot)
schedule.every(random.randint(45, 75)).minutes.do(scan_and_reply)

print("💅🔥 Ivana is in full glam and ready to roast...")
while True:
    schedule.run_pending()
    time.sleep(10)

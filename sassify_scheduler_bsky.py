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
import feedparser
from datetime import datetime
import smtplib

# ======== Optional language detection ========
try:
    from langdetect import detect
except ImportError:
    def detect(text):
        return "en"

# ========== 🎐 Sleep Time Checker ==========
def is_sleep_time():
    now = datetime.now()
    current_minutes = now.hour * 60 + now.minute
    return (22 * 60 + 30) <= current_minutes or current_minutes <= (6 * 60 + 15)

# ========== 🌱 Load .env & Login ==========
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

# ========== 📹 Posted Log ==========
POSTED_LOG = "posted_headlines.json"
if os.path.exists(POSTED_LOG):
    with open(POSTED_LOG, "r") as f:
        posted_headlines = json.load(f)
else:
    posted_headlines = []

# ========== 🧐 Sassify Function ==========
def generate_sassy_headline(original_text):
    prompt = f"""
Rewrite this political headline with drag queen sass. Keep it sarcastic, focusing on corruption and hypocrisy—not everyday people or victims.
You're a drag queen—fierce, fabulous, and always punching up at power with style.
Headline: {original_text}
Sassified:
    """
    resp = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a sassy, drag queen commentator. Sassify political headlines with savage wit and fierce commentary."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.9,
        max_tokens=60
    )
    return resp.choices[0].message.content.strip()

# ========== 📌 Facet Builder (basic) ==========
def build_facets_from_text(post_text):
    # Quick facets: skip on validation errors
    facets = []
    # URLs
    for match in re.finditer(r'(https?://\S+)', post_text):
        facets.append({"index": {"byteStart": match.start(), "byteEnd": match.end()}, "features": [{"$type": "app.bsky.richtext.facet#link", "uri": match.group(0)}]})
    # Hashtags
    for match in re.finditer(r'#\w+', post_text):
        tag = match.group(0)[1:]
        facets.append({"index": {"byteStart": match.start(), "byteEnd": match.end()}, "features": [{"$type": "app.bsky.richtext.facet#hashtag", "text": tag}]})
    # Mentions (basic): treat as text
    for match in re.finditer(r'@\w+', post_text):
        user = match.group(0)[1:]
        facets.append({"index": {"byteStart": match.start(), "byteEnd": match.end()}, "features": [{"$type": "app.bsky.richtext.facet#mention", "did": user}]})
    return facets

# ========== 🎯 Trending Topics ==========
def fetch_trending():
    return ["#HypocrisyAlert", "#FilibusterFriday"]

# ========== 😀 Emojis & GIFs ==========
EMOJIS = ["💅", "🔥", "🍵", "👑"]
GIFS = [
    "https://media1.giphy.com/media/3o6Zt481isNVuQI1l6/giphy.gif",
    "https://media2.giphy.com/media/l0MYEqEzwMWFCg8rm/giphy.gif"
]

def spruce_with_reaction(text):
    return text + (" " + random.choice(EMOJIS) if random.random() < 0.5 else "\n" + random.choice(GIFS))

# ========== ✉️ Error Alerts ==========
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
ALERT_FROM = os.getenv("ALERT_FROM")
ALERT_EMAIL = os.getenv("ALERT_EMAIL")

def send_error_email(err):
    print(f"Error Alert: {err}")
    try:
        with smtplib.SMTP(SMTP_SERVER, int(SMTP_PORT)) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            msg = f"Subject: Ivana Error\n\nIvana bot threw:\n{err}"
            server.sendmail(ALERT_FROM, ALERT_EMAIL, msg)
    except Exception as e:
        print(f"Failed email alert: {e}")

# ========== 💬 Safe Post Helper ==========
def safe_post(post_text, facets, reply_to=None):
    try:
        if grapheme.length(post_text) > 300:
            post_text = grapheme.slice(post_text, 0, 300).rstrip()
        record_kwargs = {"text": post_text, "facets": facets, "created_at": datetime.utcnow().isoformat() + "Z"}
        if reply_to:
            uri, cid = reply_to
            record_kwargs["reply"] = models.app.bsky.feed.post.ReplyRef(root={"uri": uri, "cid": cid}, parent={"uri": uri, "cid": cid})
        # Attempt post with facets
        rec = models.app.bsky.feed.post.Record(**record_kwargs).model_dump(by_alias=True)
        client.app.bsky.feed.post.create(repo=my_did, record=rec)
        return True
    except Exception as e:
        print(f"Error in safe_post (with facets): {e}")
        # Fallback: try without facets
        try:
            fallback_kwargs = {k: v for k,v in record_kwargs.items() if k != "facets"}
            rec2 = models.app.bsky.feed.post.Record(**fallback_kwargs).model_dump(by_alias=True)
            client.app.bsky.feed.post.create(repo=my_did, record=rec2)
            return True
        except Exception as e2:
            print(f"Error in safe_post (fallback): {e2}")
            send_error_email(str(e2))
            return False

# ========== 🧠 Reply Logic ==========
def ask_reply(text: str) -> str:
    try:
        lang = detect(text)
    except:
        lang = "en"
    system_msg = f"You are Ivana with full sass in {lang}. Reply only if juicy." if lang != "en" else "You are Ivana with full sass. Reply only if juicy."
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role":"system","content":system_msg},{"role":"user","content":f"Post: {text}\nReply? YES or NO and then your reply."}],
            temperature=0.85,
            max_tokens=150
        )
        content = resp.choices[0].message.content.strip()
        if content.upper().startswith("YES"):
            return content.split("\n", 1)[1].strip()
    except Exception as e:
        print(f"Error in ask_reply: {e}")
        send_error_email(str(e))
    return ""

# ========== 🧐 #RoastMe Handler ==========
def check_roastme_mentions():
    try:
        notes = client.app.bsky.notification.list_notifications({"limit":10}).notifications
        for n in notes:
            if n.author.did == my_did or n.reason != "mention":
                continue
            if "#roastme" in (n.record.text or "").lower():
                try:
                    roast = openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=[{"role":"system","content":"Ivana roast user with savage wit."},{"role":"user","content":f"Roast {n.author.handle}"}],
                        temperature=0.9,
                        max_tokens=60
                    ).choices[0].message.content.strip()
                    safe_post(roast, build_facets_from_text(roast), reply_to=(n.record.reply.root.uri, n.record.reply.root.cid))
                except Exception as e:
                    print(f"Error in roastme: {e}")
                    send_error_email(str(e))
    except Exception as e:
        print(f"Error fetching mentions: {e}")
        send_error_email(str(e))

# ========== 📰 Fetch headlines ==========
def fetch_headlines():
    headlines = []
    try:
        for url in RSS_FEEDS:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                if entry.title.strip() not in posted_headlines:
                    headlines.append({"text": entry.title, "link": entry.link})
    except Exception as e:
        print(f"Error fetch_headlines: {e}")
        send_error_email(str(e))
    return headlines

# ========== 💬 Post Scheduler ==========
def post_sassy_skoot():
    try:
        trends = fetch_trending()
        if trends:
            safe_post(f"Trending now: {random.choice(trends)} — spill the tea! ☕", build_facets_from_text("Trending now: ..."))
        heads = fetch_headlines()
        if heads:
            h = random.choice(heads)
            sass = generate_sassy_headline(h["text"]).strip('"')
            txt = f"{sass}\n💅🔥\n{h['link']}"
            safe_post(spruce_with_reaction(txt), build_facets_from_text(txt))
            posted_headlines.append(h["text"])
            posted_headlines[:] = posted_headlines[-100:]
            with open(POSTED_LOG, "w") as f:
                json.dump(posted_headlines, f)
    except Exception as e:
        print(f"Error in post_sassy_skoot: {e}")
        send_error_email(str(e))

# ========== 💬 Reply Scanner ==========
def scan_and_reply():
    if is_sleep_time():
        return
    try:
        notes = client.app.bsky.notification.list_notifications({"limit":10}).notifications
        for n in notes:
            if n.author.did == my_did or n.reason != "reply":
                continue
            if repl := ask_reply(n.record.text or ""):
                safe_post(repl, build_facets_from_text(repl), reply_to=(n.record.reply.root.uri, n.record.reply.root.cid))
                break
    except Exception as e:
        print(f"Error scan replies: {e}")
        send_error_email(str(e))

# ========== ⏱ Scheduler ==========
if __name__ == "__main__":
    schedule.every(random.randint(30,60)).minutes.do(post_sassy_skoot)
    schedule.every(random.randint(60,90)).minutes.do(scan_and_reply)
    schedule.every(random.randint(90,120)).minutes.do(check_roastme_mentions)
    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            print(f"Scheduler loop error: {e}")
            send_error_email(str(e))
        time.sleep(10)


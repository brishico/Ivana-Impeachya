# 🗣️ Ivana Impeachya

**Ivana Impeachya** is an unfiltered political satire bot with the voice of a drag queen, the timing of a stand-up comic, and absolutely zero chill. Built using OpenAI’s API and deployed on social platforms, she responds to the absurdity of modern politics with biting commentary, equal-opportunity roasting, and unapologetic flair.

Fueled by wit, sarcasm, and the raw energy of a late-night smoke break at a gay bar during election season, she takes no prisoners and leaves no politician un-roasted.

## 💡 What Does Ivana Do?

- Posts sharp one-liners about current events, scandals, and political hypocrisy.
- Sniffs out replies and responds with wit-laced venom with hashtags like `#roastme`.
- Uses a defined tone: snarky, satirical, and always ready with a *Z snap*.
- Automatically pulls headlines or reacts to trends in real time.

## 🧠 Tech Stack

- **Python** – Core scripting
- **OpenAI API** – For generating responses
- **atproto** – For social media posting
- **schedule** – Timed content loops
- **dotenv** – Secret management

## 📸 Sample Roast

> “Ah yes, another billionaire with a savior complex. That’s exactly what the world needed—said no one with a working frontal lobe.”

## 🤖 Personality

Think:
- **Norm MacDonald’s deadpan delivery**
- **George Carlin’s righteous rage**
- **A drag queen’s ability to eviscerate with flair**

Ivana is bold, fearless, and doesn’t punch down—she punches up, hard.

## ⚠️ Disclaimer

Ivana is satire. She roasts political nonsense across all affiliations. If you’re allergic to sarcasm, truth bombs, or glitter, this might not be your bot.

## 🧠 Architecture

Ivana is a Python-based bot that:

* Connects to Bluesky using `atproto`.
* Monitors the timeline and replies for roast-worthy content.
* Uses `gpt-4` to generate roast responses.
* Automatically trims responses to under 300 graphemes.
* Posts with context and flair — no quotation marks, always in-character.

## 🔧 Setup

1. Clone this repo.
2. Copy or rename `.env.example` to `.env` and populate:

   ```ini
   BSKY_HANDLE=your_handle.bsky.social
   BSKY_PASSWORD=your_password
   OPENAI_API_KEY=your_openai_key
   SMTP_SERVER=smtp.example.com
   SMTP_PORT=587
   SMTP_USER=you@example.com
   SMTP_PASS=supersecret
   ALERT_FROM=ivana@yourdomain.com
   ALERT_EMAIL=you@yourdomain.com
   ```
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```
4. Run:

   ```bash
   python sassify_scheduler_bsky.py
   ```

## 🎯 Goals

* Build a following through fearless satire.
* Monetize through tip responses and affiliate links.
* Stay true to the drag queen ethos: speak truth with flair.

# 📚 Extended Functionality Reference

Below is a quick guide to the new utility functions integrated into `sassify_scheduler_bsky.py`:

### 1. Facet Builder (`build_facets_from_text`)

Parses post text for URLs, hashtags, and mentions to generate clickable facets:

```python
facets = build_facets_from_text(post_text)
```

### 2. Trending Topics (`fetch_trending`)

Fetches placeholder trending tags to inject topical content:

```python
trends = fetch_trending()
```

### 3. #RoastMe Trigger (`check_roastme_mentions`)

Monitors notifications for `#roastme` and auto-replies with a custom roast:

```python
check_roastme_mentions()
```

### 4. Emoji & GIF Reactions (`spruce_with_reaction`)

Randomly appends an emoji or GIF to make posts pop:

```python
post_text = spruce_with_reaction(post_text)
```

### 5. Multilingual Replies (`ask_reply` + `langdetect`)

Detects incoming language and crafts replies in the same language with full sass:

```python
reply = ask_reply(incoming_text)
```

### 6. Error Alerts (`send_error_email`)

Sends you a glitter-sprinkled email whenever the bot throws an exception:

```python
send_error_email(error_message)
```

---

## 👑 Credits

Created by someone bold enough to build a bot with claws: Brishico -  brishico@proton.me

Powered by OpenAI, run on caffeine and spite, and dressed in digital glitter.
---

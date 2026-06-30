# 📋 MANUAL REDDIT DATA COLLECTION GUIDE

> If ALL automated scrapers fail, use this manual method. 
> It takes 45-60 minutes but guarantees data.

---

## Method 1: Browser Copy-Paste (Guaranteed to Work)

### Step 1: Open Reddit Search URLs

Open these URLs in your browser (one at a time):

```
https://www.reddit.com/r/spotify/search/?q=discover%20new%20music&sort=relevance&t=year
https://www.reddit.com/r/spotify/search/?q=recommendation%20algorithm&sort=relevance&t=year
https://www.reddit.com/r/spotify/search/?q=playlist%20stuck%20same%20songs&sort=relevance&t=year
https://www.reddit.com/r/spotify/search/?q=bored%20with%20spotify&sort=relevance&t=year
https://www.reddit.com/r/spotify/search/?q=discovery%20weekly%20bad&sort=relevance&t=year
https://www.reddit.com/r/spotify/search/?q=radio%20repetitive&sort=relevance&t=year
https://www.reddit.com/r/spotify/search/?q=shuffle%20algorithm&sort=relevance&t=year
https://www.reddit.com/r/spotify/search/?q=can%27t%20find%20new%20music&sort=relevance&t=year
https://www.reddit.com/r/spotify/search/?q=recommendations%20terrible&sort=relevance&t=year
https://www.reddit.com/r/spotify/search/?q=daily%20mix%20same&sort=relevance&t=year
https://www.reddit.com/r/spotify/search/?q=on%20repeat%20stuck&sort=relevance&t=year
https://www.reddit.com/r/spotify/search/?q=algorithm%20broken&sort=relevance&t=year
https://www.reddit.com/r/spotify/search/?q=new%20music%20discovery&sort=relevance&t=year
https://www.reddit.com/r/spotify/search/?q=song%20repetition&sort=relevance&t=year
https://www.reddit.com/r/spotify/search/?q=playlist%20rotation&sort=relevance&t=year
```

Also search these subreddits:
- r/truespotify
- r/spotifywrapped
- r/WeAreTheMusicMakers
- r/music
- r/AppleMusic
- r/musicsuggestions

### Step 2: Copy High-Value Posts

For each search results page:
1. **Scroll down** to load more posts (Reddit loads 25 at a time)
2. **Open posts with 10+ comments** in new tabs
3. **Copy the post title + body** into a text file
4. **Copy top 5-10 comments** from each post

**What to copy:**
```
--- POST ---
Title: [exact title]
Subreddit: r/spotify
Score: [upvote count]
Comments: [comment count]
Text: [full post text]
URL: [reddit URL]

--- COMMENTS ---
[Username]: [comment text]
[Username]: [comment text]
```

**Target:** 100-150 posts + 200-300 comments = 300-450 total entries

### Step 3: Convert to CSV

Use this Python script (save as `manual_to_csv.py`):

```python
import pandas as pd
import re
from datetime import datetime

# Paste your copied text here between triple quotes
text_data = """
[PASTE ALL YOUR COPIED POSTS AND COMMENTS HERE]
"""

# Parse posts
posts = []
for block in text_data.split("--- POST ---"):
    if not block.strip():
        continue

    title = re.search(r'Title:\s*(.+)', block)
    subreddit = re.search(r'Subreddit:\s*(.+)', block)
    score = re.search(r'Score:\s*(\d+)', block)
    comments = re.search(r'Comments:\s*(\d+)', block)
    text = re.search(r'Text:\s*(.+?)(?=--- COMMENTS ---|$)', block, re.DOTALL)
    url = re.search(r'URL:\s*(.+)', block)

    if title and text:
        posts.append({
            "id": f"manual_{len(posts)}",
            "source": "reddit",
            "subreddit": subreddit.group(1).strip() if subreddit else "reddit",
            "query": "manual",
            "title": title.group(1).strip(),
            "text": text.group(1).strip(),
            "author": "manual",
            "created_utc": datetime.now().isoformat(),
            "score": int(score.group(1)) if score else 0,
            "num_comments": int(comments.group(1)) if comments else 0,
            "upvote_ratio": None,
            "url": url.group(1).strip() if url else "",
            "is_self": True,
            "flair": None,
            "type": "post"
        })

# Parse comments
for block in text_data.split("--- COMMENTS ---"):
    if not block.strip():
        continue

    comment_lines = [l for l in block.split("\n") if l.strip() and ":" in l]
    for line in comment_lines:
        parts = line.split(":", 1)
        if len(parts) == 2:
            posts.append({
                "id": f"manual_comment_{len(posts)}",
                "source": "reddit",
                "subreddit": "reddit",
                "query": "manual",
                "title": "Manual comment",
                "text": parts[1].strip(),
                "author": parts[0].strip(),
                "created_utc": datetime.now().isoformat(),
                "score": 0,
                "num_comments": 0,
                "upvote_ratio": None,
                "url": "",
                "is_self": True,
                "flair": None,
                "type": "comment"
            })

df = pd.DataFrame(posts)
df.to_csv("data/raw/reddit_posts.csv", index=False)
print(f"Saved {len(df)} manual entries to data/raw/reddit_posts.csv")
```

Run it:
```bash
python manual_to_csv.py
```

---

## Method 2: Reddit JSON API Directly in Browser

### Step 1: Visit JSON URLs

Open these URLs directly in your browser. They return raw JSON data:

```
https://www.reddit.com/r/spotify/search.json?q=discover+new+music&sort=relevance&t=year&limit=100
https://www.reddit.com/r/spotify/search.json?q=recommendation+algorithm&sort=relevance&t=year&limit=100
https://www.reddit.com/r/spotify/search.json?q=playlist+stuck+same+songs&sort=relevance&t=year&limit=100
```

### Step 2: Save JSON Files

1. The browser will show raw JSON text
2. Press Ctrl+S (or Cmd+S) to save as `.json` files
3. Save them as `reddit_1.json`, `reddit_2.json`, etc.

### Step 3: Convert to CSV

Use this Python script (save as `json_to_csv.py`):

```python
import json
import pandas as pd
import glob
from datetime import datetime

all_posts = []

for filepath in glob.glob("reddit_*.json"):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "data" in data and "children" in data["data"]:
        for child in data["data"]["children"]:
            post = child["data"]
            all_posts.append({
                "id": f"reddit_{post['id']}",
                "source": "reddit",
                "subreddit": post.get("subreddit", "spotify"),
                "query": "json_api",
                "title": post.get("title", ""),
                "text": post.get("selftext", ""),
                "author": post.get("author", "[deleted]"),
                "created_utc": datetime.fromtimestamp(post.get("created_utc", 0)).isoformat(),
                "score": post.get("score", 0),
                "num_comments": post.get("num_comments", 0),
                "upvote_ratio": post.get("upvote_ratio", None),
                "url": f"https://reddit.com{post.get('permalink', '')}",
                "is_self": post.get("is_self", False),
                "flair": post.get("link_flair_text", None),
                "type": "post"
            })

df = pd.DataFrame(all_posts)
df.to_csv("data/raw/reddit_posts.csv", index=False)
print(f"Saved {len(df)} posts from JSON files")
```

Run it:
```bash
python json_to_csv.py
```

---

## Method 3: PullPush API (No Auth, No Rate Limits)

### Step 1: Visit API URLs in Browser

```
https://api.pullpush.io/reddit/search/submission/?q=discover+new+music&subreddit=spotify&size=100&sort=desc&sort_type=score
https://api.pullpush.io/reddit/search/submission/?q=recommendation+algorithm&subreddit=spotify&size=100&sort=desc&sort_type=score
https://api.pullpush.io/reddit/search/submission/?q=playlist+stuck+same+songs&subreddit=spotify&size=100&sort=desc&sort_type=score
```

### Step 2: Save JSON and Convert

Same as Method 2 — save the JSON response and use `json_to_csv.py`.

---

## ⚡ Speed Tips

- **Focus on r/spotify and r/truespotify** — highest yield
- **Only copy posts with 20+ comments** — more value per post
- **Skip posts about Spotify Wrapped** unless they mention discovery
- **Target 200-300 total entries** — enough for meaningful analysis
- **Use browser extensions** like "Copy as Markdown" to speed up copying

---

## 🎯 Minimum Viable Dataset

If you're short on time, collect from **just these 5 searches** on r/spotify:

1. "discover new music" — 20 posts
2. "recommendation algorithm" — 20 posts
3. "playlist stuck same songs" — 20 posts
4. "bored with spotify" — 20 posts
5. "discovery weekly bad" — 20 posts

**Total: 100 posts** — enough for a solid analysis.

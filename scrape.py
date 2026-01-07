import requests
from bs4 import BeautifulSoup
import os
import json

SLACK_WORKFLOW_URL = os.environ.get("SLACK_WORKFLOW_URL")
TARGET_URL = "https://www.nikkei.com/technology/"
CACHE_FILE = "last_articles.txt"

def get_articles():
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(TARGET_URL, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    
    articles = []
    for item in soup.select("a[href*='/article/']")[:15]:
        title = item.get_text(strip=True)
        link = item.get("href", "")
        if title and len(title) > 10 and link:
            if not link.startswith("http"):
                link = "https://www.nikkei.com" + link
            articles.append({"title": title, "url": link})
    
    seen = set()
    unique = []
    for a in articles:
        if a["url"] not in seen:
            seen.add(a["url"])
            unique.append(a)
    return unique

def load_cache():
    try:
        with open(CACHE_FILE, "r") as f:
            return set(f.read().splitlines())
    except FileNotFoundError:
        return set()

def save_cache(urls):
    with open(CACHE_FILE, "w") as f:
        f.write("\n".join(urls))

def send_to_slack(articles):
    for article in articles:
        payload = {
            "title": article["title"],
            "url": article["url"]
        }
        response = requests.post(
            SLACK_WORKFLOW_URL,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )
        print(f"Sent: {article['title']} - Status: {response.status_code}")

def main():
    articles = get_articles()
    cached_urls = load_cache()
    
    new_articles = [a for a in articles if a["url"] not in cached_urls]
    
    if new_articles:
        send_to_slack(new_articles)
        print(f"Sent {len(new_articles)} new articles")
    else:
        print("No new articles")
    
    all_urls = cached_urls.union({a["url"] for a in articles})
    save_cache(all_urls)

if __name__ == "__main__":
    main()

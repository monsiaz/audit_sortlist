import requests
import csv
from datetime import datetime, timedelta, timezone
import os
from openai import OpenAI
import time

os.environ["OPENAI_API_KEY"] = ""

# ========== CONFIG ==========

SERPAPI_KEY = ""
OPENAI_MODEL = "o3-mini"

CSV_FILENAME = "news_articles_with_relevance.csv"
ARTICLE_LIMIT = 40

TOPICS = [
    "Advertising", "360º Advertising", "Advertising Campaign", "Advertising Production",
    "Creative", "Creative & Visual", "3D", "Design", "Photography", "User Experience (UX/UI)",
    "Video Editing", "Development & Product", "Ecommerce", "Mobile App", "Software Development",
    "Web Design", "Web Development", "Digital Marketing", "Branding", "Event", "Public Relations (PR)",
    "SEO", "IT Services", "Blockchain Development", "Cloud Storage", "Consulting", "Cyber Security",
    "Web3 Development", "Marketing", "Affiliate Marketing", "B2B Marketing", "Communication Strategy",
    "International Marketing"
]

def fetch_news(topic):
    params = {
        "engine": "google_news",
        "q": topic,
        "hl": "en",
        "gl": "us",
        "api_key": SERPAPI_KEY
    }
    try:
        response = requests.get("https://serpapi.com/search.json", params=params)
        if response.status_code == 200:
            return response.json().get("news_results", [])
    except Exception as e:
        print(f"Error fetching topic '{topic}': {e}")
    return []

def get_recent_articles(limit=40):
    articles = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=2)
    for topic in TOPICS:
        news = fetch_news(topic)
        for item in news:
            date_str = item.get("date")
            if not date_str:
                continue
            try:
                news_date = datetime.strptime(date_str.split(",")[0], "%m/%d/%Y").replace(tzinfo=timezone.utc)
                if news_date >= cutoff:
                    articles.append({
                        "Title": item.get("title"),
                        "Meta": item.get("snippet", ""),
                        "URL": item.get("link")
                    })
                    if len(articles) >= limit:
                        return articles
            except Exception:
                continue
    return articles

def get_relevance_openai(title, meta):
    prompt = f"""
You are an editorial assistant. Determine if the following article would be relevant to a professional marketing and digital agency blog like Sortlist.com.

### Criteria:
- Must relate to digital marketing, agencies, branding, UX/UI, video, web, or app development, etc.
- Prefer global business topics or platform trends.
- Avoid politics, medical cannabis, local/regional news, religion, or sex-related advertising.

### Examples of relevant articles:
- TikTok monetization: How does it work and make money?
- The Complete Guide to Mobile App Development: From Concept to Launch
- Event Management Case Study: How Nike Achieved Event Success
- Why Are Animated Explainer Videos So Powerful for Brands?

### Not relevant:
- This week in politics: Medical cannabis advocates still pushing for ability to advertise
- Trump's trade war is giving renewed importance to advertising Upfronts
- Sex, scent and celebrity: what perfume ads of the 2000s reveal about consumer culture today

### Article to evaluate:
Title: {title}
Meta: {meta}

Should this be featured on Sortlist's blog? Reply only with "Yes" or "No".
    """
    try:
        response = client.chat.completions.create(model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}])
        answer = response.choices[0].message.content.strip()
        return "Yes" if "yes" in answer.lower() else "No"
    except Exception as e:
        print(f"OpenAI error: {e}")
        return "Unknown"

def write_csv(data, filename=CSV_FILENAME):
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Title", "Meta", "URL", "Relevant"])
        writer.writeheader()
        for row in data:
            writer.writerow(row)

def main():
    print("🔍 Fetching recent articles...")
    articles = get_recent_articles(ARTICLE_LIMIT)

    print("🤖 Evaluating relevance via OpenAI...")
    for article in articles:
        article["Relevant"] = get_relevance_openai(article["Title"], article["Meta"])
        time.sleep(1.2)  # Eviter le throttling

    print("💾 Writing CSV...")
    write_csv(articles)
    print(f"✅ Done. File saved as: {CSV_FILENAME}")

if __name__ == "__main__":
    main()

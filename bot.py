import os
import requests
import feedparser
import html
import re

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ADMIN_ID = os.environ["ADMIN_CHAT_ID"]
GEMINI_KEY = os.environ["GEMINI_API_KEY"]

FEEDS = [
    "https://openai.com/news/rss.xml",
    "https://blog.google/technology/ai/rss/",
    "https://deepmind.google/blog/rss.xml",
    "https://techcrunch.com/category/artificial-intelligence/feed/"
]


def clean_text(value):
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    return " ".join(value.split())


def get_latest_news():
    articles = []

    for url in FEEDS:
        try:
            feed = feedparser.parse(url)

            if feed.entries:
                item = feed.entries[0]
                articles.append({
                    "title": clean_text(item.get("title", "")),
                    "link": item.get("link", ""),
                    "summary": clean_text(
                        item.get("summary", item.get("description", ""))
                    )[:1500]
                })
        except Exception as error:
            print("RSS error:", error)

    return articles


def create_arabic_post(article):
    prompt = f"""
اكتب منشور أخبار ذكاء اصطناعي باللغة العربية.
استخدم أسلوبًا واضحًا وجذابًا دون اختراع معلومات.
اذكر عنوان الخبر وملخصًا مختصرًا ورابط المصدر.
لا تضف معلومات غير موجودة في المصدر.

العنوان: {article['title']}
التفاصيل: {article['summary']}
الرابط: {article['link']}
"""

    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        "models/gemini-2.5-flash:generateContent"
    )

    response = requests.post(
        url,
        params={"key": GEMINI_KEY},
        json={
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        },
        timeout=60
    )

    response.raise_for_status()
    data = response.json()

    return data["candidates"][0]["content"]["parts"][0]["text"]


def send_preview(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    response = requests.post(
        url,
        json={
            "chat_id": ADMIN_ID,
            "text": "📰 معاينة خبر جديد:\n\n" + message
        },
        timeout=30
    )

    response.raise_for_status()


def main():
    articles = get_latest_news()

    if not articles:
        print("No news found.")
        return

    article = articles[0]
    post = create_arabic_post(article)

    # معاينة للمشرف فقط، بدون نشر في القناة
    send_preview(post)

    print("Preview sent to admin successfully.")


if __name__ == "__main__":
    main()

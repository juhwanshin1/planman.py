# 뉴스 헤드라인 및 요약 

import requests
from bs4 import BeautifulSoup

def get_korean_news_headlines(url="https://rss.etnews.com/Section901.xml"):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "xml")
        items = soup.find_all("item")

        if not items:
            return ["❌ 뉴스 기사를 찾을 수 없습니다."]

        headlines = [item.title.text.strip() for item in items[:5]]
        return headlines

    except Exception as e:
        return [f"❌ 뉴스 불러오기 실패: {str(e)}"]
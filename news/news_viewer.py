import requests
from bs4 import BeautifulSoup

# 뉴스 카테고리별 URL
CATEGORY_RSS = {
    "정치": "https://www.yna.co.kr/rss/politics.xml",
    "경제": "https://www.yna.co.kr/rss/economy.xml",
    "사회/문화": "https://rss.etnews.com/Section904.xml",
    "산업/과학": "https://rss.etnews.com/Section903.xml",
    "세계": "https://www.yna.co.kr/rss/international.xml"
}

# 뉴스 제목 출력
def get_news_items_by_category(category):
    url = CATEGORY_RSS.get(category)
    if not url:
        return [{"title": f"❌ '{category}' 카테고리에 대한 RSS가 없습니다.", "link": ""}]

    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        res.raise_for_status()
        soup = BeautifulSoup(res.content, "xml")
        items = soup.find_all("item")

        news_list = []
        for item in items[:10]:
            title = item.title.text.strip()
            link = item.link.text.strip()
            news_list.append({"title": title, "link": link})

        return news_list if news_list else [{"title": "❌ 뉴스 없음", "link": ""}]

    except Exception as e:
        return [{"title": f"❌ 뉴스 로드 실패: {str(e)}", "link": ""}]

import os
import requests
import re
from datetime import datetime, timedelta

# 1. 설정 정보
NAVER_CLIENT_ID = os.environ.get('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.environ.get('NAVER_CLIENT_SECRET')
SLACK_WEB_URL = os.environ.get('SLACK_WEB_URL')

def clean_html(text):
    if not text: return ""
    return re.sub('<.+?>', '', text).replace('&quot;', '"').replace('&amp;', '&')

def fetch_and_send_news():
    # 어제 날짜 계산
    yesterday = datetime.now() - timedelta(days=1)
    date_filter = yesterday.strftime("%d %b %Y") 
    display_date = yesterday.strftime("%Y-%m-%d")

    query = "ROAI | 로아이"
    url = f"https://openapi.naver.com/v1/search/news.json?query={query}&display=50&sort=date"
    
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"네이버 API 에러: {response.status_code}")
        return

    items = response.json().get('items', [])
    
    # 🔍 어제 날짜 기사만 필터링
    yesterday_items = [item for item in items if date_filter in item['pubDate']]

    # ❌ 제외하고 싶은 단어 리스트 (영어는 반드시 '소문자'로 적어주세요)
    exclude_keywords = ['로아이시가', 'law.ai', 'return on ai', '투자수익률 중심 ai']

    # 过滤 🔍 제외 단어 필터링 적용
    filtered_items = []
    for item in yesterday_items:
        title = clean_html(item['title'])
        description = clean_html(item['description'])
        
        # 대소문자 구분을 없애기 위해 제목과 본문을 소문자로 만듭니다.
        combined_text_lower = (title + " " + description).lower()
        
        # 제외 단어가 하나라도 들어있는지 확인
        has_exclude_keyword = any(keyword in combined_text_lower for keyword in exclude_keywords)
        
        # 제외 단어가 없을 때만 리스트에 추가
        if not has_exclude_keyword:
            filtered_items.append(item)

    # 이제 필터링된 결과(filtered_items)로 슬랙 메시지를 보냅니다.
    if not filtered_items:
        payload = {
            "text": f"📅 *{display_date}* 알림\n어제는 *'ROAI'* 관련 새로운 뉴스가 없습니다. ☕"
        }
        requests.post(SLACK_WEB_URL, json=payload)
        print(f"🔔 {display_date} 새로운 뉴스 없음 - 슬랙 알림 전송 완료")
        return

    attachments = []
    for item in filtered_items:
        attachments.append({
            "title": clean_html(item['title']),
            "title_link": item['link'],
            "text": f"{clean_html(item['description'])}\n_{item['pubDate']}_",
            "color": "#36a64f"
        })

    payload = {
        "text": f"📅 *{display_date}* 전일 뉴스 요약 (총 {len(filtered_items)}건)",
        "attachments": attachments
    }

    requests.post(SLACK_WEB_URL, json=payload)
    print(f"✅ {display_date} 뉴스 전송 완료!")

if __name__ == "__main__":
    fetch_and_send_news()

import google.generativeai as genai
import os
from datetime import datetime
import re

# ✅ API 키 설정
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("models/gemini-1.5-flash")

# ✅ AI 공부 계획 생성
def generate_exam_plan(subjects):
    prompt = """
    당신은 대학생을 위한 공부 계획 도우미입니다.
    입력된 시험 과목 정보(과목명, 시험일, 전공/교양 여부, 예상 학습량)를 기반으로,
    각 과목에 대해 남은 날짜를 고려한 날짜별 공부 계획을 짜주세요.
    시간대별이 아닌 날짜별 분배로 하며, 학습량이 많을수록 더 많은 시간을 배정하세요.
    시험일 전날은 전범위 복습을 배정하고, 학습 계획은 보기 좋게 정리해주세요.

    다음은 입력된 시험 과목 목록입니다:
    """
    for s in subjects:
        prompt += f"\n- 과목명: {s['subject']}, 시험일: {s['date']}, 구분: {s['category']}, 학습량: {s['workload']}"

    prompt += """
    
    위 정보를 기반으로 날짜별 공부 계획을 한국어로 출력해주세요. 날짜와 과목, 학습 내용을 명확히 구분해주세요.
    """

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"❌ AI 계획 생성 실패: {str(e)}"

# ✅ AI 계획 텍스트에서 일정 추출
def extract_schedule_from_plan(plan_text):
    schedule = []
    lines = plan_text.splitlines()
    current_date = None
    EXAM_YEAR = 2025

    # 필터링할 불필요한 문장 키워드
    skip_keywords = [
        "추가 조언", "화이팅", "컨디션", "휴식", "수면", "계획은 예시",
        "자신의 학습", "조정 가능합니다", "진도가 빨리", "예비 학습 시간",
        "질문하고 해결", "규칙적인 휴식", "시험 준비에 도움이"
    ]

    for line in lines:
        line = line.strip()

        # 1. YYYY-MM-DD / YYYY.MM.DD / YYYY/MM/DD
        match_full = re.search(r"(\d{4})[.\-/ ]?(\d{1,2})[.\-/ ]?(\d{1,2})", line)
        if match_full:
            y, m, d = match_full.groups()
            current_date = f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
            continue

        # 2. 한국어 날짜 형식: 6월 1일
        match_kor = re.search(r"(\d{1,2})월\s*(\d{1,2})일", line)
        if match_kor:
            m, d = match_kor.groups()
            current_date = f"{EXAM_YEAR}-{int(m):02d}-{int(d):02d}"
            continue

        # 3. 일정 내용 추출
        if current_date and line and not line.startswith("|") and not line.startswith("시험"):
            clean = line.lstrip("* •- ").strip()
            if any(kw in clean for kw in skip_keywords):
                continue
            clean = clean.rstrip(".").strip()
            if clean:
                schedule.append({"date": current_date, "title": clean})

    return schedule

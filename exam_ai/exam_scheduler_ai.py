# exam_ai/exam_scheduler_ai.py
import google.generativeai as genai
import os

# ✅ API 키는 환경변수로 설정할 것을 권장합니다 (예: .env 파일 사용)
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")  # 환경변수로부터 키 불러오기

if not GOOGLE_API_KEY:
    raise ValueError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")

genai.configure(api_key=GOOGLE_API_KEY)

# Gemini 모델 초기화 (사용 가능한 최신 모델 지정)
model = genai.GenerativeModel("models/gemini-1.5-flash")

def generate_exam_plan(subjects):
    """
    subjects: 리스트 형태 [{"subject": ..., "date": ..., "category": ..., "workload": ...}, ...]
    """
    prompt = """
    당신은 대학생을 위한 공부 계획 도우미입니다.
    입력된 시험 과목 정보(과목명, 시험일, 전공/교양 여부, 예상 학습량)를 기반으로, 각 과목에 대해 남은 날짜를 고려한 일자별 공부 계획을 짜주세요.
    시간대별로 나누기보다는 날짜별로 분배하며, 학습량이 많을수록 더 많은 시간을 배정합니다.
    시험일 전날은 전범위 복습 위주로 배정해주세요.

    다음은 입력된 시험 과목 목록입니다:
    """
    for s in subjects:
        prompt += f"\n- 과목명: {s['subject']}, 시험일: {s['date']}, 구분: {s['category']}, 학습량: {s['workload']}"

    prompt += """

    위 정보를 기반으로, 날짜별로 분배된 공부 계획을 한국어로 출력해주세요. 보기 좋게 정리해서 제시해주세요.
    """

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"\u274c AI 계획 생성 실패: {str(e)}"

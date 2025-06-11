# 📚 Plan Man

> 대학생을 위한 스마트 일정 관리 및 시험 공부 도우미

Plan Man은 일정을 체계적으로 관리하고, AI 기반의 공부 계획을 자동으로 생성해주는 데스크탑 애플리케이션입니다. Tkinter를 기반으로 제작되었으며, 학업 일정 관리에 최적화된 도구입니다.

---

## 🛠️ 주요 기능

### ✅ 1. 일정 관리 (캘린더 기반)
- 날짜별 일정 추가, 수정, 삭제
- 고정 일정 핀 기능 (`📌`)
- 반복 일정 (매주) 등록 기능
- 체크리스트 추가 및 완료 상태 저장
- 일정 자동 저장 (`schedule_data.json`)

### ⏰ 2. 일정 알림 기능 (win10toast)
- 프로그램 실행 시 **24시간 이내 일정 자동 알림**
- 일정이 **2시간 이내로 임박**했을 경우 강조 알림 출력
- Windows 트레이에 팝업 알림 표시

### 🧠 3. AI 기반 시험 공부 계획 생성
- 시험 과목명, 시험일, 전공/교양 여부, 학습량 등을 입력하면
- **Gemini AI**가 자동으로 날짜별 학습 계획을 생성
- 일정 및 복습 관련 부분만 자동 추출하여 캘린더에 반영 가능

### 📰 4. 카테고리별 뉴스 조회
- 정치 / 경제 / 사회·문화 / 산업·과학 / 세계 카테고리
- 주요 언론사 RSS 기반 뉴스 헤드라인 10건씩 표시
- 뉴스 제목 더블클릭 시 웹 브라우저로 기사 열람

### 🌤 5. 날씨 기능
-지역의의 날씨 예보를 확인하는 기능
- 날씨 API를 활용하여 원하는 주도시의 날씨 확인

---
## 실행 방법
 1. git clone https://github.com/juhwanshin1/planman.py (터미널 입력)
 2. pip install -r requirements.txt (터미널 입력)
 3. main.py 실행(RUN)

## ⚠️ API 키 설정 안내

본 애플리케이션을 실행하기 위해서는 다음 API 키들이 필요하며, 환경 변수로 설정해야 합니다.

1.  **기상청 API 키 (`KMA_API_KEY`)**:
    * [공공데이터포털](https
://www.data.go.kr/) 등에서 기상청 초단기예보 API 활용신청 후 발급받은 일반 인증키(decoding)를 사용하세요.
    * 환경 변수 설정 예시:
        * Windows: `set KMA_API_KEY=여러분의_KMA_API_키`
        * macOS/Linux: `export KMA_API_KEY="여러분의_KMA_API_키"`

2.  **Google Gemini API 키 (`GEMINI_API_KEY`)**:
    * [Google AI Studio](https://aistudio.google.com/app/apikey)에서 API 키를 발급받으세요.
    * 환경 변수 설정 예시:
        * Windows: `set GEMINI_API_KEY=여러분의_GEMINI_API_키`
        * macOS/Linux: `export GEMINI_API_KEY="여러분의_GEMINI_API_키"`

애플리케이션 실행 전에 위 환경 변수들을 설정해주세요.   

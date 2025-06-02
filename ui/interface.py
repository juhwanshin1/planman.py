import tkinter as tk
from tkinter import ttk, messagebox
from news.news_viewer import get_news_items_by_category
from plancalendar.calendar_planman import launch_calendar_viewer, add_event_to_calendar
from tkcalendar import DateEntry
from exam_ai.exam_scheduler_ai import generate_exam_plan, extract_schedule_from_plan

# weather.weather_fetcher에서 필요한 함수 및 데이터 임포트
from weather.weather_fetcher import get_kma_ultra_srt_fcst_data, CITY_COORDINATES
import os # KMA_API_KEY 환경 변수 확인 안내를 위해

# 기존 PlanMan 프로젝트의 CATEGORIES 정의 사용 (planman.py의 README.md 기준)
CATEGORIES = ["정치", "경제", "사회·문화", "산업·과학", "세계"] # README.md와 일치시킴

def raise_topmost(win):
    # 이 함수는 planman.py의 ui/interface.py 원본에 있어야 함 (존재 확인)
    win.attributes("-topmost", True)
    win.lift()
    win.after(0, lambda: win.attributes("-topmost", False))

def on_schedule_click():
    # 이 함수는 planman.py의 ui/interface.py 원본에서 가져옴
    launch_calendar_viewer()

def on_news_click():
    # 이 함수는 planman.py의 ui/interface.py 원본을 기반으로 통합
    news_window = tk.Toplevel()
    news_window.title("카테고리별 뉴스 보기")
    news_window.geometry("800x600")
    raise_topmost(news_window)

    tab_control = ttk.Notebook(news_window)

    for category in CATEGORIES:
        frame = ttk.Frame(tab_control)
        tab_control.add(frame, text=category)

        items = get_news_items_by_category(category) # news.news_viewer에 정의됨

        listbox = tk.Listbox(frame, font=("Arial", 13), height=20)
        listbox.pack(padx=10, pady=0, fill=tk.BOTH, expand=True)

        for item in items:
            listbox.insert(tk.END, item['title'])
            listbox.insert(tk.END, "") # 빈 줄 추가

        def make_open_article_function(local_items):
            def open_article(event):
                index = event.widget.curselection()
                if index:
                    actual_index = index[0] // 2
                    if actual_index < len(local_items):
                        url = local_items[actual_index]['link']
                        if url:
                            import webbrowser
                            webbrowser.open(url)
            return open_article

        listbox.bind("<Double-Button-1>", make_open_article_function(items))

    tab_control.pack(expand=True, fill="both")


def on_exam_plan_click():
    # 이 함수는 planman.py의 ui/interface.py 원본에서 가져옴 (완전한 기능)
    exam_data_list = []

    def add_subject():
        subject = subject_entry.get()
        date = date_entry.get_date().strftime('%Y-%m-%d')
        category = category_var.get()
        workload = workload_var.get()

        if not subject:
            messagebox.showwarning("입력 오류", "과목명을 입력하세요.", parent=popup) # parent 지정
            return

        exam_data_list.append({
            "subject": subject,
            "date": date,
            "category": category,
            "workload": workload
        })

        subject_entry.delete(0, tk.END)
        feedback_label.config(text=f"✅ '{subject}' 과목 추가 완료")

    def generate_plan():
        if not exam_data_list:
            messagebox.showwarning("입력 부족", "최소 한 과목 이상 입력하세요.", parent=popup) # parent 지정
            return

        # GEMINI_API_KEY는 exam_scheduler_ai.py 내부에서 확인하므로 여기서는 중복 확인 불필요
        # 단, 해당 모듈에서 키가 없을 때 ValueError가 발생하므로 try-except로 처리 필요

        try:
            plan_text = generate_exam_plan(exam_data_list)
            if "❌ AI 계획 생성 실패" in plan_text or "환경변수가 설정되지 않았습니다." in plan_text : # exam_scheduler_ai.py의 오류 반환 형식 확인
                 messagebox.showerror("오류", plan_text, parent=popup) # parent 지정 및 오류 메시지 직접 사용
                 return

        except Exception as e: # generate_exam_plan 내부에서 Exception을 반환할 수도 있음
            messagebox.showerror("오류", f"계획 생성 중 예외 발생: {str(e)}", parent=popup) # parent 지정
            return

        result_window = tk.Toplevel(popup) # 부모 창 지정
        result_window.title("공부 계획 결과")
        result_window.geometry("600x400")
        raise_topmost(result_window)

        text_area = tk.Text(result_window, wrap=tk.WORD, font=("Arial", 12))
        text_area.insert(tk.END, plan_text)
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        text_area.config(state=tk.DISABLED) # 읽기 전용으로

        def confirm_add_to_calendar(p_text): # plan_text를 인자로 받도록 수정
            # 사용자에게 한 번 더 확인
            if messagebox.askyesno("일정 반영", "AI가 생성한 공부 계획을 캘린더에 반영할까요?", parent=result_window):
                schedule_list = extract_schedule_from_plan(p_text) # 인자로 받은 plan_text 사용
                if not schedule_list:
                    messagebox.showinfo("정보", "추출된 일정이 없습니다.", parent=result_window)
                    return
                try:
                    for item in schedule_list:
                        add_event_to_calendar(item['date'], item['title'], time="18:00 ~ 20:00") # 예시 시간
                    messagebox.showinfo("완료", f"{len(schedule_list)}개의 일정이 캘린더에 추가되었습니다.", parent=result_window)
                    result_window.destroy() # 성공 시 결과창 닫기
                    popup.destroy() # 과목 입력창도 닫기
                except Exception as e:
                    messagebox.showerror("캘린더 추가 오류", f"일정 추가 중 오류 발생: {str(e)}", parent=result_window)

        # 버튼 생성 시 plan_text 전달
        ttk.Button(result_window, text="캘린더에 반영", command=lambda p=plan_text: confirm_add_to_calendar(p)).pack(pady=10)
        # 최초 생성 시 자동 반영 질문은 제거하고, 버튼으로만 반영하도록 수정 (사용자 선택 존중)

    popup = tk.Toplevel()
    popup.title("📘 시험 과목 입력")
    popup.geometry("400x420")
    raise_topmost(popup)

    tk.Label(popup, text="과목명:").pack(pady=(10,0))
    subject_entry = tk.Entry(popup, width=30)
    subject_entry.pack()

    tk.Label(popup, text="시험일:").pack(pady=(5,0))
    date_entry = DateEntry(popup, date_pattern='yyyy-mm-dd', width=28) # 너비 조정
    date_entry.pack()

    tk.Label(popup, text="전공/교양:").pack(pady=(5,0))
    category_var = tk.StringVar(value="전공")
    # ttk.Combobox의 width는 글자수가 아닌 캐릭터 너비이므로 Entry와 다름
    ttk.Combobox(popup, textvariable=category_var, values=["전공", "교양"], width=28, state="readonly").pack()
    category_var.set("전공") # 기본값 설정

    tk.Label(popup, text="학습량:").pack(pady=(5,0))
    workload_var = tk.StringVar(value="보통")
    ttk.Combobox(popup, textvariable=workload_var, values=["많음", "보통", "적음"], width=28, state="readonly").pack()
    workload_var.set("보통") # 기본값 설정

    tk.Button(popup, text="➕ 과목 추가", command=add_subject, width=15).pack(pady=(10,0))
    feedback_label = tk.Label(popup, text="", fg="green")
    feedback_label.pack(pady=(5,0))

    tk.Button(popup, text="📝 계획 생성 및 캘린더 반영", command=generate_plan, width=25).pack(pady=10) # 버튼명 변경


def on_weather_click():
    kma_api_key_env = os.getenv("KMA_API_KEY")
    if not kma_api_key_env:
        messagebox.showwarning("API 키 필요",
                               "날씨 정보를 가져오려면 KMA_API_KEY 환경 변수를 설정해야 합니다.\n"
                               "프로그램을 종료하고 환경 변수 설정 후 다시 실행해주세요.\n\n"
                               "예시 (Windows CMD):\nset KMA_API_KEY=발급받은인증키\n\n"
                               "예시 (Linux/macOS 터미널):\nexport KMA_API_KEY=\"발급받은인증키\"")
        return

    weather_window = tk.Toplevel()
    weather_window.title("날씨 정보 (기상청 초단기 예보)")
    weather_window.geometry("500x550")
    raise_topmost(weather_window)

    tk.Label(weather_window, text="도시를 선택하세요:").pack(pady=(10,0))

    city_entry_frame = tk.Frame(weather_window)
    city_entry_frame.pack(pady=5)

    available_cities = list(CITY_COORDINATES.keys())
    city_combobox = ttk.Combobox(city_entry_frame, values=available_cities, width=15, state="readonly")
    if available_cities:
        city_combobox.set(available_cities[0]) # Combobox 기본값 설정
    city_combobox.pack(side=tk.LEFT)

    result_frame = tk.Frame(weather_window, pady=10, padx=10)
    result_frame.pack(fill="both", expand=True)

    weather_display_labels = {
        "city": tk.Label(result_frame, text="", font=("Arial", 16, "bold"), wraplength=480, anchor="w", justify="left"),
        "forecast_time": tk.Label(result_frame, text="", font=("Arial", 11, "italic"), wraplength=480, anchor="w", justify="left"),
        "temperature": tk.Label(result_frame, text="", font=("Arial", 14), wraplength=480, anchor="w", justify="left"),
        "sky_condition": tk.Label(result_frame, text="", font=("Arial", 12), wraplength=480, anchor="w", justify="left"),
        "humidity": tk.Label(result_frame, text="", font=("Arial", 12), wraplength=480, anchor="w", justify="left"),
        "precipitation_form": tk.Label(result_frame, text="", font=("Arial", 12), wraplength=480, anchor="w", justify="left"),
        "precipitation_1h": tk.Label(result_frame, text="", font=("Arial", 12), wraplength=480, anchor="w", justify="left"),
        "wind_speed": tk.Label(result_frame, text="", font=("Arial", 12), wraplength=480, anchor="w", justify="left"),
        "error": tk.Label(result_frame, text="", fg="red", font=("Arial", 11), wraplength=480, anchor="w", justify="left")
    }
    # 순서대로 pack (온도 먼저 보이도록)
    weather_display_labels["city"].pack(pady=3, fill="x")
    weather_display_labels["forecast_time"].pack(pady=3, fill="x")
    weather_display_labels["temperature"].pack(pady=5, fill="x") # 온도 강조
    weather_display_labels["sky_condition"].pack(pady=3, fill="x")
    weather_display_labels["humidity"].pack(pady=3, fill="x")
    weather_display_labels["precipitation_form"].pack(pady=3, fill="x")
    weather_display_labels["precipitation_1h"].pack(pady=3, fill="x")
    weather_display_labels["wind_speed"].pack(pady=3, fill="x")
    weather_display_labels["error"].pack(pady=3, fill="x")


    def fetch_and_display_weather():
        city_name = city_combobox.get()
        if not city_name:
            messagebox.showwarning("선택 필요", "도시를 선택해주세요.", parent=weather_window)
            return

        for key in weather_display_labels:
            weather_display_labels[key].config(text="")
        weather_display_labels["error"].config(text="날씨 정보 로딩 중...")
        weather_window.update_idletasks() # 로딩 메시지 즉시 표시

        weather_data = get_kma_ultra_srt_fcst_data(city_name) # API 키 인자 없음

        if "error" in weather_data:
            weather_display_labels["error"].config(text=f"오류: {weather_data['error']}")
            # 에러 발생 시 다른 필드는 비워두기 위해 위에서 이미 초기화됨
            for key in weather_display_labels:
                if key != "error":
                    weather_display_labels[key].config(text="")
        else:
            weather_display_labels["error"].config(text="")
            weather_display_labels["city"].config(text=weather_data.get("city", city_name))
            weather_display_labels["forecast_time"].config(text=f"{weather_data.get('forecast_time', '시간정보 없음')}")
            weather_display_labels["temperature"].config(text=f"🌡️ 기온: {weather_data.get('temperature', 'N/A')}")
            weather_display_labels["sky_condition"].config(text=f" আকাশ: {weather_data.get('sky_condition', 'N/A')} / 습도: {weather_data.get('humidity', 'N/A')}") # 하늘, 습도 같이 표시
            # weather_display_labels["humidity"].config(text=f"💧 습도: {weather_data.get('humidity', 'N/A')}") # 별도 라인 대신 위로 통합
            weather_display_labels["precipitation_form"].config(text=f"🌧️ 강수 형태: {weather_data.get('precipitation_form', 'N/A')}")
            weather_display_labels["precipitation_1h"].config(text=f"💧 1시간 강수량: {weather_data.get('precipitation_1h', 'N/A')}")
            weather_display_labels["wind_speed"].config(text=f"💨 풍속: {weather_data.get('wind_speed', 'N/A')}")
            # 불필요한 라벨 숨기기 (습도)
            weather_display_labels["humidity"].pack_forget()


    fetch_button = tk.Button(weather_window, text="날씨 가져오기", command=fetch_and_display_weather, font=("Arial", 12))
    fetch_button.pack(pady=10)

    if city_combobox.get():
        fetch_and_display_weather()


def launch_main_gui():
    root = tk.Tk()
    root.title("Plan Man")
    root.geometry("800x800+200+100")
    raise_topmost(root)

    title_label_text = "📚 PLAN MAN"
    title = tk.Label(root, text=title_label_text, font=("Arial", 28, "bold")) # 원본: bold 추가
    title.pack(pady=15)

    # 버튼 스타일 (planman.py 원본의 height=4, font는 약간 크게)
    btn_style = {"width": 40, "height": 4, "font": ("Arial", 11)}

    btn1 = tk.Button(root, text="1. 일정 관리", command=on_schedule_click, **btn_style)
    btn2 = tk.Button(root, text="2. 오늘의 뉴스", command=on_news_click, **btn_style)
    btn3 = tk.Button(root, text="3. 시험 공부 계획", command=on_exam_plan_click, **btn_style)
    btn4 = tk.Button(root, text="4. 날씨 보기", command=on_weather_click, **btn_style)
    btn5 = tk.Button(root, text="종료", command=root.quit, **btn_style)

    for btn in [btn1, btn2, btn3, btn4, btn5]:
        btn.pack(pady=5)

    root.mainloop()

# if __name__ == "__main__":
# launch_main_gui()
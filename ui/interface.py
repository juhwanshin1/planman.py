# ui/interface.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from news.news_viewer import get_news_items_by_category # 이 함수는 news_viewer.py에 정의되어 있어야 함
from plancalendar.calendar_planman import launch_calendar_viewer
# from weather.weather_fetcher import get_weather_data # 기존 OpenWeatherMap 함수 주석 처리
from weather.weather_fetcher import get_kma_ultra_srt_fcst_data, CITY_COORDINATES # 기상청 함수 및 도시 좌표 임포트

# --- 기존 코드의 CATEGORIES 정의가 있다면 그대로 사용 ---
# 예시: CATEGORIES = ["정치", "경제", "IT/과학", "생활/문화", "세계"]
# 제공해주신 파일 내용에 따라 CATEGORIES와 다른 함수들이 이미 정의되어 있을 것입니다.
# 아래는 on_weather_click 함수와 launch_main_gui 함수, 그리고 KMA_API_KEY 관련 부분만 수정/추가된 내용입니다.
# 실제 적용 시에는 기존 코드와 병합해야 합니다.

# 임시 CATEGORIES 정의 (실제로는 파일에 있는 것을 사용해야 함)
if 'CATEGORIES' not in globals():
    CATEGORIES = ["정치", "경제", "IT/과학", "생활/문화", "세계"] # PlanMan 프로젝트에 맞게 수정 필요

# --- 기존 함수들 (예시로 on_schedule_click, on_news_click, on_exam_plan_click 등) ---
# 이 함수들은 PlanMan 프로젝트의 기존 내용에 따라 이미 존재해야 합니다.
# (이전에 제공해주신 코드에는 내용이 있었습니다)
def on_schedule_click():
    launch_calendar_viewer()

def on_news_click():
    news_window = tk.Toplevel()
    news_window.title("뉴스 뷰어")
    news_window.geometry("800x600")
    tab_control = ttk.Notebook(news_window)
    for category in CATEGORIES:
        frame = ttk.Frame(tab_control)
        tab_control.add(frame, text=category)
        # get_news_items_by_category 함수는 news.news_viewer 모듈에 있어야 합니다.
        # 만약 이 함수가 없다면, 해당 모듈을 확인하거나 임시로 주석 처리해야 합니다.
        try:
            items = get_news_items_by_category(category) 
        except NameError: # 함수가 없을 경우를 대비한 임시 처리
             items = [{"title": f"{category} 뉴스 로딩 실패 (get_news_items_by_category 함수 확인 필요)", "link": ""}]

        listbox = tk.Listbox(frame, font=("Arial", 13), height=20)
        listbox.pack(padx=10, pady=0, fill=tk.BOTH, expand=True)
        for item in items:
            listbox.insert(tk.END, item['title'])
            listbox.insert(tk.END, "")

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
    messagebox.showinfo("시험 계획", "시험 계획 기능은 준비 중입니다.")
# -------------------------------------------------------------------------

# 기상청 API 서비스 키 (공공데이터포털에서 발급받은 키로 대체)
# 이 변수는 프로그램 실행 중 사용자가 입력하거나, 아래처럼 직접 코드에 넣을 수 있습니다.
KMA_API_SERVICE_KEY = "sgxKOhDvJsTAW6P/fTottmmxOGylFHwB+cnPvT1IuEFFqnyB5F5GrgYLTojfKiTs5hYRc0DS92YWYV3s2iNrAw==" # <<< 여기에 사용자님의 실제 기상청 서비스 키를 넣어주세요!!!

def on_weather_click():
    global KMA_API_SERVICE_KEY

    if not KMA_API_SERVICE_KEY or KMA_API_SERVICE_KEY == "YOUR_KMA_SERVICE_KEY": # 초기값 또는 플레이스홀더인지 확인
        # 서비스 키가 설정되어 있지 않으면 사용자에게 입력받음
        api_key_input = simpledialog.askstring("기상청 서비스 키 입력",
                                               "기상청 공공데이터포털에서 발급받은 서비스 키를 입력하세요:",
                                               show='*')
        if api_key_input:
            KMA_API_SERVICE_KEY = api_key_input # 입력받은 키로 업데이트
        else:
            messagebox.showwarning("서비스 키 필요", "날씨 정보를 가져오려면 기상청 서비스 키가 필요합니다.")
            return

    weather_window = tk.Toplevel()
    weather_window.title("날씨 정보 (기상청 초단기 예보)")
    weather_window.geometry("500x550") # 창 크기 조정

    tk.Label(weather_window, text="도시 이름을 입력하세요:").pack(pady=(10,0))
    
    # 도시 이름 입력 필드 (자동완성 기능이 없으므로, 지원되는 도시 목록 안내)
    city_entry_frame = tk.Frame(weather_window)
    city_entry_frame.pack(pady=5)
    city_entry = tk.Entry(city_entry_frame, width=20)
    city_entry.pack(side=tk.LEFT, padx=(0,5))
    
    # 지원되는 도시 목록을 보여주기 위한 콤보박스 (선택용)
    available_cities = list(CITY_COORDINATES.keys())
    city_combobox = ttk.Combobox(city_entry_frame, values=available_cities, width=10, state="readonly")
    if available_cities:
        city_combobox.current(0) # 첫 번째 도시를 기본 선택
    city_combobox.pack(side=tk.LEFT)

    def set_city_from_combobox(event=None):
        selected_city = city_combobox.get()
        city_entry.delete(0, tk.END)
        city_entry.insert(0, selected_city)

    city_combobox.bind("<<ComboboxSelected>>", set_city_from_combobox)
    # 초기값 설정
    if available_cities:
        set_city_from_combobox()


    result_frame = tk.Frame(weather_window, pady=10, padx=10)
    result_frame.pack(fill="both", expand=True)

    # 결과 표시용 라벨들을 미리 만들어두고 업데이트 (더 깔끔한 UI를 위해)
    weather_display_labels = {
        "city": tk.Label(result_frame, text="", font=("Arial", 16, "bold"), wraplength=480),
        "forecast_time": tk.Label(result_frame, text="", font=("Arial", 11, "italic"), wraplength=480),
        "sky_condition": tk.Label(result_frame, text="", font=("Arial", 12), wraplength=480),
        "precipitation_form": tk.Label(result_frame, text="", font=("Arial", 12), wraplength=480),
        "temperature": tk.Label(result_frame, text="", font=("Arial", 14), wraplength=480),
        "humidity": tk.Label(result_frame, text="", font=("Arial", 12), wraplength=480),
        "precipitation_1h": tk.Label(result_frame, text="", font=("Arial", 12), wraplength=480),
        "wind_speed": tk.Label(result_frame, text="", font=("Arial", 12), wraplength=480),
        "error": tk.Label(result_frame, text="", fg="red", font=("Arial", 11), wraplength=480)
    }
    for label in weather_display_labels.values():
        label.pack(pady=3, anchor="w") # 왼쪽 정렬

    def fetch_and_display_weather():
        city_name = city_entry.get()
        if not city_name:
            messagebox.showwarning("입력 필요", "도시 이름을 입력하거나 선택해주세요.")
            return

        if city_name not in CITY_COORDINATES:
            messagebox.showwarning("지원하지 않는 도시",
                                   f"'{city_name}'은(는) 미리 정의된 도시 목록에 없습니다.\n"
                                   f"지원되는 도시: {', '.join(CITY_COORDINATES.keys())}")
            return

        # 이전 결과 초기화
        for key in weather_display_labels:
            weather_display_labels[key].config(text="")
        weather_display_labels["error"].config(text="날씨 정보 로딩 중...")


        # get_kma_ultra_srt_fcst_data 함수 호출
        weather_data = get_kma_ultra_srt_fcst_data(KMA_API_SERVICE_KEY, city_name)

        if "error" in weather_data:
            weather_display_labels["error"].config(text=f"오류: {weather_data['error']}")
        else:
            weather_display_labels["error"].config(text="") # 오류 메시지 없음
            weather_display_labels["city"].config(text=weather_data.get("city", city_name))
            weather_display_labels["forecast_time"].config(text=f"({weather_data.get('forecast_time', '시간정보 없음')})")
            
            sky_text = f"하늘 상태: {weather_data.get('sky_condition', 'N/A')}"
            weather_display_labels["sky_condition"].config(text=sky_text)
            
            pty_text = f"강수 형태: {weather_data.get('precipitation_form', 'N/A')}"
            weather_display_labels["precipitation_form"].config(text=pty_text)
            
            temp_text = f"기온: {weather_data.get('temperature', 'N/A')}"
            weather_display_labels["temperature"].config(text=temp_text)
            
            hum_text = f"습도: {weather_data.get('humidity', 'N/A')}"
            weather_display_labels["humidity"].config(text=hum_text)

            rn1_text = f"1시간 강수량: {weather_data.get('precipitation_1h', 'N/A')}"
            weather_display_labels["precipitation_1h"].config(text=rn1_text)

            wind_text = f"풍속: {weather_data.get('wind_speed', 'N/A')}"
            weather_display_labels["wind_speed"].config(text=wind_text)


    fetch_button = tk.Button(weather_window, text="날씨 가져오기", command=fetch_and_display_weather, font=("Arial", 12))
    fetch_button.pack(pady=10)
    
    # 창이 열릴 때 기본 선택된 도시의 날씨를 바로 가져오도록 설정 (선택 사항)
    # fetch_and_display_weather()


def launch_main_gui():
    root = tk.Tk()
    root.title("Plan Man")
    root.geometry("800x800+200+100") # 창 크기는 그대로 유지하거나 필요시 조정

    title = tk.Label(root, text="📅 PLAN MAN 📝", font=("Arial", 28, "bold"))
    title.pack(pady=15)

    # 버튼 스타일 통일 (기존 코드에서 가져옴)
    btn_style = {"width": 40, "height": 3, "font": ("Arial", 12)}

    btn1 = tk.Button(root, text="1. 🗓️ 스케줄 관리", command=on_schedule_click, **btn_style)
    btn2 = tk.Button(root, text="2. 📰 뉴스 보기", command=on_news_click, **btn_style)
    btn3 = tk.Button(root, text="3. ✍️ 시험 계획 (준비 중)", command=on_exam_plan_click, **btn_style)
    btn4 = tk.Button(root, text="4. ☀️ 날씨 보기 (기상청)", command=on_weather_click, **btn_style) # 버튼 텍스트 수정
    btn5 = tk.Button(root, text="🚪 종료", command=root.quit, **btn_style)

    for btn in [btn1, btn2, btn3, btn4, btn5]:
        btn.pack(pady=10)

    root.mainloop()

# main.py에서 launch_main_gui()를 호출하므로, 이 파일에서 직접 실행 부분은 주석 처리하거나 삭제합니다.
# if __name__ == "__main__":
# launch_main_gui()
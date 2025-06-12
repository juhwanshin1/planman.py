import tkinter as tk
from tkinter import ttk, messagebox
from news.news_viewer import get_news_items_by_category
from plancalendar.calendar_planman import launch_calendar_viewer, add_event_to_calendar
from tkcalendar import DateEntry
from exam_ai.exam_scheduler_ai import generate_exam_plan, extract_schedule_from_plan
from weather.weather_fetcher import get_kma_ultra_srt_fcst_data, CITY_COORDINATES
import os
from datetime import datetime, timedelta

CATEGORIES = ["정치", "경제", "사회·문화", "산업·과학", "세계"]

def raise_topmost(win):
    win.attributes("-topmost", True)
    win.lift()
    win.after(0, lambda: win.attributes("-topmost", False))

def on_schedule_click():
    launch_calendar_viewer()

def on_news_click():
    news_window = tk.Toplevel()
    news_window.title("카테고리별 뉴스 보기")
    news_window.geometry("800x600")
    raise_topmost(news_window)

    tab_control = ttk.Notebook(news_window)

    for category in CATEGORIES:
        frame = ttk.Frame(tab_control)
        tab_control.add(frame, text=category)

        items = get_news_items_by_category(category)

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
    exam_data_list = []

    def refresh_subject_list():
        for widget in subject_list_frame.winfo_children():
            widget.destroy()
        
        for i, subject_data in enumerate(exam_data_list):
            item_frame = ttk.Frame(subject_list_frame)
            item_frame.pack(fill='x', pady=2, padx=5)

            info_text = f"과목: {subject_data['subject']} ({subject_data['category']}/{subject_data['workload']}) - 시험일: {subject_data['date']}"
            ttk.Label(item_frame, text=info_text, anchor="w").pack(side=tk.LEFT, expand=True, fill='x')

            delete_btn = ttk.Button(item_frame, text="삭제", width=5, command=lambda idx=i: delete_subject(idx))
            delete_btn.pack(side=tk.RIGHT)

    def delete_subject(index_to_delete):
        del exam_data_list[index_to_delete]
        refresh_subject_list()

    def add_subject():
        subject = subject_entry.get()
        date = date_entry.get_date().strftime('%Y-%m-%d')
        category = category_var.get()
        workload = workload_var.get()

        if not subject:
            messagebox.showwarning("입력 오류", "과목명을 입력하세요.", parent=popup)
            return

        exam_data_list.append({
            "subject": subject,
            "date": date,
            "category": category,
            "workload": workload
        })

        subject_entry.delete(0, tk.END)
        refresh_subject_list()

    def generate_plan():
        if not exam_data_list:
            messagebox.showwarning("입력 부족", "최소 한 과목 이상 추가해주세요.", parent=popup)
            return
            
        start_date = start_date_entry.get_date().strftime('%Y-%m-%d')
            
        try:
            plan_text = generate_exam_plan(exam_data_list, start_date)
            if "❌ AI 계획 생성 실패" in plan_text or "환경변수가 설정되지 않았습니다." in plan_text :
                 messagebox.showerror("오류", plan_text, parent=popup)
                 return

        except Exception as e:
            messagebox.showerror("오류", f"계획 생성 중 예외 발생: {str(e)}", parent=popup)
            return

        result_window = tk.Toplevel(popup)
        result_window.title("공부 계획 결과")
        result_window.geometry("600x500")
        raise_topmost(result_window)

        button_frame = ttk.Frame(result_window)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10, padx=10)
        
        text_frame = ttk.Frame(result_window)
        text_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(10, 0), padx=10)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_area = tk.Text(text_frame, wrap=tk.WORD, font=("Arial", 12), yscrollcommand=scrollbar.set)
        text_area.insert(tk.END, plan_text)
        text_area.config(state=tk.DISABLED)
        text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.config(command=text_area.yview)

        def confirm_add_to_calendar(p_text):
            if messagebox.askyesno("일정 반영", "AI가 생성한 공부 계획을 캘린더에 반영할까요?", parent=result_window):
                schedule_list = extract_schedule_from_plan(p_text)
                if not schedule_list:
                    messagebox.showinfo("정보", "추출된 일정이 없습니다.", parent=result_window)
                    return
                try:
                    for item in schedule_list:
                        add_event_to_calendar(item['date'], item['title'], time="18:00 ~ 20:00")
                    messagebox.showinfo("완료", f"{len(schedule_list)}개의 일정이 캘린더에 추가되었습니다.", parent=result_window)
                    result_window.destroy() 
                    popup.destroy()
                except Exception as e:
                    messagebox.showerror("캘린더 추가 오류", f"일정 추가 중 오류 발생: {str(e)}", parent=result_window)

        ttk.Button(button_frame, text="캘린더에 반영", command=lambda p=plan_text: confirm_add_to_calendar(p)).pack()
    
    popup = tk.Toplevel()
    popup.title("📘 시험 과목 입력")
    popup.geometry("400x600")
    raise_topmost(popup)

    input_frame = ttk.Frame(popup, padding="10")
    input_frame.pack(fill='x')

    ttk.Label(input_frame, text="과목명:").pack()
    subject_entry = ttk.Entry(input_frame, width=30)
    subject_entry.pack(pady=(0, 5))

    ttk.Label(input_frame, text="공부 시작일:").pack()
    start_date_entry = DateEntry(input_frame, date_pattern='yyyy-mm-dd', width=28)
    start_date_entry.set_date(datetime.now().date())
    start_date_entry.pack(pady=(0, 5))
    
    ttk.Label(input_frame, text="시험일:").pack()
    date_entry = DateEntry(input_frame, date_pattern='yyyy-mm-dd', width=28)
    date_entry.set_date(datetime.now().date() + timedelta(days=1))
    date_entry.pack(pady=(0, 5))

    ttk.Label(input_frame, text="전공/교양:").pack()
    category_var = tk.StringVar(value="전공")
    category_frame = ttk.Frame(input_frame)
    ttk.Radiobutton(category_frame, text="전공", variable=category_var, value="전공").pack(side=tk.LEFT, padx=10)
    ttk.Radiobutton(category_frame, text="교양", variable=category_var, value="교양").pack(side=tk.LEFT, padx=10)
    category_frame.pack(pady=(0, 5))

    ttk.Label(input_frame, text="학습량:").pack()
    workload_var = tk.StringVar(value="보통")
    workload_frame = ttk.Frame(input_frame)
    ttk.Radiobutton(workload_frame, text="많음", variable=workload_var, value="많음").pack(side=tk.LEFT, padx=5)
    ttk.Radiobutton(workload_frame, text="보통", variable=workload_var, value="보통").pack(side=tk.LEFT, padx=5)
    ttk.Radiobutton(workload_frame, text="적음", variable=workload_var, value="적음").pack(side=tk.LEFT, padx=5)
    workload_frame.pack(pady=(0, 10))

    ttk.Button(input_frame, text="➕ 과목 추가", command=add_subject, width=15).pack()

    ttk.Separator(popup, orient='horizontal').pack(fill='x', pady=10, padx=10)
    
    list_container = ttk.Frame(popup)
    list_container.pack(fill='both', expand=True)
    ttk.Label(list_container, text="추가된 과목 목록", font=("Arial", 10, "bold")).pack()
    subject_list_frame = ttk.Frame(list_container)
    subject_list_frame.pack(fill='x')

    bottom_frame = ttk.Frame(popup, padding="10")
    bottom_frame.pack(side='bottom', fill='x')
    ttk.Button(bottom_frame, text="📝 계획 생성", command=generate_plan, width=25).pack()


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
        city_combobox.set(available_cities[0])
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
    weather_display_labels["city"].pack(pady=3, fill="x")
    weather_display_labels["forecast_time"].pack(pady=3, fill="x")
    weather_display_labels["temperature"].pack(pady=5, fill="x")
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
        weather_window.update_idletasks()

        weather_data = get_kma_ultra_srt_fcst_data(city_name) 

        if "error" in weather_data:
            weather_display_labels["error"].config(text=f"오류: {weather_data['error']}")
            for key in weather_display_labels:
                if key != "error":
                    weather_display_labels[key].config(text="")
        else:
            weather_display_labels["error"].config(text="")
            weather_display_labels["city"].config(text=weather_data.get("city", city_name))
            weather_display_labels["forecast_time"].config(text=f"{weather_data.get('forecast_time', '시간정보 없음')}")
            weather_display_labels["temperature"].config(text=f"🌡️ 기온: {weather_data.get('temperature', 'N/A')}")
            weather_display_labels["sky_condition"].config(text=f" 하늘: {weather_data.get('sky_condition', 'N/A')} / 습도: {weather_data.get('humidity', 'N/A')}")
            weather_display_labels["precipitation_form"].config(text=f"🌧️ 강수 형태: {weather_data.get('precipitation_form', 'N/A')}")
            weather_display_labels["precipitation_1h"].config(text=f"💧 1시간 강수량: {weather_data.get('precipitation_1h', 'N/A')}")
            weather_display_labels["wind_speed"].config(text=f"💨 풍속: {weather_data.get('wind_speed', 'N/A')}")
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
    title = tk.Label(root, text=title_label_text, font=("Arial", 28, "bold"))
    title.pack(pady=15)

    btn_style = {"width": 40, "height": 4, "font": ("Arial", 11)}

    btn1 = tk.Button(root, text="1. 일정 관리", command=on_schedule_click, **btn_style)
    btn2 = tk.Button(root, text="2. 오늘의 뉴스", command=on_news_click, **btn_style)
    btn3 = tk.Button(root, text="3. 시험 공부 계획", command=on_exam_plan_click, **btn_style)
    btn4 = tk.Button(root, text="4. 날씨 보기", command=on_weather_click, **btn_style)
    btn5 = tk.Button(root, text="종료", command=root.quit, **btn_style)

    for btn in [btn1, btn2, btn3, btn4, btn5]:
        btn.pack(pady=5)

    root.mainloop()
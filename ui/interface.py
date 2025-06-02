import tkinter as tk
from tkinter import ttk, messagebox
from news.news_viewer import get_news_items_by_category
from plancalendar.calendar_planman import launch_calendar_viewer, add_event_to_calendar
from tkcalendar import DateEntry
from exam_ai.exam_scheduler_ai import generate_exam_plan, extract_schedule_from_plan

CATEGORIES = ["정치", "경제", "사회/문화", "산업/과학", "세계"]

def raise_topmost(win):
    win.attributes("-topmost", True)
    win.lift()
    win.after(0, lambda: win.attributes("-topmost", False))

def on_schedule_click():
    # launch_calendar_viewer 내부에서 Toplevel 처리됨
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

    def add_subject():
        subject = subject_entry.get()
        date = date_entry.get_date().strftime('%Y-%m-%d')
        category = category_var.get()
        workload = workload_var.get()

        if not subject:
            messagebox.showwarning("입력 오류", "과목명을 입력하세요.")
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
            messagebox.showwarning("입력 부족", "최소 한 과목 이상 입력하세요.")
            return

        try:
            plan_text = generate_exam_plan(exam_data_list)
        except Exception as e:
            messagebox.showerror("오류", f"계획 생성 실패: {str(e)}")
            return

        result_window = tk.Toplevel()
        result_window.title("공부 계획 결과")
        result_window.geometry("600x400")
        raise_topmost(result_window)

        text_area = tk.Text(result_window, wrap=tk.WORD, font=("Arial", 12))
        text_area.insert(tk.END, plan_text)
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # ✅ 자동 반영 여부 묻기
        if messagebox.askyesno("일정 반영", "AI가 생성한 공부 계획을 캘린더에 반영할까요?"):
            schedule_list = extract_schedule_from_plan(plan_text)
            for item in schedule_list:
                add_event_to_calendar(item['date'], item['title'], time="18:00 ~ 20:00")
            messagebox.showinfo("완료", f"{len(schedule_list)}개의 일정이 추가되었습니다.")

        def confirm_add():
            if messagebox.askyesno("캘린더 반영", "이 계획을 다시 캘린더에 반영할까요?"):
                schedule_list = extract_schedule_from_plan(plan_text)
                for item in schedule_list:
                    add_event_to_calendar(item['date'], item['title'], time="18:00 ~ 20:00")
                messagebox.showinfo("완료", "캘린더에 반영 완료")

        ttk.Button(result_window, text="캘린더에 반영", command=confirm_add).pack(pady=10)

    popup = tk.Toplevel()
    popup.title("📘 시험 과목 입력")
    popup.geometry("400x420")
    raise_topmost(popup)

    tk.Label(popup, text="과목명:").pack()
    subject_entry = tk.Entry(popup, width=30)
    subject_entry.pack()

    tk.Label(popup, text="시험일:").pack()
    date_entry = DateEntry(popup, date_pattern='yyyy-mm-dd')
    date_entry.pack()

    tk.Label(popup, text="전공/교양:").pack()
    category_var = tk.StringVar(value="전공")
    ttk.Combobox(popup, textvariable=category_var, values=["전공", "교양"]).pack()

    tk.Label(popup, text="학습량:").pack()
    workload_var = tk.StringVar(value="보통")
    ttk.Combobox(popup, textvariable=workload_var, values=["많음", "보통", "적음"]).pack()

    tk.Button(popup, text="➕ 과목 추가", command=add_subject).pack(pady=10)
    feedback_label = tk.Label(popup, text="", fg="green")
    feedback_label.pack()

    tk.Button(popup, text="📝 계획 생성", command=generate_plan).pack(pady=10)

def on_weather_click():
    messagebox.showinfo("날씨", "🌤 날씨 기능은 추후 연결 예정입니다.")

def launch_main_gui():
    root = tk.Tk()
    root.title("Plan Man")
    root.geometry("800x800+200+100")
    raise_topmost(root)

    title = tk.Label(root, text="📚 PLAN MAN", font=("Arial", 28))
    title.pack(pady=15)

    btn1 = tk.Button(root, text="1. 일정 관리", width=40, height=4, command=on_schedule_click)
    btn2 = tk.Button(root, text="2. 오늘의 뉴스", width=40, height=4, command=on_news_click)
    btn3 = tk.Button(root, text="3. 시험 공부 계획", width=40, height=4, command=on_exam_plan_click)
    btn4 = tk.Button(root, text="4. 날씨 보기", width=40, height=4, command=on_weather_click)
    btn5 = tk.Button(root, text="종료", width=40, height=4, command=root.quit)

    for btn in [btn1, btn2, btn3, btn4, btn5]:
        btn.pack(pady=5)

    root.mainloop()

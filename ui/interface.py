import tkinter as tk
from tkinter import ttk, messagebox
from news.news_viewer import get_news_items_by_category
from plancalendar.calendar_planman import launch_calendar_viewer  # 일정 관리 UI

# 뉴스 카테고리 목록
CATEGORIES = ["정치", "경제", "사회/문화", "산업/과학", "세계"]

def on_schedule_click():
    launch_calendar_viewer()  # 일정 UI 실행

def on_news_click():
    news_window = tk.Toplevel()
    news_window.title("카테고리별 뉴스 보기")
    news_window.geometry("800x600")

    tab_control = ttk.Notebook(news_window)

    for category in CATEGORIES:
        frame = ttk.Frame(tab_control)
        tab_control.add(frame, text=category)

        items = get_news_items_by_category(category)

        listbox = tk.Listbox(frame, font=("Arial", 13), height=20)
        listbox.pack(padx=10, pady=0, fill=tk.BOTH, expand=True)

        for item in items:
            listbox.insert(tk.END, item['title'])
            listbox.insert(tk.END, "")  # 한 줄 띄우기

        def make_open_article_function(local_items):
            def open_article(event):
                index = event.widget.curselection()
                if index:
                    actual_index = index[0] // 2  # 줄 띄움으로 인한 보정
                    if actual_index < len(local_items):
                        url = local_items[actual_index]['link']
                        if url:
                            import webbrowser
                            webbrowser.open(url)
            return open_article

        listbox.bind("<Double-Button-1>", make_open_article_function(items))

    tab_control.pack(expand=True, fill="both")


def on_exam_plan_click():
    messagebox.showinfo("공부 계획", "📘 공부 계획 기능은 추후 연결 예정입니다.")

def on_weather_click():
    messagebox.showinfo("날씨", "🌤 날씨 기능은 추후 연결 예정입니다.")

def launch_main_gui():
    root = tk.Tk()
    root.title("Plan Man")
    root.geometry("800x800+200+100")

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

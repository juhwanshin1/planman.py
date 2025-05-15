# 메뉴 출력 함수
import tkinter as tk
from tkinter import ttk
import webbrowser
from news.news_viewer import get_news_items_by_category

CATEGORIES = ["정치", "경제", "사회/문화", "산업/과학", "세계"]

def launch_main_gui():
    root = tk.Tk()
    root.title("Plan Man")

    # 창 크기
    window_width = 800
    window_height = 800

    # 창 위치
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = int((screen_width - window_width) / 2)
    y = int((screen_height - window_height) / 2)
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # 제목
    title = tk.Label(root, text="📚 PLAN MAN", font=("Arial", 28))
    title.pack(pady=15)

    # 메인메뉴 버튼
    btn1 = tk.Button(root, text="1. 일정 관리", width=40, height=4, command=lambda: tk.messagebox.showinfo("일정", "일정 기능은 추후 연결 예정입니다."))
    btn2 = tk.Button(root, text="2. 오늘의 뉴스", width=40, height=4, command=on_news_click)
    btn3 = tk.Button(root, text="3. 시험 공부 계획", width=40, height=4, command=lambda: tk.messagebox.showinfo("공부 계획", "공부 계획 기능은 추후 연결 예정입니다."))
    btn4 = tk.Button(root, text="4. 날씨 보기", width=40, height=4, command=lambda: tk.messagebox.showinfo("날씨", "날씨 기능은 추후 연결 예정입니다."))
    btn5 = tk.Button(root, text="종료", width=40, height=4, command=root.quit)

    for btn in [btn1, btn2, btn3, btn4, btn5]:
        btn.pack(pady=5)

    root.mainloop()

def on_news_click():
    news_window = tk.Toplevel()
    news_window.title("📰 카테고리별 뉴스 보기  (더블클릭 시 원문으로 이동)")
    news_window.geometry("800x600")

    # 상단 카테고리 버튼 프레임 추가
    button_frame = tk.Frame(news_window)
    button_frame.pack(fill=tk.X)

    selected_category = tk.StringVar(value=CATEGORIES[0])

    content_frame = tk.Frame(news_window)
    content_frame.pack(expand=1, fill="both")

    listbox = tk.Listbox(
        content_frame, width=100, height=30,
        font=("Arial", 14), activestyle='dotbox'
    )
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = tk.Scrollbar(content_frame, command=listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    listbox.config(yscrollcommand=scrollbar.set)

    def load_news(category):
        listbox.delete(0, tk.END)
        items = get_news_items_by_category(category)
        for item in items:
            display_title = item['title']
            listbox.insert(tk.END, display_title)
            listbox.insert(tk.END, "")

        def open_article(event):
            index = listbox.curselection()
            if index:
                actual_index = index[0] // 2  # 한 줄 공백 포함 시 보정
                if actual_index < len(items):
                    url = items[actual_index]['link']
                    if url:
                        webbrowser.open(url)

        listbox.bind("<Double-Button-1>", open_article)

    for category in CATEGORIES:
        btn = tk.Button(button_frame, text=category, font=("Arial", 12), width=16, height=2,
                        command=lambda c=category: load_news(c))
        btn.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

    load_news(CATEGORIES[0])

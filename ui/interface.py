# 메뉴 출력 함수 정의

import tkinter as tk
from tkinter import messagebox
from news.news_viewer import get_korean_news_headlines

def on_schedule_click():
    messagebox.showinfo("일정", "📅 일정 기능은 추후 연결 예정입니다.")

def on_news_click():
    headlines = get_korean_news_headlines()
    news_text = "\n\n".join(headlines)
    messagebox.showinfo("📰 오늘의 뉴스 헤드라인", news_text)

def on_exam_plan_click():
    messagebox.showinfo("공부 계획", "📘 공부 계획 기능은 추후 연결 예정입니다.")

def on_weather_click():
    messagebox.showinfo("날씨", "🌤 날씨 기능은 추후 연결 예정입니다.")

def launch_main_gui():
    root = tk.Tk()
    root.title("Smart Scheduler AI")
    root.geometry("300x300")

    title = tk.Label(root, text="📚 PLAN MAN", font=("Arial", 16))
    title.pack(pady=10)

    btn1 = tk.Button(root, text="1. 일정 관리", width=25, command=on_schedule_click)
    btn2 = tk.Button(root, text="2. 오늘의 뉴스", width=25, command=on_news_click)
    btn3 = tk.Button(root, text="3. 시험 공부 계획", width=25, command=on_exam_plan_click)
    btn4 = tk.Button(root, text="4. 날씨 보기", width=25, command=on_weather_click)
    btn5 = tk.Button(root, text="종료", width=25, command=root.quit)

    for btn in [btn1, btn2, btn3, btn4, btn5]:
        btn.pack(pady=5)

    root.mainloop()

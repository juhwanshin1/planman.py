import json
import os
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from tkcalendar import Calendar

DATA_FILE = "schedule_data.json"

# Load and save data
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Launch calendar UI
def launch_calendar_viewer():
    root = tk.Toplevel()
    root.title("📅 Plan Man 일정 관리")
    root.geometry("900x700")

    data = load_data()

    def refresh_all():
        date = cal.get_date()
        events = data.get(date, {}).get("events", [])
        checklist = data.get(date, {}).get("checklist", [])

        # 일정 리스트
        event_listbox.delete(0, tk.END)
        if not events:
            event_listbox.insert(tk.END, "📖 일정이 없습니다.")
        else:
            sorted_events = sorted(events, key=lambda e: e.get("time", ""))
            for idx, e in enumerate(sorted_events):
                mark = "📌 " if e.get("pinned") else ""
                display = f"{mark}{e.get('title')} [{e.get('time', '')}]"
                event_listbox.insert(tk.END, display)

        # 체크리스트
        checklist_frame_clear()
        for idx, item in enumerate(checklist):
            var = tk.BooleanVar(value=item.get("done", False))
            cb = tk.Checkbutton(checklist_frame, text=item["task"], variable=var,
                                command=lambda i=idx, v=var: toggle_check_item(date, i, v))
            cb.pack(anchor="w")

    def add_event():
        date = cal.get_date()
        title = simpledialog.askstring("일정 추가", "일정 제목:")
        if not title: return
        time = simpledialog.askstring("시간 입력", "예: 14:00 ~ 15:00")
        color = simpledialog.askstring("색상 (선택)", "red, green, blue 등")
        is_pinned = messagebox.askyesno("중요 일정", "이 일정을 고정할까요?")
        is_repeat = messagebox.askyesno("반복 일정", "매주 반복할까요?")

        if date not in data:
            data[date] = {"events": [], "checklist": []}
        data[date]["events"].append({
            "title": title, "time": time,
            "color": color, "pinned": is_pinned
        })

        if is_repeat:
            repeat_weekly(date, title, time, color, is_pinned)

        save_data(data)
        refresh_all()

    def edit_event():
        date = cal.get_date()
        idx = event_listbox.curselection()
        if not idx: return
        idx = idx[0]
        event = data.get(date, {}).get("events", [])[idx]
        new_title = simpledialog.askstring("제목 수정", "새 제목:", initialvalue=event["title"])
        new_time = simpledialog.askstring("시간 수정", "예: 14:00 ~ 15:00", initialvalue=event["time"])
        new_color = simpledialog.askstring("색상 수정", "red, green 등", initialvalue=event.get("color", ""))
        event.update({"title": new_title, "time": new_time, "color": new_color})
        save_data(data)
        refresh_all()

    def delete_event():
        date = cal.get_date()
        idx = event_listbox.curselection()
        if not idx: return
        idx = idx[0]
        del data[date]["events"][idx]
        save_data(data)
        refresh_all()

    def repeat_weekly(date, title, time, color, pinned):
        base_date = datetime.strptime(date, "%Y-%m-%d")
        for i in range(1, 5):
            next_date = (base_date + timedelta(weeks=i)).strftime("%Y-%m-%d")
            if next_date not in data:
                data[next_date] = {"events": [], "checklist": []}
            data[next_date]["events"].append({
                "title": title, "time": time, "color": color, "pinned": pinned
            })

    def add_check_item():
        date = cal.get_date()
        task = simpledialog.askstring("체크리스트", "할 일:")
        if not task: return
        if date not in data:
            data[date] = {"events": [], "checklist": []}
        data[date]["checklist"].append({"task": task, "done": False})
        save_data(data)
        refresh_all()

    def toggle_check_item(date, index, var):
        data[date]["checklist"][index]["done"] = var.get()
        save_data(data)

    def checklist_frame_clear():
        for widget in checklist_frame.winfo_children():
            widget.destroy()

    # Widgets
    cal = Calendar(root, selectmode="day", date_pattern="yyyy-mm-dd")
    cal.pack(pady=10)

    event_listbox = tk.Listbox(root, width=80, height=10)
    event_listbox.pack(pady=5)

    btn_frame = tk.Frame(root)
    btn_frame.pack()

    ttk.Button(btn_frame, text="➕ 일정 추가", command=add_event).grid(row=0, column=0, padx=5)
    ttk.Button(btn_frame, text="✏️ 수정", command=edit_event).grid(row=0, column=1, padx=5)
    ttk.Button(btn_frame, text="❌ 삭제", command=delete_event).grid(row=0, column=2, padx=5)
    ttk.Button(btn_frame, text="📖 새로고침", command=refresh_all).grid(row=0, column=3, padx=5)

    tk.Label(root, text="✅ 체크리스트", font=("Arial", 14)).pack(pady=10)
    checklist_frame = tk.Frame(root)
    checklist_frame.pack()

    ttk.Button(root, text="➕ 체크 항목 추가", command=add_check_item).pack(pady=10)

    refresh_all()
    root.mainloop()

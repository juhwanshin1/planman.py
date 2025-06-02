import json
import os
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from tkcalendar import Calendar
import threading
import random
from win10toast import ToastNotifier

toaster = ToastNotifier()

DATA_FILE = "schedule_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_event_to_calendar(date: str, title: str, time: str = "", color: str = "blue", pinned: bool = False):
    data = load_data()
    if date not in data:
        data[date] = {"events": [], "checklist": []}
    data[date]["events"].append({
        "title": title,
        "time": time,
        "color": color,
        "pinned": pinned
    })
    save_data(data)

def check_alarms():
    def alert_thread():
        now = datetime.now()
        data = load_data()
        for date_str, content in data.items():
            for event in content.get("events") or []:
                event_time = event.get("time", "")
                if event_time:
                    try:
                        date_time_str = f"{date_str} {event_time.split('~')[0].strip()}"
                        event_dt = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M")
                        diff_sec = (event_dt - now).total_seconds()
                        if 0 <= diff_sec <= 7200:
                            toaster.show_toast("⏰ 임박한 일정!", f"{event['title']} - {date_time_str}", duration=10)
                        elif 0 <= diff_sec <= 86400:
                            toaster.show_toast("📅 다가오는 일정", f"{event['title']} - {date_time_str}", duration=10)
                    except:
                        pass
    threading.Thread(target=alert_thread, daemon=True).start()

def launch_calendar_viewer():
    root = tk.Toplevel()
    root.title("\ud83d\uddd5 Plan Man \uc77c\uc815 \uad00\ub9ac")
    root.geometry("900x700")
    root.attributes("-topmost", True)
    root.after(500, lambda: root.attributes("-topmost", False))

    data = load_data()

    def get_selected_date():
        return datetime.strptime(cal.get_date(), "%Y-%m-%d").strftime("%Y-%m-%d")

    def refresh_all():
        date = get_selected_date()
        events = data.get(date, {}).get("events") or []
        checklist = data.get(date, {}).get("checklist") or []

        event_listbox.delete(0, tk.END)
        if not events:
            event_listbox.insert(tk.END, "\ud83d\udcd6 \uc77c\uc815\uc774 \uc5c6\uc2b5\ub2c8\ub2e4.")
        else:
            sorted_events = sorted(events, key=lambda e: e.get("time", ""))
            for e in sorted_events:
                mark = "\ud83d\udccc " if e.get("pinned") else ""
                display = f"{mark}{e.get('title')} [{e.get('time', '')}]"
                event_listbox.insert(tk.END, display)

        checklist_frame_clear()
        for idx, item in enumerate(checklist):
            var = tk.BooleanVar(value=item.get("done", False))
            cb = tk.Checkbutton(checklist_frame, text=item["task"], variable=var,
                                command=lambda i=idx, v=var: toggle_check_item(date, i, v))
            cb.pack(anchor="w")

    def add_event():
        date = get_selected_date()
        title = simpledialog.askstring("\uc77c\uc815 \ucd94\uac00", "\uc77c\uc815 \uc81c\ubaa9:", parent=root)
        if not title: return
        time = simpledialog.askstring("\uc2dc\uac04 \uc785\ub825", "\uc608: 14:00 ~ 15:00", parent=root)
        color = random.choice(["red", "green", "blue", "orange", "purple", "brown"])
        is_pinned = messagebox.askyesno("\uc911\uc694 \uc77c\uc815", "\uc774 \uc77c\uc815\uc744 \uace0\uc815\ud560\uae4c\uc694?", parent=root)
        is_repeat = messagebox.askyesno("\ubc18\ubcf5 \uc77c\uc815", "\ub9e4\uc8fc \ubc18\ubcf5\ud560\uae4c\uc694?", parent=root)

        add_event_to_calendar(date, title, time, color, is_pinned)

        if is_repeat:
            repeat_weekly(date, title, time, color, is_pinned)

        refresh_all()

    def edit_event():
        date = get_selected_date()
        idx = event_listbox.curselection()
        if not idx: return
        idx = idx[0]
        event = data.get(date, {}).get("events") or []
        if idx >= len(event): return
        event = event[idx]
        new_title = simpledialog.askstring("\uc81c\ubaa9 \uc218\uc815", "\uc0c8 \uc81c\ubaa9:", initialvalue=event["title"], parent=root)
        new_time = simpledialog.askstring("\uc2dc\uac04 \uc218\uc815", "\uc608: 14:00 ~ 15:00", initialvalue=event["time"], parent=root)
        new_color = simpledialog.askstring("\uc0c9\uc0c1 \uc218\uc815", "red, green \ub4f1", initialvalue=event.get("color", ""), parent=root)
        event.update({"title": new_title, "time": new_time, "color": new_color})
        save_data(data)
        refresh_all()

    def delete_event():
        date = get_selected_date()
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
            add_event_to_calendar(next_date, title, time, color, pinned)

    def add_check_item():
        date = get_selected_date()
        task = simpledialog.askstring("\uccb4\ud06c\ub9ac\uc2a4\ud2b8", "\ud560 \uc77c:", parent=root)
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

    cal = Calendar(root, selectmode="day", date_pattern="yyyy-mm-dd")
    cal.pack(pady=10)

    event_listbox = tk.Listbox(root, width=80, height=10)
    event_listbox.pack(pady=5)

    btn_frame = tk.Frame(root)
    btn_frame.pack()

    ttk.Button(btn_frame, text="\u2795 \uc77c\uc815 \ucd94\uac00", command=add_event).grid(row=0, column=0, padx=5)
    ttk.Button(btn_frame, text="\u270f\ufe0f \uc218\uc815", command=edit_event).grid(row=0, column=1, padx=5)
    ttk.Button(btn_frame, text="\u274c \uc0ad\uc81c", command=delete_event).grid(row=0, column=2, padx=5)
    ttk.Button(btn_frame, text="\ud83d\udcd6 \uc0c8\ub85c\uace0\uce68", command=refresh_all).grid(row=0, column=3, padx=5)

    tk.Label(root, text="\u2705 \uccb4\ud06c\ub9ac\uc2a4\ud2b8", font=("Arial", 14)).pack(pady=10)
    checklist_frame = tk.Frame(root)
    checklist_frame.pack()

    ttk.Button(root, text="\u2795 \uccb4\ud06c \ud56d\u202f\ubcf4 \ucd94\uac00", command=add_check_item).pack(pady=10)

    refresh_all()
    root.mainloop()

check_alarms()
